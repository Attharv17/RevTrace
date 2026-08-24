import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import { Overview }       from "@/pages/Overview";
import { Reconciliation } from "@/pages/Reconciliation";
import { Exceptions }     from "@/pages/Exceptions";
import { Settlements }    from "@/pages/Settlements";
import { CashPosition }   from "@/pages/CashPosition";
import { AIAssistant }    from "@/pages/AIAssistant";
import { AuditTrail }     from "@/pages/AuditTrail";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/"               element={<Overview />} />
          <Route path="/reconciliation" element={<Reconciliation />} />
          <Route path="/exceptions"     element={<Exceptions />} />
          <Route path="/settlements"    element={<Settlements />} />
          <Route path="/cash-position"  element={<CashPosition />} />
          <Route path="/ai-assistant"   element={<AIAssistant />} />
          <Route path="/audit-trail"    element={<AuditTrail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
