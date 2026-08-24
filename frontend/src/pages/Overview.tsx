import {
  ArrowUpRight,
  DollarSign,
  RefreshCcw,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Clock,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";
import { DatasetPanel } from "@/components/DatasetPanel";

// ── Placeholder KPI Data ──────────────────────────────────────────────────────

const KPI_DATA = [
  {
    id: "total-volume",
    label: "Total Transaction Volume",
    value: "$4.82M",
    delta: "+12.4%",
    type: "positive" as const,
    icon: DollarSign,
    color: "blue",
    desc: "vs. last 30 days",
  },
  {
    id: "reconciled",
    label: "Reconciled",
    value: "98.6%",
    delta: "+0.4%",
    type: "positive" as const,
    icon: CheckCircle2,
    color: "green",
    desc: "match rate",
  },
  {
    id: "exceptions",
    label: "Open Exceptions",
    value: "47",
    delta: "-8",
    type: "positive" as const,
    icon: AlertTriangle,
    color: "amber",
    desc: "since yesterday",
  },
  {
    id: "pending",
    label: "Pending Settlements",
    value: "$218K",
    delta: "+3",
    type: "neutral" as const,
    icon: Clock,
    color: "indigo",
    desc: "awaiting clearance",
  },
];

// ── Placeholder chart data ────────────────────────────────────────────────────

const VOLUME_DATA = [
  { date: "Aug 17", volume: 3200, reconciled: 3150 },
  { date: "Aug 18", volume: 4100, reconciled: 4020 },
  { date: "Aug 19", volume: 3800, reconciled: 3760 },
  { date: "Aug 20", volume: 4700, reconciled: 4620 },
  { date: "Aug 21", volume: 3300, reconciled: 3260 },
  { date: "Aug 22", volume: 5100, reconciled: 5030 },
  { date: "Aug 23", volume: 4820, reconciled: 4760 },
];

const RECENT_TRANSACTIONS = [
  { id: "TXN-001", counterparty: "Razorpay Gateway",   amount: "$12,480.00", status: "Matched",  time: "2 min ago" },
  { id: "TXN-002", counterparty: "HDFC Bank NEFT",     amount: "$8,200.00",  status: "Pending",  time: "5 min ago" },
  { id: "TXN-003", counterparty: "Stripe US",          amount: "$34,750.00", status: "Matched",  time: "11 min ago" },
  { id: "TXN-004", counterparty: "PayPal Intl",        amount: "$2,100.00",  status: "Exception",time: "18 min ago" },
  { id: "TXN-005", counterparty: "Axis Bank RTGS",     amount: "$56,000.00", status: "Matched",  time: "24 min ago" },
];

const STATUS_BADGE = {
  Matched:   "badge-success",
  Pending:   "badge-warning",
  Exception: "badge-danger",
} as Record<string, string>;

const COLOR_MAP = {
  blue:   { bg: "bg-blue-50 dark:bg-blue-900/20", icon: "text-blue-600 dark:text-blue-400" },
  green:  { bg: "bg-emerald-50 dark:bg-emerald-900/20", icon: "text-emerald-600 dark:text-emerald-400" },
  amber:  { bg: "bg-amber-50 dark:bg-amber-900/20", icon: "text-amber-600 dark:text-amber-400" },
  indigo: { bg: "bg-indigo-50 dark:bg-indigo-900/20", icon: "text-indigo-600 dark:text-indigo-400" },
};

// ── Component ─────────────────────────────────────────────────────────────────

export function Overview() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard Overview</h1>
          <p className="page-subtitle">
            Real-time summary · Updated just now
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-success gap-1.5">
            <span className="status-dot-green" />
            All Systems Operational
          </span>
          <button className="btn-primary">
            <RefreshCcw size={14} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Dataset Panel ────────────────────────────────────────────────── */}
      <DatasetPanel />

      {/* ── KPI Cards ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {KPI_DATA.map(({ id, label, value, delta, type, icon: Icon, color, desc }) => {
          const colors = COLOR_MAP[color as keyof typeof COLOR_MAP];
          return (
            <div key={id} id={`kpi-${id}`} className="kpi-card">
              <div className="flex items-start justify-between">
                <div className={cn("p-2.5 rounded-lg", colors.bg)}>
                  <Icon size={18} className={colors.icon} />
                </div>
                <span
                  className={cn(
                    "flex items-center gap-0.5 text-xs font-semibold",
                    type === "positive"
                      ? "text-emerald-600 dark:text-emerald-400"
                      : "text-[var(--text-secondary)]"
                  )}
                >
                  {type === "positive" && <ArrowUpRight size={13} />}
                  {delta}
                </span>
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--text-primary)] font-mono tracking-tight">
                  {value}
                </p>
                <p className="text-sm text-[var(--text-secondary)] mt-0.5">{label}</p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">{desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Chart + Activity ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Volume Chart */}
        <div className="card p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                Transaction Volume
              </h2>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Last 7 days — volume vs. reconciled
              </p>
            </div>
            <TrendingUp size={16} className="text-[var(--accent-blue)]" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={VOLUME_DATA} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorReconciled" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#10B981" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "var(--text-primary)",
                  boxShadow: "0 4px 12px rgba(0,0,0,.1)",
                }}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={((val: number, name: string) => [
                `$${val.toLocaleString()}`,
                name === "volume" ? "Volume" : "Reconciled",
              ]) as any}
              />
              <Area
                type="monotone"
                dataKey="volume"
                stroke="#3B82F6"
                strokeWidth={2}
                fill="url(#colorVolume)"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="reconciled"
                stroke="#10B981"
                strokeWidth={2}
                fill="url(#colorReconciled)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
          {/* Legend */}
          <div className="flex items-center gap-4 mt-3">
            <span className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
              <span className="w-3 h-0.5 rounded bg-accent-blue inline-block" />
              Volume
            </span>
            <span className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
              <span className="w-3 h-0.5 rounded bg-accent-green inline-block" />
              Reconciled
            </span>
          </div>
        </div>

        {/* Reconciliation Status Breakdown */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
            Reconciliation Status
          </h2>
          <div className="space-y-3">
            {[
              { label: "Auto-Matched",  pct: 86, color: "bg-emerald-500" },
              { label: "Manual Review", pct: 9,  color: "bg-amber-400" },
              { label: "Exceptions",    pct: 3,  color: "bg-red-500" },
              { label: "Pending",       pct: 2,  color: "bg-slate-400" },
            ].map(({ label, pct, color }) => (
              <div key={label}>
                <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-1">
                  <span>{label}</span>
                  <span className="font-medium text-[var(--text-primary)]">{pct}%</span>
                </div>
                <div className="h-1.5 w-full bg-[var(--bg-surface-3)] rounded-full overflow-hidden">
                  <div
                    className={cn("h-full rounded-full transition-all duration-500", color)}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Summary stats */}
          <div className="mt-5 pt-4 border-t border-[var(--border)] grid grid-cols-2 gap-3">
            {[
              { label: "Today's batches", value: "24" },
              { label: "STP Rate",        value: "86%" },
              { label: "Avg match time",  value: "1.4s" },
              { label: "Rules active",    value: "12" },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-lg font-bold text-[var(--text-primary)] font-mono">{value}</p>
                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Recent Transactions ─────────────────────────────────────────── */}
      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            Recent Transactions
          </h2>
          <button className="text-xs font-medium text-[var(--accent-blue)] hover:underline">
            View all →
          </button>
        </div>
        <div className="table-wrapper border-0 rounded-none">
          <table className="lp-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Counterparty</th>
                <th className="text-right">Amount</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_TRANSACTIONS.map((tx) => (
                <tr key={tx.id}>
                  <td>
                    <code className="text-xs font-mono text-[var(--navy)]">
                      {tx.id}
                    </code>
                  </td>
                  <td className="text-[var(--text-primary)]">{tx.counterparty}</td>
                  <td className="text-right font-mono font-medium text-[var(--text-primary)]">
                    {tx.amount}
                  </td>
                  <td>
                    <span className={STATUS_BADGE[tx.status] ?? "badge-neutral"}>
                      {tx.status}
                    </span>
                  </td>
                  <td className="text-[var(--text-muted)]">{tx.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
