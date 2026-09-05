import { ClipboardList } from "lucide-react";
import { PhasePlaceholder } from "@/components/PhasePlaceholder";

export function Audit() {
  return (
    <PhasePlaceholder
      icon={ClipboardList}
      title="Audit Log"
      subtitle="Immutable record of every state-changing action in RevTrace"
      phase="Phase 5"
      description="The Audit Log captures every action that modifies system state — ingestion events, opportunity promotions, recovery approvals, and outcome updates. Records are append-only and tamper-evident."
      features={[
        "Chronological feed of all audited events",
        "Actor, action, resource, and timestamp for every entry",
        "Filter by event type, actor, and date range",
        "Recovery approval and rejection history",
        "Exportable audit report for compliance review",
      ]}
    />
  );
}
