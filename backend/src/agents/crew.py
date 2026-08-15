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
# to groq/openai/gpt-oss-120b because the Gemini free tier on this project hit
# a daily 20-requests/day wall (GenerateRequestsPerDayPerProjectPerModel-FreeTier),
# which made iterative dev/testing unworkable. GEMINI_API_KEY is left loaded above
# in case anything else in the project still needs it -- it is just no longer used
# by any LLM() call in this file. GROQ_API_KEY must exist in backend/.env for any
# of these crews to run now.


# ---- Shared helper ----------------------------------------------------------

def _build_crew_base(user_id: str, crew_name: str, inject_allergies: bool = False, shared_kb_files: Optional[List[str]] = None):
    """
    Common setup for all crews - reads user profile, writes knowledge file,
    optionally injects allergy info, returns (knowledge_sources, embedder_config).
    Centralised here so each crew.crew() method stays clean.

    IMPORTANT: `crew_name` isolates each crew's ChromaDB memory storage. Without
    this, every crew for a given user shared the SAME CREWAI_STORAGE_DIR, so
    e.g. SpeechCrew's `doctor` agent (memory=True) could retrieve/reuse
    memories that were actually written by FileCrew (prescription photo scan)
    for the same user â€” causing symptom-only queries (like a "Diarrhea" bubble
    click) to return stale, unrelated medicine combinations from a totally
    different past interaction. Each crew now gets its own memory subfolder.

    `shared_kb_files` (new): optional list of file paths (relative to the
    project's `knowledge/` folder, same convention as the per-user profile
    file) pointing at a SHARED, non-user-specific reference knowledge base â€”
    e.g. `["medical_kb/drug_interactions.txt"]`. When provided, a second
    TextFileKnowledgeSource is added alongside the per-user profile source,
    so the crew's agent can retrieve from both the user's own profile AND a
    curated reference set via the same embedding pipeline. See decisions.md
    D26 for why this exists and why it's scoped to only the crews that
    benefit from a real external reference (LabReportCrew,
    MedicineInteractionCrew, SymptomTriageCrew, MedicineEffectivenessCrew,
    ClinicalSummaryCrew).
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

    knowledge_sources = [TextFileKnowledgeSource(file_paths=[str(profile_file_rel)])]

    if shared_kb_files:
        # Separate TextFileKnowledgeSource instance (not merged into the same
        # file_paths list) so the per-user profile source and the shared
        # reference source are chunked/embedded independently â€” a large,
        # mostly-static reference file shouldn't affect chunking behavior for
        # the small, frequently-changing per-user profile file.
        knowledge_sources.append(TextFileKnowledgeSource(file_paths=shared_kb_files))

    # FIX (Docker adaptability): this used to be hardcoded to
    # "http://localhost:11434/api/embeddings", which works on bare-metal
    # (Ollama running on the same machine) but breaks inside Docker â€”
    # "localhost" inside a container refers to the CONTAINER itself, not
    # the host machine actually running Ollama. That's why RAG-backed
    # crews (which is now ALL crews, since embedder is always set below
    # regardless of shared_kb_files) were failing/hanging as soon as this
    # project moved into Docker.
    #
    # Fix: read the URL from an env var, defaulting to the old bare-metal
    # value so nothing changes for non-Docker runs. Set
    # OLLAMA_EMBED_URL=http://host.docker.internal:11434/api/embeddings in
    # backend/.env when running via docker-compose (see updated
    # docker-compose.yml, which also adds the extra_hosts mapping needed
    # for host.docker.internal to resolve on Linux Docker hosts â€” it works
    # out of the box on Docker Desktop for Windows/Mac).
    ollama_url = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")

    embedder = {
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large",
            "url": ollama_url
        }
    }
    return knowledge_sources, embedder


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
    numeric_value: Optional[float] = Field(None, description="The numeric portion of `value` only, unit stripped, for charting (e.g. 11.2 for '11.2 g/dL'). Null if the value isn't a plain number (e.g. 'Positive', 'Trace', 'Nil').")
    normal_range: str = Field("", description="The reference/normal range shown on the report, if present.")
    status: str = Field(..., description="One of: 'Normal', 'Low', 'High', 'Critical Low', 'Critical High', 'Unknown'.")
    plain_explanation: str = Field(..., description="What this test measures and what the result means, in plain everyday language a non-medical person can understand.")
    action_needed: str = Field("", description="What the patient should do about this result - e.g. 'No action needed', 'Mention to doctor at next visit', 'Consult doctor soon', 'Seek care today'.")


class LabReportAnalysisOutput(BaseModel):
    """Full analysis of a lab report - plain-language per-test breakdown."""
    report_type: str = Field(..., description="Type of report detected (e.g., 'Complete Blood Count', 'Lipid Profile', 'Thyroid Function Test', 'General Blood Work').")
    report_date: Optional[str] = Field(None, description="The date this report was generated/collected/printed, if mentioned anywhere in the text. Output strictly as ISO 8601 'YYYY-MM-DD'. Null if no date is found anywhere in the document.")
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


# ---- Medicine Effectiveness schemas (phase 2, decisions.md D29) -------------

class MedicineEffectivenessOutput(BaseModel):
    """
    Direction + pace verdict for one medicine's effect on one of the user's
    own tracked lab tests, given that test's dated value series since (and,
    where available, before) the medicine's start date. Grounded via RAG
    against two shared reference files: test_direction_reference.txt
    (which direction counts as "improving" for this test â€” already used by
    phase 1) and medicine_response_timelines.txt (the new phase-2 file,
    expected response windows per medicine/test pair). See decisions.md D29
    "Phase 2" for the full feature plan and why this is deliberately
    sequenced after phase 1.
    """
    direction_correct: bool = Field(..., description="True if the value is moving in the medically expected direction for this medicine+test pair.")
    pace_verdict: str = Field(..., description="One of: 'On track', 'Too early to tell', 'Slower than typical, still within expected window', 'Not responding as expected'.")
    plain_explanation: str = Field(..., description="2-4 sentence plain-language explanation of the verdict - states the WHY (e.g. the typical response window being used for this medicine+test pair), not just the verdict. Written for a non-medical reader.")
    doctor_talk_recommended: bool = Field(..., description="True if the patient should proactively mention this to their doctor at the next visit - e.g. direction is wrong, or pace is well outside the expected window.")
    disclaimer: str = Field(..., description="Short reminder this is AI-generated guidance based on the patient's own saved data, not a diagnosis, and doesn't replace a doctor's assessment.")


# ---- Clinical Summary schema (Doctor Visit QR, decisions.md D29) ------------

class ClinicalSummaryOutput(BaseModel):
    """
    Doctor Visit QR feature (decisions.md D29 sketch). Deliberately a
    DIFFERENT register from LabReportAnalysisOutput.overall_summary â€” that
    one is plain-language for the patient; this one is terse clinical
    shorthand for a doctor who already has the vocabulary and wants
    density, not hand-holding. Example target style: "Hb 9.6 (down trend,
    2mo), FBS 118 (improving on Metformin), TSH 4.8 (down, likely
    responding to treatment)." No em-dashes or narrative framing â€” reads
    like a chart note, not an explanation.
    """
    clinical_summary: str = Field(..., description="Terse, clinical-register summary of the patient's current lab picture and trends, written the way a doctor would jot a quick chart note â€” dense, abbreviation-friendly, no patient-facing plain-language explanation.")
    key_flags: List[str] = Field(default_factory=list, description="Short list of the most clinically notable items to check first this visit â€” abnormal/critical current values, or trends moving the wrong direction for their expected medicine response. Empty list if nothing stands out.")
    active_medicines_note: str = Field("", description="One-line note on currently active medicines per saved prescriptions (e.g. 'On Metformin 500mg since 12-Sep-2024, Atorvastatin 10mg since 01-Oct-2024'). Empty string if no prescriptions on record.")
    disclaimer: str = Field(..., description="Short reminder that this summary is generated from the patient's own self-reported/saved app data, not a chart pulled from a clinical record system, and doesn't replace the doctor's own examination and judgment.")


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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
        )

    @agent
    def care_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["care_coordinator"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
            tools=[GoogleCalendarTool()]
        )

    @agent
    def prescription_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["prescription_analyst"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
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
        knowledge_sources, embedder = _build_crew_base(user_id, "speech", inject_allergies=True)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @agent
    def care_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["care_coordinator"],
            verbose=True,
            max_iter=1,
            memory=False,
            max_rpm=3,
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
            tools=[GoogleCalendarTool()]
        )

    @agent
    def prescription_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["prescription_analyst"],
            verbose=True,
            max_iter=1,
            memory=False,
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
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
        knowledge_sources, embedder = _build_crew_base(user_id, "file", inject_allergies=True)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            max_rpm=3,
            knowledge_sources=knowledge_sources,
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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
            verbose=True
        )

    @agent
    def hospital_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['hospital_reporter'],
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
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
        knowledge_sources, embedder = _build_crew_base(user_id, "hospitals")
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.2, api_key=GROQ_API_KEY),
            verbose=True
        )

    @task
    def general_health_assistance_task(self) -> Task:
        return Task(config=self.tasks_config['general_health_assistance_task'])

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_sources, embedder = _build_crew_base(user_id, "general")
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.1, api_key=GROQ_API_KEY),
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
        # RAG: grounds the agent's plain-language explanations against a shared
        # standard reference-ranges file, alongside the per-user profile. See
        # decisions.md D26.
        knowledge_sources, embedder = _build_crew_base(
            user_id, "lab_report", inject_allergies=False,
            shared_kb_files=["medical_kb/lab_reference_ranges.txt"],
        )
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.1, api_key=GROQ_API_KEY),
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
        # RAG: grounds the agent's interaction calls against a shared,
        # curated drug-interaction reference file, alongside the per-user
        # profile (kept for allergy injection). See decisions.md D26.
        knowledge_sources, embedder = _build_crew_base(
            user_id, "med_interaction", inject_allergies=True,
            shared_kb_files=["medical_kb/drug_interactions.txt"],
        )
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
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
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.1, api_key=GROQ_API_KEY),
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
        # RAG: grounds the agent's urgency reasoning against a shared
        # symptom-urgency reference file, alongside the per-user profile.
        # Deliberately does NOT duplicate safety_guardrails.py's hardcoded
        # keyword list â€” that layer already short-circuits the clearest
        # emergencies before this crew is even invoked. See decisions.md D26.
        knowledge_sources, embedder = _build_crew_base(
            user_id, "symptom_triage", inject_allergies=False,
            shared_kb_files=["medical_kb/symptom_red_flags.txt"],
        )
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- Medicine Effectiveness crew (phase 2, decisions.md D29) -----------------

@CrewBase
class MedicineEffectivenessCrew:
    """
    Medicine Effectiveness feature, phase 2 (decisions.md D29). Given one
    medicine's effect on one of a user's own tracked lab tests â€” the test's
    dated value series, its normal range, and the medicine's start date â€”
    reasons about BOTH direction (is the value moving the right way) and
    pace (is it moving at the expected speed for this medicine) together,
    grounded against two shared reference files via RAG: test_direction_
    reference.txt (which direction is "improving" per test â€” already used
    by phase 1's backend logic) and medicine_response_timelines.txt (new
    this session â€” expected response windows per medicine/test pair).
    Produces a plain-language verdict + doctor-talk recommendation a
    non-medical user can trust.

    NOTE ON test_direction_reference.txt'S PATH: this crew assumes it lives
    at knowledge/medical_kb/test_direction_reference.txt, matching where the
    other three shared reference files (lab_reference_ranges.txt,
    drug_interactions.txt, symptom_red_flags.txt) already live. This wasn't
    independently re-confirmed against the actual phase-1 file layout in
    this session â€” if phase 1 put it somewhere else, update the
    shared_kb_files path below to match before running this crew for real.

    Deliberately built as phase 2, after phase 1 (annotation marker + delta
    badge, already live-tested) â€” see decisions.md D29 "Why phased instead
    of building the full pace-aware version directly."
    """

    agents_config = 'config/medicine_effectiveness_agent.yaml'
    tasks_config = 'config/medicine_effectiveness_task.yaml'

    @agent
    def effectiveness_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["effectiveness_analyst"],
            verbose=True,
            max_iter=2,
            memory=False,
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @task
    def effectiveness_task(self) -> Task:
        return Task(
            config=self.tasks_config["effectiveness_task"],
            agent=self.effectiveness_analyst(),
            output_pydantic=MedicineEffectivenessOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        # RAG: grounds direction + pace reasoning against two shared
        # reference files, alongside the per-user profile. See decisions.md
        # D26 (RAG pattern) and D29 (this feature's own reference files).
        knowledge_sources, embedder = _build_crew_base(
            user_id, "medicine_effectiveness", inject_allergies=False,
            shared_kb_files=[
                "medical_kb/test_direction_reference.txt",
                "medical_kb/medicine_response_timelines.txt",
            ],
        )
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )


# ---- Clinical Summary crew (Doctor Visit QR, decisions.md D29) --------------

@CrewBase
class ClinicalSummaryCrew:
    """
    Doctor Visit QR feature (decisions.md D29 sketch, PROJECT_CONTEXT.md
    Â§10 "Doctor Visit QR"). Takes a user's saved lab report history, their
    per-test trends, and their saved prescriptions, and produces a single
    terse, clinical-register summary for a doctor to glance at during an
    in-person visit â€” the whole reason this is a separate crew from
    LabReportCrew rather than reusing its output: LabReportAnalysisOutput's
    overall_summary is deliberately plain-language for the patient, and
    mixing registers (or trying to make one field serve both readers) was
    explicitly rejected â€” see ClinicalSummaryOutput's docstring.

    Called from main.py's POST /health/doctor-qr/{user_id} at QR-generation
    time only (not on every scan) â€” the result is cached into the token's
    snapshot by health_records.create_doctor_qr_token(). See that file's
    "DESIGN NOTE â€” snapshot, not live lookup" comment for why.
    """

    agents_config = 'config/clinical_summary_agent.yaml'
    tasks_config = 'config/clinical_summary_task.yaml'

    @agent
    def clinical_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config["clinical_summarizer"],
            verbose=True,
            max_iter=2,
            memory=False,
            llm=LLM(model="groq/openai/gpt-oss-120b", temperature=0.1, api_key=GROQ_API_KEY),
        )

    @task
    def clinical_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["clinical_summary_task"],
            agent=self.clinical_summarizer(),
            output_pydantic=ClinicalSummaryOutput,
        )

    @crew
    def crew(self, user_id: str) -> Crew:
        # RAG: grounds abnormal-value flagging and trend-direction framing
        # against the same two reference files phase-1/phase-2 Medicine
        # Effectiveness already uses, so "which direction is improving" and
        # "what counts as abnormal" stay consistent across features rather
        # than being re-derived per crew. See decisions.md D26/D29.
        knowledge_sources, embedder = _build_crew_base(
            user_id, "clinical_summary", inject_allergies=True,
            shared_kb_files=[
                "medical_kb/lab_reference_ranges.txt",
                "medical_kb/test_direction_reference.txt",
            ],
        )
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=False,
            knowledge_sources=knowledge_sources,
            embedder=embedder,
            process=Process.sequential,
            max_rpm=3
        )