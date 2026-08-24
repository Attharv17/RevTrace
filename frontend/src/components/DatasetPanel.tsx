import { useState, useEffect, useCallback } from "react";
import {
  Database,
  RefreshCcw,
  Download,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  ArrowUpRight,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  generateDataset,
  getDatasetStatus,
  getDatasetSummary,
  getCsvDownloadUrl,
  type DatasetSummary,
  type DatasetStatus,
} from "@/api/dataset";

// ── Exception badge colour map ────────────────────────────────────────────────
const EXC_BADGE: Record<string, string> = {
  exact_match:         "badge-success",
  missing_settlement:  "badge-danger",
  duplicate:           "badge-danger",
  reference_mismatch:  "badge-danger",
  amount_mismatch:     "badge-warning",
  fee_difference:      "badge-warning",
  tax_difference:      "badge-warning",
  timing_difference:   "badge-info",
  partial_settlement:  "badge-warning",
  refund:              "badge-info",
  reversal:            "badge-danger",
};

const EXC_LABEL: Record<string, string> = {
  exact_match:         "Exact Match",
  missing_settlement:  "Missing Settlement",
  duplicate:           "Duplicate",
  reference_mismatch:  "Ref Mismatch",
  amount_mismatch:     "Amount Mismatch",
  fee_difference:      "Fee Difference",
  tax_difference:      "Tax Difference",
  timing_difference:   "Timing Difference",
  partial_settlement:  "Partial Settlement",
  refund:              "Refund",
  reversal:            "Reversal",
};

