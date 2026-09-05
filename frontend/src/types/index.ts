// ── API Types ────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: "ok" | "degraded";
  version: string;
  environment: string;
  database: "connected" | "unreachable";
  uptime_seconds: number;
}

// ── Navigation ───────────────────────────────────────────────────────────────

export interface NavItem {
  id: string;
  label: string;
  path: string;
  badge?: number; // notification count
}

// ── Theme ─────────────────────────────────────────────────────────────────────

export type Theme = "light" | "dark";

// ── Phase 4 — Recovery Opportunity types ─────────────────────────────────────

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type OpportunityStatus = "pending" | "in_progress" | "recovered" | "unrecoverable";

export interface Opportunity {
  id: number;
  transaction_id: string;
  expected_revenue: number;
  realized_revenue: number;
  revenue_at_risk: number;
  recoverable_amount: number;
  reason: string;
  severity: Severity;
  status: OpportunityStatus;
  
  // Phase 5: Scoring fields
  recovery_probability?: number;
  expected_recovery?: number;
  priority?: string;
  recommended_action?: string;
  decision_band?: string;
  score_version?: string;
  score_metadata?: string;
  scored_at?: string;

  detected_at: string;
  updated_at: string;
}

export interface OpportunityListOut {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
}

export interface OpportunitySummary {
  total_opportunities: number;
  total_revenue_at_risk: number;
  total_realized_revenue: number;
  total_expected_revenue: number;
  total_recoverable_amount: number;
  pending_count: number;
  in_progress_count: number;
  recovered_count: number;
  unrecoverable_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface LeakageRunStats {
  transactions_scanned: number;
  opportunities_created: number;
  opportunities_updated: number;
  skipped_not_applicable: number;
  duration_seconds: number;
}

// ── Phase 7 — AI Investigation Agent types ────────────────────────────────────

export interface InvestigationRequest {
  transaction_id: string;
  question: string;
}

export interface ToolCallLog {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: string;
  called_at: string;
}

export interface InvestigationReport {
  transaction_id: string;
  question: string;

  // DB-sourced scoring data (never LLM-invented)
  recovery_probability?: number;
  decision_band?: string;   // GREEN | AMBER | RED

  // LLM-synthesized fields (grounded in tool call results)
  evidence: string[];
  revenue_impact?: string;
  recommendation?: string;
  confidence_note?: string;

  // Error / degraded state flags
  llm_unavailable: boolean;
  not_found: boolean;
  error_message?: string;

  // Audit trail
  tool_calls_log: ToolCallLog[];
  investigated_at: string;
}

export interface AssistantHealthResponse {
  llm_configured: boolean;
  llm_model: string;
  status: "ready" | "degraded" | "unavailable";
  message: string;
}
