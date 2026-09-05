import { useEffect, useState } from "react";
import {
  Activity,
  Database,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
} from "lucide-react";
import { api } from "@/api/client";
import type { HealthResponse } from "@/types";

export function Overview() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<HealthResponse>("/api/health")
      .then((data) => setHealth(data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">
            System status and RevTrace foundation — Phase 1
          </p>
        </div>
        <span className="badge badge-info">Phase 1 — Foundation</span>
      </div>

      {/* System status cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* API Status */}
        <div className="card p-5 flex items-start gap-4 animate-fade-in">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              loading
                ? "bg-slate-100 dark:bg-slate-800"
                : health?.status === "ok"
                ? "bg-emerald-100 dark:bg-emerald-900/30"
                : "bg-red-100 dark:bg-red-900/30"
            }`}
          >
            {loading ? (
              <Activity size={20} className="text-slate-400 animate-pulse" />
            ) : health?.status === "ok" ? (
              <CheckCircle size={20} className="text-emerald-600 dark:text-emerald-400" />
            ) : (
              <AlertCircle size={20} className="text-red-500" />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
              API Status
            </p>
            <p className="text-base font-semibold text-[var(--text-primary)] mt-0.5">
              {loading ? "Checking…" : health?.status === "ok" ? "Online" : "Unreachable"}
            </p>
            {health && (
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                v{health.version} · {health.environment}
              </p>
            )}
          </div>
        </div>

        {/* Database Status */}
        <div className="card p-5 flex items-start gap-4 animate-fade-in">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              loading
                ? "bg-slate-100 dark:bg-slate-800"
                : health?.database === "connected"
                ? "bg-blue-100 dark:bg-blue-900/30"
                : "bg-amber-100 dark:bg-amber-900/30"
            }`}
          >
            <Database
              size={20}
              className={
                loading
                  ? "text-slate-400 animate-pulse"
                  : health?.database === "connected"
                  ? "text-blue-600 dark:text-blue-400"
                  : "text-amber-600 dark:text-amber-400"
              }
            />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
              Database
            </p>
            <p className="text-base font-semibold text-[var(--text-primary)] mt-0.5">
              {loading ? "Checking…" : health?.database === "connected" ? "Connected" : "Unreachable"}
            </p>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Financial schema added in Phase 2
            </p>
          </div>
        </div>

        {/* Uptime */}
        <div className="card p-5 flex items-start gap-4 animate-fade-in">
          <div className="w-10 h-10 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center flex-shrink-0">
            <Clock size={20} className="text-violet-600 dark:text-violet-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
              Uptime
            </p>
            <p className="text-base font-semibold text-[var(--text-primary)] mt-0.5">
              {loading ? "—" : health ? `${Math.round(health.uptime_seconds)}s` : "—"}
            </p>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Since last server start
            </p>
          </div>
        </div>
      </div>

      {/* Phase roadmap */}
      <div className="card p-6 animate-fade-in">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={16} className="text-[var(--accent-violet)]" />
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            Build Roadmap
          </h2>
        </div>
        <div className="space-y-3">
          {[
            { phase: "Phase 1", label: "Foundation + Fintech UI", status: "complete" },
            { phase: "Phase 2", label: "Financial Event Ingestion + Data Schema", status: "pending" },
            { phase: "Phase 3", label: "Revenue Leakage Detection Engine", status: "pending" },
            { phase: "Phase 4", label: "Recovery Opportunity Scoring + AI Investigation", status: "pending" },
            { phase: "Phase 5", label: "Recovery Workflow + Outcome Tracking", status: "pending" },
            { phase: "Phase 6", label: "Analytics Dashboard + Evaluation", status: "pending" },
          ].map(({ phase, label, status }) => (
            <div
              key={phase}
              className="flex items-center gap-3 text-sm"
            >
              <span
                className={`flex-shrink-0 w-2 h-2 rounded-full ${
                  status === "complete"
                    ? "bg-emerald-500"
                    : "bg-[var(--border-strong)]"
                }`}
              />
              <span className="font-medium text-[var(--text-secondary)] w-20 flex-shrink-0">
                {phase}
              </span>
              <span
                className={
                  status === "complete"
                    ? "text-[var(--text-primary)]"
                    : "text-[var(--text-muted)]"
                }
              >
                {label}
              </span>
              {status === "complete" && (
                <span className="badge badge-success ml-auto">Complete</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* No financial data notice */}
      <div className="rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50 dark:bg-amber-900/10 p-4 text-sm text-amber-800 dark:text-amber-400">
        <strong>Note:</strong> Financial data, leakage detection, and recovery metrics will appear here in Phase 2+.
        This page currently shows only system health from real API calls. No financial values are fabricated.
      </div>
    </div>
  );
}
