import { Route, Routes } from "react-router-dom";
import { Landing } from "@/pages/Landing";
import { DiagnosticStart } from "@/pages/DiagnosticStart";
import { Questionnaire } from "@/pages/Questionnaire";
import { Generating } from "@/pages/Generating";
import { ReportView } from "@/pages/ReportView";
import { AdminLogin } from "@/pages/AdminLogin";
import { AdminDashboard } from "@/pages/AdminDashboard";
import { NotFound } from "@/pages/NotFound";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/diagnostic/start" element={<DiagnosticStart />} />
      <Route path="/diagnostic/:sessionId/q/:questionIndex" element={<Questionnaire />} />
      <Route path="/diagnostic/:sessionId/generating" element={<Generating />} />
      <Route path="/diagnostic/report/:reportId" element={<ReportView />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin" element={<AdminDashboard />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
