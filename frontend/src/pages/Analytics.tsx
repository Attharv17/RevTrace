import { BarChart2 } from "lucide-react";
import { PhasePlaceholder } from "@/components/PhasePlaceholder";

export function Analytics() {
  return (
    <PhasePlaceholder
      icon={BarChart2}
      title="Analytics"
      subtitle="Revenue recovery performance and leakage trend analysis"
      phase="Phase 6"
      description="The Analytics module aggregates recovery outcomes across all processed events. Charts and KPIs are derived exclusively from actual recovery records — no simulated or estimated figures are displayed."
      features={[
        "Recovery rate over time (actual recovered / total at-risk)",
        "Leakage breakdown by failure category and gateway",
        "Recovery funnel: detected → scored → actioned → recovered",
        "Cohort analysis by payment method and customer segment",
        "Exportable reports in CSV and PDF",
      ]}
    />
  );
}
