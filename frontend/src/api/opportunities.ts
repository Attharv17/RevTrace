import { api } from "@/api/client";
import type {
  LeakageRunStats,
  OpportunityListOut,
  OpportunitySummary,
  Opportunity,
} from "@/types";

export interface OpportunityFilters {
  status?: string;
  severity?: string;
  reason?: string;
  page?: number;
  page_size?: number;
}

export const opportunitiesApi = {
  runLeakageDetection: (): Promise<LeakageRunStats> =>
    api.post<LeakageRunStats>("/api/leakage/run", null),

  runScoringEngine: (): Promise<{ opportunities_scanned: number; opportunities_scored: number; duration_seconds: number }> =>
    api.post("/api/scoring/run", null),

  list: (filters: OpportunityFilters = {}): Promise<OpportunityListOut> => {
    const params = new URLSearchParams();
    if (filters.status)    params.set("status", filters.status);
    if (filters.severity)  params.set("severity", filters.severity);
    if (filters.reason)    params.set("reason", filters.reason);
    if (filters.page)      params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));
    const qs = params.toString();
    return api.get<OpportunityListOut>(`/api/opportunities${qs ? `?${qs}` : ""}`);
  },

  summary: (): Promise<OpportunitySummary> =>
    api.get<OpportunitySummary>("/api/opportunities/summary"),

  getById: (id: number): Promise<Opportunity> =>
    api.get<Opportunity>(`/api/opportunities/${id}`),
};
