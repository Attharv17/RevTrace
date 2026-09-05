import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  XCircle,
  Zap,
  TrendingUp,
  ShieldAlert,
  Filter,
  Calculator,
  Bot,
} from "lucide-react";
import { opportunitiesApi } from "@/api/opportunities";
import type {
  Opportunity,
  OpportunitySummary,
  OpportunityStatus,
} from "@/types";

// ── Helpers ──────────────────────────────────────────────────────────────────

const formatINR = (v: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(v);

const STATUS_CONFIG: Record<OpportunityStatus, { label: string; className: string; icon: typeof Clock }> = {
  pending:       { label: "Pending",       className: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",   icon: Clock },
  in_progress:   { label: "In Progress",   className: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300", icon: RefreshCw },
  recovered:     { label: "Recovered",     className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300", icon: CheckCircle2 },
  unrecoverable: { label: "Unrecoverable", className: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",     icon: XCircle },
};

const BAND_CLASSES: Record<string, string> = {
  GREEN: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300 border border-green-200 dark:border-green-800",
  AMBER: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300 border border-yellow-200 dark:border-yellow-800",
  RED:   "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border border-red-200 dark:border-red-800",
};

// ── Summary cards ────────────────────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  sub,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 flex gap-4 items-start shadow-sm">
      <div className={`p-2.5 rounded-lg ${accent}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-foreground truncate">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export function Opportunities() {
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]); 
  const [summary, setSummary] = useState<OpportunitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [scoringRunning, setScoringRunning] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 25;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [list, sum] = await Promise.all([
        opportunitiesApi.list({
          status: statusFilter || undefined,
          severity: severityFilter || undefined,
          page,
          page_size: PAGE_SIZE,
        }),
        opportunitiesApi.summary(),
      ]);
      setOpportunities(list.items);
      setTotal(list.total);
      setSummary(sum);
    } catch (e: unknown) {
      setError("Failed to load opportunities. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, severityFilter, page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRunDetection = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const stats = await opportunitiesApi.runLeakageDetection();
      setRunMsg(
        `Detection complete — ${stats.opportunities_created} created, ${stats.opportunities_updated} updated in ${stats.duration_seconds}s`
      );
      await fetchData();
    } catch {
      setRunMsg("Detection failed. Check backend logs.");
    } finally {
      setRunning(false);
    }
  };

  const handleRunScoring = async () => {
    setScoringRunning(true);
    setRunMsg(null);
    try {
      const stats = await opportunitiesApi.runScoringEngine();
      setRunMsg(
        `Scoring complete — ${stats.opportunities_scored} scored in ${stats.duration_seconds}s`
      );
      await fetchData();
    } catch {
      setRunMsg("Scoring failed. Check backend logs.");
    } finally {
      setScoringRunning(false);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Recovery Opportunities</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Deterministic leakage detection — all figures are verified database records.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border border-border bg-card hover:bg-accent transition-colors text-foreground disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleRunDetection}
            disabled={running || scoringRunning}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm bg-primary/10 text-primary hover:bg-primary/20 transition-colors font-medium disabled:opacity-50"
          >
            <Zap className="h-4 w-4" />
            {running ? "Running…" : "Detect Leakage"}
          </button>
          <button
            onClick={handleRunScoring}
            disabled={running || scoringRunning}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm bg-primary text-primary-foreground hover:opacity-90 transition-opacity font-medium disabled:opacity-50"
          >
            <Calculator className="h-4 w-4" />
            {scoringRunning ? "Scoring…" : "Run Scoring"}
          </button>
        </div>
      </div>

      {runMsg && (
        <div className="rounded-lg border border-border bg-card px-4 py-3 text-sm text-muted-foreground">
          {runMsg}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard
            label="Total at Risk"
            value={formatINR(summary.total_revenue_at_risk)}
            sub={`${summary.total_opportunities} opportunities`}
            icon={ShieldAlert}
            accent="bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-300"
          />
          <SummaryCard
            label="Realized Revenue"
            value={formatINR(summary.total_realized_revenue)}
            sub="From partial/full recoveries"
            icon={CheckCircle2}
            accent="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-300"
          />
          <SummaryCard
            label="Recoverable (GT)"
            value={formatINR(summary.total_recoverable_amount)}
            sub="Ground truth estimate"
            icon={TrendingUp}
            accent="bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300"
          />
          <SummaryCard
            label="Critical / High"
            value={`${summary.critical_count + summary.high_count}`}
            sub={`${summary.critical_count} critical · ${summary.high_count} high`}
            icon={AlertTriangle}
            accent="bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-300"
          />
        </div>
      )}

      {/* Status breakdown */}
      {summary && (
        <div className="grid grid-cols-4 gap-3">
          {(
            [
              ["pending", summary.pending_count],
              ["in_progress", summary.in_progress_count],
              ["recovered", summary.recovered_count],
              ["unrecoverable", summary.unrecoverable_count],
            ] as [OpportunityStatus, number][]
          ).map(([s, count]) => {
            const cfg = STATUS_CONFIG[s];
            const Icon = cfg.icon;
            return (
              <button
                key={s}
                onClick={() => { setStatusFilter(statusFilter === s ? "" : s); setPage(1); }}
                className={`rounded-lg border border-border p-3 flex items-center gap-2 text-sm font-medium transition-all ${
                  statusFilter === s ? "ring-2 ring-primary" : "bg-card hover:bg-accent"
                } ${cfg.className}`}
              >
                <Icon className="h-4 w-4" />
                <span className="capitalize">{cfg.label}</span>
                <span className="ml-auto font-bold">{count}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <select
          value={severityFilter}
          onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
          className="text-sm rounded-lg border border-border bg-card px-3 py-1.5 text-foreground"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        {(statusFilter || severityFilter) && (
          <button
            onClick={() => { setStatusFilter(""); setSeverityFilter(""); setPage(1); }}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Clear filters
          </button>
        )}
        <span className="ml-auto text-xs text-muted-foreground">
          {total} opportunities
        </span>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Transaction</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Reason</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Expected</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Realized</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">At Risk</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Score</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Exp. Rec</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Action</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">Band</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">Investigate</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />
                    Loading opportunities…
                  </td>
                </tr>
              ) : opportunities.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                    No opportunities found.{" "}
                    <button onClick={handleRunDetection} className="underline hover:text-foreground">
                      Run detection
                    </button>{" "}
                    to detect leakage from ingested transactions.
                  </td>
                </tr>
              ) : (
                opportunities.map((opp) => {
                  const statusCfg = STATUS_CONFIG[opp.status];
                  const StatusIcon = statusCfg.icon;
                  return (
                    <tr key={opp.id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs text-foreground">{opp.transaction_id}</span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{opp.reason}</td>
                      <td className="px-4 py-3 text-right font-mono text-foreground">{formatINR(opp.expected_revenue)}</td>
                      <td className="px-4 py-3 text-right font-mono text-emerald-600 dark:text-emerald-400">{formatINR(opp.realized_revenue)}</td>
                      <td className="px-4 py-3 text-right font-mono font-semibold text-red-600 dark:text-red-400">{formatINR(opp.revenue_at_risk)}</td>
                      <td className="px-4 py-3 text-right font-mono text-foreground">
                        {opp.recovery_probability !== undefined && opp.recovery_probability !== null ? `${(opp.recovery_probability * 100).toFixed(1)}%` : "—"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-blue-600 dark:text-blue-400">
                        {opp.expected_recovery !== undefined && opp.expected_recovery !== null ? formatINR(opp.expected_recovery) : "—"}
                      </td>
                      <td className="px-4 py-3 text-left text-xs text-muted-foreground">
                        {opp.recommended_action || "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {opp.decision_band ? (
                          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold tracking-wide ${BAND_CLASSES[opp.decision_band]}`}>
                            {opp.decision_band}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${statusCfg.className}`}>
                          <StatusIcon className="h-3 w-3" />
                          {statusCfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          id={`investigate-${opp.transaction_id}`}
                          onClick={() =>
                            navigate(
                              `/assistant?txn=${encodeURIComponent(opp.transaction_id)}&q=${encodeURIComponent("Why is this a recovery opportunity?")}`
                            )
                          }
                          title={`Investigate ${opp.transaction_id} with AI`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border border-violet-500/30 bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 transition-colors"
                        >
                          <Bot className="h-3 w-3" />
                          AI
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20 text-xs text-muted-foreground">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 rounded border border-border bg-card hover:bg-accent disabled:opacity-40 text-foreground transition-colors"
              >
                ← Prev
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 rounded border border-border bg-card hover:bg-accent disabled:opacity-40 text-foreground transition-colors"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Data source note */}
      <p className="text-xs text-muted-foreground text-center">
        All financial figures are derived from immutable source records in the <code className="font-mono text-xs">transactions</code> table.
        Ground truth recoverable amounts are labelled as such and are not live predictions.
      </p>
    </div>
  );
}
