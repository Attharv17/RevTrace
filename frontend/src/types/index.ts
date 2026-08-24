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
  icon: string;   // lucide-react icon name
  badge?: number; // notification count
}

// ── KPI Cards (Phase 2 will populate from real data) ─────────────────────────

export interface KpiCard {
  id: string;
  label: string;
  value: string;
  delta: string;
  deltaType: "positive" | "negative" | "neutral";
  icon: string;
  accentColor: string;
}

// ── Theme ─────────────────────────────────────────────────────────────────────

export type Theme = "light" | "dark";
