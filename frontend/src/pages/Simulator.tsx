import { FlaskConical } from "lucide-react";
import { PhasePlaceholder } from "@/components/PhasePlaceholder";

export function Simulator() {
  return (
    <PhasePlaceholder
      icon={FlaskConical}
      title="Simulator"
      subtitle="Safe simulation of recovery scenarios — no real funds moved"
      phase="Phase 5"
      description="The Simulator lets you model recovery strategies on historical data without touching live records. All outputs are clearly labelled as SIMULATED and are never written to the financial ledger."
      features={[
        "Scenario builder: define retry strategy, timing, and scope",
        "Run simulation against historical failed payments",
        "Projected recovery amount (labelled: SIMULATED, not actual)",
        "Side-by-side comparison of multiple strategies",
        "Export simulation report for stakeholder review",
      ]}
    />
  );
}