// ── Utility ───────────────────────────────────────────────────────────────────
function fmtInr(n: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

// ── Component ─────────────────────────────────────────────────────────────────
export function DatasetPanel() {
  const [status, setStatus]   = useState<DatasetStatus | null>(null);
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  // Check initial status on mount
  useEffect(() => {
    getDatasetStatus()
      .then(setStatus)
      .catch(() => setStatus({ loaded: false }));
  }, []);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await generateDataset(42, 600);
      const [newStatus, newSummary] = await Promise.all([
        getDatasetStatus(),
        getDatasetSummary(),
      ]);
      setStatus(newStatus);
      setSummary(newSummary);
      setExpanded(true);
    } catch (e) {
      setError("Failed to generate dataset. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleLoadSummary = useCallback(async () => {
    if (!status?.loaded) return;
    setLoading(true);
    try {
      setSummary(await getDatasetSummary());
      setExpanded(true);
    } catch {
      setError("Failed to load summary.");
    } finally {
      setLoading(false);
    }
  }, [status]);

  const isLoaded = status?.loaded ?? false;

  return (
    <div className={cn(
      "card border-l-4 animate-fade-in",
      isLoaded
        ? "border-l-emerald-500 dark:border-l-emerald-400"
        : "border-l-[var(--border-strong)]"
    )}>
      {/* ── Header row ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            isLoaded
              ? "bg-emerald-50 dark:bg-emerald-900/20"
              : "bg-[var(--bg-surface-3)]"
          )}>
            <Database
              size={16}
              className={isLoaded ? "text-emerald-600 dark:text-emerald-400" : "text-[var(--text-muted)]"}
            />
          </div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">
              Demo Dataset
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              {isLoaded
                ? `Loaded · ${status?.num_transactions?.toLocaleString()} transactions · Seed ${status?.seed}`
                : "No dataset loaded — generate a synthetic batch to power the dashboard"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isLoaded && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="btn-ghost py-1.5 text-xs"
            >
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              {expanded ? "Hide" : "Details"}
            </button>
          )}
          <button
            id="dataset-generate-btn"
            onClick={isLoaded ? handleLoadSummary : handleGenerate}
            disabled={loading}
            className={cn(
              "btn-primary text-xs py-1.5 px-3",
              loading && "opacity-70 cursor-not-allowed"
            )}
          >
            {loading
              ? <><Loader2 size={13} className="animate-spin" /> Generating…</>
              : isLoaded
                ? <><RefreshCcw size={13} /> Refresh</>
                : <><Database size={13} /> Load Demo Batch</>
            }
          </button>
        </div>
      </div>

      {/* ── Error banner ───────────────────────────────────────────────────── */}
      {error && (
        <div className="mx-5 mb-4 px-4 py-2.5 rounded-lg bg-red-50 dark:bg-red-900/20
                        border border-red-200 dark:border-red-800
                        text-xs text-red-700 dark:text-red-400 flex items-center gap-2">
          <AlertTriangle size={13} />
          {error}
        </div>
      )}

      {/* ── Expanded summary ───────────────────────────────────────────────── */}
      {expanded && summary && (
        <div className="border-t border-[var(--border)] px-5 pb-5 pt-4 space-y-5 animate-fade-in">

          {/* Record counts */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Gateway Txns",   value: summary.record_counts.gateway_transactions, icon: TrendingUp },
              { label: "Merchant Orders", value: summary.record_counts.merchant_orders,     icon: CheckCircle2 },
              { label: "Settlements",    value: summary.record_counts.bank_settlements,    icon: ArrowUpRight },
              { label: "Total Records",  value: summary.record_counts.total,               icon: Database },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-lg bg-[var(--bg-surface-2)] border border-[var(--border)] p-3">
                <Icon size={13} className="text-[var(--text-muted)] mb-1" />
                <p className="text-lg font-bold font-mono text-[var(--text-primary)]">
                  {value.toLocaleString()}
                </p>
                <p className="text-[11px] text-[var(--text-muted)]">{label}</p>
              </div>
            ))}
          </div>

          {/* Financial summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {[
              { label: "Total Volume",   value: fmtInr(summary.financial.total_volume_inr) },
              { label: "Avg Transaction", value: fmtInr(summary.financial.avg_transaction_inr) },
              { label: "Settlement Rate", value: `${summary.settlement_coverage.match_rate_pct}%` },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between items-center
                                          px-3 py-2 rounded-lg bg-[var(--bg-surface-3)]">
                <span className="text-[var(--text-secondary)]">{label}</span>
                <span className="font-semibold font-mono text-[var(--text-primary)]">{value}</span>
              </div>
            ))}
          </div>

          {/* Exception breakdown table */}
          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
              Exception Breakdown
            </p>
            <div className="table-wrapper">
              <table className="lp-table text-xs">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th className="text-right">Count</th>
                    <th className="text-right">%</th>
                    <th>Bar</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.exception_breakdown.map((exc) => (
                    <tr key={exc.exception_type}>
                      <td>
                        <span className={`badge ${EXC_BADGE[exc.exception_type] ?? "badge-neutral"} text-[10px]`}>
                          {EXC_LABEL[exc.exception_type] ?? exc.exception_type}
                        </span>
                      </td>
                      <td className="text-right font-mono font-medium text-[var(--text-primary)]">
                        {exc.count}
                      </td>
                      <td className="text-right text-[var(--text-muted)]">{exc.percentage}%</td>
                      <td className="w-28">
                        <div className="h-1.5 bg-[var(--bg-surface-3)] rounded-full overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              exc.expected_match ? "bg-emerald-500" : "bg-amber-400"
                            )}
                            style={{ width: `${exc.percentage}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Download links */}
          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
              Download CSVs
            </p>
            <div className="flex flex-wrap gap-2">
              {(["gateway_transactions", "merchant_orders", "bank_settlements"] as const).map((table) => (
                <a
                  key={table}
                  href={getCsvDownloadUrl(table)}
                  download
                  className="btn-ghost text-xs py-1.5 px-3"
                >
                  <Download size={12} />
                  {table.replace(/_/g, " ")}
                </a>
              ))}
            </div>
            <p className="text-[11px] text-[var(--text-muted)] mt-2">
              Ground truth labels are kept hidden. Seed: {summary.seed} ·
              Date range: {summary.date_range.start} to {summary.date_range.end}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
