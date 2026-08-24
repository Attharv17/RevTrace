/**
 * LedgerPilot — Dataset API Client
 * Typed functions for the /api/data endpoints.
 */
import { api } from "./client";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ExceptionBreakdownItem {
  exception_type: string;
  count: number;
  percentage: number;
  expected_match: boolean;
}

export interface RecordCounts {
  gateway_transactions: number;
  merchant_orders: number;
  bank_settlements: number;
  ground_truth: number;
  total: number;
}

export interface FinancialStats {
  total_volume_inr: number;
  total_settled_inr: number;
  total_gateway_fees_inr: number;
  total_tax_inr: number;
  avg_transaction_inr: number;
  min_transaction_inr: number;
  max_transaction_inr: number;
}

export interface PaymentMethodBreakdown {
  method: string;
  count: number;
  volume_inr: number;
  percentage: number;
}

export interface SettlementCoverage {
  total_transactions: number;
  with_settlement: number;
  missing_settlement: number;
  match_rate_pct: number;
}

export interface DatasetSummary {
  record_counts: RecordCounts;
  financial: FinancialStats;
  exception_breakdown: ExceptionBreakdownItem[];
  payment_method_breakdown: PaymentMethodBreakdown[];
  top_merchants: { name: string; count: number }[];
  settlement_coverage: SettlementCoverage;
  seed: number;
  generated_at: string | null;
  date_range: { start: string | null; end: string | null };
}

export interface GenerateResponse {
  status: string;
  seed: number;
  num_transactions: number;
  generated_at: string;
  record_counts: RecordCounts;
  exception_breakdown: ExceptionBreakdownItem[];
}

export interface DatasetStatus {
  loaded: boolean;
  message?: string;
  seed?: number;
  generated_at?: string;
  num_transactions?: number;
  num_settlements?: number;
  num_ground_truth?: number;
}

// ── API Functions ─────────────────────────────────────────────────────────────

/** Generate (or regenerate) the synthetic dataset. */
export const generateDataset = (
  seed = 42,
  num_transactions = 600
): Promise<GenerateResponse> =>
  api.post<GenerateResponse>("/api/data/generate", { seed, num_transactions });

/** Get full summary statistics of the loaded dataset. */
export const getDatasetSummary = (): Promise<DatasetSummary> =>
  api.get<DatasetSummary>("/api/data/summary");

/** Get exception type breakdown. */
export const getExceptionBreakdown = (): Promise<{
  total: number;
  breakdown: ExceptionBreakdownItem[];
}> => api.get("/api/data/exceptions");

/** Get dataset status (loaded / not loaded). */
export const getDatasetStatus = (): Promise<DatasetStatus> =>
  api.get<DatasetStatus>("/api/data/status");

/** Return the CSV download URL for a given table. */
export const getCsvDownloadUrl = (
  table: "gateway_transactions" | "merchant_orders" | "bank_settlements"
): string => `/api/data/export/${table}`;
