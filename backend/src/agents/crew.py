from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Type, Optional, List
from crewai import LLM
from pydantic import BaseModel, Field
from agents.auth import get_user_knowledge_profile
from agents.health_records import get_emergency_profile
import os
from dotenv import load_dotenv
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from pathlib import Path
from .tools.custom_tool import MyCustomTool
from .tools.google_cal import GoogleCalendarTool

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# NOTE (Groq migration): All 7 crews below were moved off gemini/gemini-2.5-flash
# to groq/llama-3.3-70b-versatile because the Gemini free tier on this project hit
# a daily 20-requests/day wall (GenerateRequestsPerDayPerProjectPerModel-FreeTier),
# which made iterative dev/testing unworkable. GEMINI_API_KEY is left loaded above
# in case anything else in the project still needs it -- it is just no longer used
# by any LLM() call in this file. GROQ_API_KEY must exist in backend/.env for any
# of these crews to run now.


# ---- Shared helper ----------------------------------------------------------

def _build_crew_base(user_id: str, crew_name: str, inject_allergies: bool = False):
    """
    Common setup for all crews - reads user profile, writes knowledge file,
    optionally injects allergy info, returns (knowledge_source, embedder_config).
    Centralised here so each crew.crew() method stays clean.

    IMPORTANT: `crew_name` isolates each crew's ChromaDB memory storage. Without
    this, every crew for a given user shared the SAME CREWAI_STORAGE_DIR, so
    e.g. SpeechCrew's `doctor` agent (memory=True) could retrieve/reuse
    memories that were actually written by FileCrew (prescription photo scan)
    for the same user — causing symptom-only queries (like a "Diarrhea" bubble
    click) to return stale, unrelated medicine combinations from a totally
    different past interaction. Each crew now gets its own memory subfolder.
    """
    user_data, _ = get_user_knowledge_profile(user_id)

    if inject_allergies:
        try:
            emergency_profile = get_emergency_profile(user_data["ID"])
        except Exception:
            emergency_profile = None
        allergy_line = emergency_profile.get("allergies", "") if emergency_profile else ""
    else:
        allergy_line = ""

    os.environ["EMBEDDINGS_OLLAMA_MODEL_NAME"] = "mxbai-embed-large"
    project_root = Path(__file__).resolve().parents[2]
    storage_dir = project_root / f"./medical_memory/{user_data['ID']}/{crew_name}"
    os.environ["CREWAI_STORAGE_DIR"] = str(storage_dir)
    profile_file_rel = f"user_{user_data['ID']}/profile.txt"

    if inject_allergies and allergy_line:
        try:
            full_profile_path = project_root / "knowledge" / profile_file_rel
            existing = full_profile_path.read_text(encoding="utf-8") if full_profile_path.exists() else ""
            if "Known Allergies (for analysis):" not in existing:
                with open(full_profile_path, "a", encoding="utf-8") as f:
                    f.write(f"\nKnown Allergies (for analysis): {allergy_line or 'None recorded'}\n")
        except Exception:
            pass

    knowledge_source = TextFileKnowledgeSource(file_paths=[str(profile_file_rel)])
    embedder = {
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large",
            "url": "http://localhost:11434/api/embeddings"
        }
    }
    return knowledge_source, embedder


# ---- Pydantic Schemas --------------------------------------------------------

class MedicineItem(BaseModel):
    name: str = Field(..., description="Exact medicine name, as close as possible to how it's listed on an e-commerce pharmacy platform.")
    start_time: str = Field(..., description="Start time in ISO 8601 format (e.g., '2025-12-08T10:00:00').")
    end_time: str = Field(..., description="End time in ISO 8601 format (e.g., '2025-12-08T10:15:00').")
    description: str = Field("", description="Dosage instructions or notes (e.g., 'Take after food, twice daily').")


class PrescriptionOutput(BaseModel):
    """
    Doctor/Extractor output - may contain multiple medicines.
    care_coordinator loops over this list to create one calendar event per medicine.
    """
    user_id: str = Field(..., description="Unique ID for the user.")
    medicines: List[MedicineItem] = Field(..., description="List of ALL medicines in this prescription.")


class MedicineAnalysis(BaseModel):
    name: str = Field(..., description="Medicine name.")
    purpose: str = Field(..., description="What this medicine is for, in plain language.")
    how_to_take: str = Field(..., description="When, how, with/without food, etc.")
    common_side_effects: str = Field(..., description="Common side effects in simple language.")
    precautions: str = Field("", description="Anything specific to watch out for.")
    allergy_warning: Optional[str] = Field(None, description="If this medicine conflicts with a known allergy, explain here. Otherwise null.")


class PrescriptionAnalysisOutput(BaseModel):
    """Prescription Analyser output - plain-language breakdown + allergy cross-check."""
    overall_summary: str = Field(..., description="3-4 line plain-language summary of the prescription.")
    medicines: List[MedicineAnalysis] = Field(..., description="Per-medicine breakdown.")
    has_allergy_conflict: bool = Field(..., description="True if ANY medicine conflicts with a known allergy.")
    safety_note: str = Field(..., description="Short closing safety reminder.")


