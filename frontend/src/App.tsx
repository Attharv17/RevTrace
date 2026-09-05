import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MainLayout }    from "@/components/layout/MainLayout";
import { Overview }      from "@/pages/Overview";
import { Recovery }      from "@/pages/Recovery";
import { Opportunities } from "@/pages/Opportunities";
import { Transactions }  from "@/pages/Transactions";
import { Analytics }     from "@/pages/Analytics";
import { Assistant }     from "@/pages/Assistant";
import { Simulator }     from "@/pages/Simulator";
import { Audit }         from "@/pages/Audit";
import { Evaluation }    from "@/pages/Evaluation";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          {/* Root redirect */}
          <Route path="/"              element={<Navigate to="/overview" replace />} />

          {/* RevTrace routes */}
          <Route path="/overview"      element={<Overview />} />
          <Route path="/recovery"      element={<Recovery />} />
          <Route path="/opportunities" element={<Opportunities />} />
          <Route path="/transactions"  element={<Transactions />} />
          <Route path="/analytics"     element={<Analytics />} />
          <Route path="/assistant"     element={<Assistant />} />
          <Route path="/simulator"     element={<Simulator />} />
          <Route path="/audit"         element={<Audit />} />
          <Route path="/evaluation"    element={<Evaluation />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
