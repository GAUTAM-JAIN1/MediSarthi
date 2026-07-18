import { BrowserRouter, Routes, Route } from "react-router-dom";
import Hero_Page from "./Pages/Hero_Page";
import FindMedicine from "./Pages/FindMedicine";
import Compare from "./Pages/Compare";
import Appointments from "./Pages/Appointments";
import HealthInfo from "./Pages/HealthInfo";
import Auth from "./Pages/Auth";
import Donor from "./Pages/donor";
import EmergencyView from "./Pages/EmergencyView";
import LabReport from "./Pages/LabReport";
import MedicineCheck from "./Pages/MedicineCheck";
import DoctorVisitView from "./Pages/DoctorVisitView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Hero_Page />} />
        <Route path="/find-medicine" element={<FindMedicine />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/appointments" element={<Appointments />} />
        <Route path="/health-info" element={<HealthInfo />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/donor" element={<Donor />} />
        <Route path="/emergency/:token" element={<EmergencyView />} />
        <Route path="/lab-report" element={<LabReport />} />
        <Route path="/medicine-check" element={<MedicineCheck />} />
        <Route path="/doctor-visit/:token" element={<DoctorVisitView />} />
      </Routes>
    </BrowserRouter>
  );
}