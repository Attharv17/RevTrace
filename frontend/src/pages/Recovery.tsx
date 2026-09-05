import { RefreshCcw } from "lucide-react";
import { PhasePlaceholder } from "@/components/PhasePlaceholder";

export function Recovery() {
  return (
    <PhasePlaceholder
      icon={RefreshCcw}
      title="Recovery"
      subtitle="Manage and execute approved recovery actions"
      phase="Phase 5"
      description="The Recovery module orchestrates the controlled re-attempt of failed payment events. Every recovery action is audited, approval-gated, and outcome-tracked to prevent financial errors."
      features={[
        "Recovery action queue with approval workflow",
        "Immutable audit trail for every state change",
        "Retry scheduling with configurable back-off",
        "Real-time outcome tracking (recovered / failed / partial)",
        "Financial impact reconciliation per recovery batch",
      ]}
    />
  );
}