# ---- Lab Report Analyser schemas --------------------------------------------

class LabTestResult(BaseModel):
    test_name: str = Field(..., description="Name of the lab test (e.g., Haemoglobin, Fasting Blood Sugar).")
    value: str = Field(..., description="The reported value with unit (e.g., '11.2 g/dL', '98 mg/dL').")
    normal_range: str = Field("", description="The reference/normal range shown on the report, if present.")
    status: str = Field(..., description="One of: 'Normal', 'Low', 'High', 'Critical Low', 'Critical High', 'Unknown'.")
    plain_explanation: str = Field(..., description="What this test measures and what the result means, in plain everyday language a non-medical person can understand.")
    action_needed: str = Field("", description="What the patient should do about this result - e.g. 'No action needed', 'Mention to doctor at next visit', 'Consult doctor soon', 'Seek care today'.")


class LabReportAnalysisOutput(BaseModel):
    """Full analysis of a lab report - plain-language per-test breakdown."""
    report_type: str = Field(..., description="Type of report detected (e.g., 'Complete Blood Count', 'Lipid Profile', 'Thyroid Function Test', 'General Blood Work').")
    overall_summary: str = Field(..., description="3-5 line plain-language overview - what this report is checking and the general picture.")
    tests: List[LabTestResult] = Field(..., description="Per-test breakdown.")
    urgent_flags: List[str] = Field(default_factory=list, description="List of test names that are Critical Low or Critical High - empty list if none.")
    has_urgent_values: bool = Field(..., description="True if any test result is Critical Low or Critical High.")
    next_steps: str = Field(..., description="Overall recommendation - what the patient should do next based on all results combined.")
    disclaimer: str = Field(..., description="Short reminder that this is an AI explanation, not a medical diagnosis, and the patient should discuss results with their doctor.")


# ---- Medicine Interaction Checker schemas -----------------------------------

class InteractionDetail(BaseModel):
    medicine_a: str = Field(..., description="First medicine in the interaction pair.")
    medicine_b: str = Field(..., description="Second medicine in the interaction pair.")
    severity: str = Field(..., description="One of: 'None', 'Minor', 'Moderate', 'Major', 'Contraindicated'.")
    description: str = Field(..., description="Plain-language explanation of what the interaction is and why it matters.")
    recommendation: str = Field(..., description="What the patient should do - e.g. 'Safe to take together', 'Take at least 2 hours apart', 'Do not take together - consult your doctor'.")


class MedicineInteractionOutput(BaseModel):
    """Full interaction check for a list of medicines."""
    medicines_checked: List[str] = Field(..., description="The list of medicine names that were checked.")
    interactions: List[InteractionDetail] = Field(..., description="All interaction pairs found. Empty list if no interactions.")
    has_major_interaction: bool = Field(..., description="True if any interaction is Major or Contraindicated.")
    overall_safety_summary: str = Field(..., description="2-3 line plain-language overall safety picture for this combination.")
    recommendation: str = Field(..., description="What the patient should do - consult a doctor, pharmacist, or is it generally safe?")
    disclaimer: str = Field(..., description="Reminder that this is AI-generated information and not a substitute for a pharmacist's or doctor's advice.")


# ---- Symptom Triage schemas --------------------------------------------------

class SymptomFlag(BaseModel):
    symptom: str = Field(..., description="The specific symptom or detail that influenced the triage decision.")
    reason: str = Field(..., description="Why this symptom raised or lowered the urgency level.")


class SymptomTriageOutput(BaseModel):
    """Triage assessment of reported symptoms."""
    urgency_level: str = Field(..., description="One of: 'Home Care', 'See a Doctor Soon', 'Visit Emergency / Go Now'.")
    urgency_color: str = Field(..., description="One of: 'green', 'yellow', 'red' - matching urgency_level.")
    headline: str = Field(..., description="Short (1 sentence) plain-language headline summarising the triage decision.")
    explanation: str = Field(..., description="3-5 sentence explanation of why this urgency level was assigned, in plain language.")
    flags: List[SymptomFlag] = Field(default_factory=list, description="Key symptoms that influenced the decision, with reasoning.")
    home_care_tips: List[str] = Field(default_factory=list, description="If urgency is Home Care or See Doctor Soon, practical home care tips. Empty for emergency level.")
    warning_signs: List[str] = Field(..., description="Symptoms to watch for that would require upgrading urgency - always populated.")
    disclaimer: str = Field(..., description="Reminder this is AI triage and not a medical diagnosis.")


# ---- Speech-based consultation crew -----------------------------------------

