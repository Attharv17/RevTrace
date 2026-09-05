import { CreditCard } from "lucide-react";
import { PhasePlaceholder } from "@/components/PhasePlaceholder";

export function Transactions() {
  return (
    <PhasePlaceholder
      icon={CreditCard}
      title="Transactions"
      subtitle="Immutable log of all ingested financial events"
      phase="Phase 2"
      description="The Transactions module provides an append-only view of all financial events ingested into RevTrace. Source records are stored immutably — no financial values are modified after ingestion."
      features={[
        "Paginated transaction event log",
        "Filter by status (success / failed / pending / disputed)",
        "Payment method, gateway, and amount breakdowns",
        "Linked leakage flags and recovery opportunity references",
        "Raw event JSON inspector for debugging",
      ]}
    />
  );
}