@CrewBase
class SpeechCrew:
    """Medical consultation crew - voice/text symptoms"""

    agents_config = 'config/speech_agent.yaml'
    tasks_config = 'config/speech_task.yaml'

    @agent
    def doctor(self) -> Agent:
        return Agent(
            config=self.agents_config["doctor"],
            verbose=True,
            max_iter=1,
            memory=True,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
        )

    @agent
    def care_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["care_coordinator"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
            tools=[GoogleCalendarTool()]
        )

    @agent
    def prescription_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["prescription_analyst"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
        )

    @task
    def medical_consultation(self) -> Task:
        return Task(
            config=self.tasks_config["medical_consultation"],
            agent=self.doctor(),
            output_pydantic=PrescriptionOutput,
        )

    @task
    def care_task(self) -> Task:
        return Task(
            config=self.tasks_config["care_task"],
            agent=self.care_coordinator(),
            context=[self.medical_consultation()],
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],
            agent=self.prescription_analyst(),
            context=[self.medical_consultation()],
            output_pydantic=PrescriptionAnalysisOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "speech", inject_allergies=True)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- File/photo-based consultation crew -------------------------------------

@CrewBase
class FileCrew:
    """Prescription photo OCR consultation crew"""

    agents_config = 'config/file_agent.yaml'
    tasks_config = 'config/file_task.yaml'

    @agent
    def Medical_Data_Extractor(self) -> Agent:
        return Agent(
            config=self.agents_config["Medical_Data_Extractor"],
            verbose=True,
            max_rpm=3,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @agent
    def care_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["care_coordinator"],
            verbose=True,
            max_iter=1,
            memory=False,
            max_rpm=3,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
            tools=[GoogleCalendarTool()]
        )

    @agent
    def prescription_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["prescription_analyst"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
        )

    @task
    def medical_data(self) -> Task:
        return Task(
            config=self.tasks_config["medical_data"],
            agent=self.Medical_Data_Extractor(),
            output_pydantic=PrescriptionOutput,
        )

    @task
    def care_task(self) -> Task:
        return Task(
            config=self.tasks_config["care_task"],
            agent=self.care_coordinator(),
            context=[self.medical_data()],
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],
            agent=self.prescription_analyst(),
            context=[self.medical_data()],
            output_pydantic=PrescriptionAnalysisOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "file", inject_allergies=True)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            max_rpm=3,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
        )


# ---- Nearby hospitals crew ---------------------------------------------------

@CrewBase
class Nearbyhospitals():
    """Nearbyhospitals crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/hospital_agent.yaml'
    tasks_config = 'config/hospital_task.yaml'

    @agent
    def hospital_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['hospital_finder'],
            tools=[MyCustomTool()],
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
            verbose=True
        )

    @agent
    def hospital_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['hospital_reporter'],
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def reporting_task(self) -> Task:
        return Task(config=self.tasks_config['reporting_task'], output_file='report.md')

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "hospitals")
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- General health query crew -----------------------------------------------

@CrewBase
class general_que():
    """General health query crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/general_que_agent.yaml'
    tasks_config = 'config/general_que_task.yaml'

    @agent
    def home_health_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['home_health_assistant'],
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.2, api_key=GROQ_API_KEY),
            verbose=True
        )

    @task
    def general_health_assistance_task(self) -> Task:
        return Task(config=self.tasks_config['general_health_assistance_task'])

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "general")
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- Lab Report Analyser crew -------------------------------------------------

@CrewBase
class LabReportCrew:
    """
    Analyses a lab report (OCR text from photo or PDF extraction) and produces
    a plain-language breakdown of every test result, flags critical values, and
    gives clear next-step recommendations.
    """

    agents_config = 'config/lab_report_agent.yaml'
    tasks_config = 'config/lab_report_task.yaml'

    @agent
    def lab_report_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["lab_report_analyst"],
            verbose=True,
            max_iter=2,
            memory=False,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @task
    def lab_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["lab_analysis_task"],
            agent=self.lab_report_analyst(),
            output_pydantic=LabReportAnalysisOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "lab_report", inject_allergies=False)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- Medicine Interaction Checker crew -----------------------------------------

@CrewBase
class MedicineInteractionCrew:
    """
    Checks a list of medicines for known interactions - severity, plain-language
    explanation, and clear recommendation. Standalone crew, no calendar/OCR needed.
    """

    agents_config = 'config/medicine_interaction_agent.yaml'
    tasks_config = 'config/medicine_interaction_task.yaml'

    @agent
    def interaction_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["interaction_checker"],
            verbose=True,
            max_iter=2,
            memory=False,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @task
    def interaction_check_task(self) -> Task:
        return Task(
            config=self.tasks_config["interaction_check_task"],
            agent=self.interaction_checker(),
            output_pydantic=MedicineInteractionOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "med_interaction", inject_allergies=True)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- Symptom Triage crew --------------------------------------------------------

@CrewBase
class SymptomTriageCrew:
    """
    Takes a symptom description and produces a triage assessment:
    Home Care / See Doctor Soon / Emergency. Fast, single-agent crew.
    """

    agents_config = 'config/symptom_triage_agent.yaml'
    tasks_config = 'config/symptom_triage_task.yaml'

    @agent
    def triage_nurse(self) -> Agent:
        return Agent(
            config=self.agents_config["triage_nurse"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/llama-3.3-70b-versatile", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @task
    def triage_task(self) -> Task:
        return Task(
            config=self.tasks_config["triage_task"],
            agent=self.triage_nurse(),
            output_pydantic=SymptomTriageOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_source, embedder = _build_crew_base(user_id, "symptom_triage", inject_allergies=False)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=[knowledge_source],
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )