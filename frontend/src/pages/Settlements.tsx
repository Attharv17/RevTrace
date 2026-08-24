import { Landmark, Clock, CheckCircle2 } from "lucide-react";

const SETTLEMENTS = [
  { id: "SET-001", batch: "BATCH-2024-0823-01", amount: "$1,240,500.00", bank: "HDFC Bank",  status: "Cleared",  date: "Aug 23, 2024" },
  { id: "SET-002", batch: "BATCH-2024-0823-02", amount: "$890,200.00",   bank: "Axis Bank",  status: "Pending",  date: "Aug 23, 2024" },
  { id: "SET-003", batch: "BATCH-2024-0822-01", amount: "$2,100,000.00", bank: "ICICI Bank", status: "Cleared",  date: "Aug 22, 2024" },
];

export function Settlements() {
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settlements</h1>
          <p className="page-subtitle">Track clearing and settlement batches</p>
        </div>
        <button className="btn-primary"><Landmark size={14} />New Settlement</button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { icon: CheckCircle2, label: "Cleared Today",   value: "$3.34M", color: "text-emerald-500" },
          { icon: Clock,        label: "Pending",         value: "$890K",  color: "text-amber-500" },
          { icon: Landmark,     label: "Avg Batch Size",  value: "$1.47M", color: "text-blue-500" },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="kpi-card flex-row items-center">
            <Icon size={20} className={color} />
            <div>
              <p className="text-xl font-bold font-mono text-[var(--text-primary)]">{value}</p>
              <p className="text-xs text-[var(--text-secondary)]">{label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="px-5 py-4 border-b border-[var(--border)]">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Settlement Batches</h2>
        </div>
        <div className="table-wrapper border-0 rounded-none">
          <table className="lp-table">
            <thead>
              <tr>
                <th>Settlement ID</th>
                <th>Batch Reference</th>
                <th>Bank</th>
                <th className="text-right">Amount</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {SETTLEMENTS.map((s) => (
                <tr key={s.id}>
                  <td><code className="text-xs font-mono text-[var(--navy)]">{s.id}</code></td>
                  <td><code className="text-xs font-mono">{s.batch}</code></td>
                  <td>{s.bank}</td>
                  <td className="text-right font-mono font-medium">{s.amount}</td>
                  <td>
                    <span className={s.status === "Cleared" ? "badge-success" : "badge-warning"}>
                      {s.status}
                    </span>
                  </td>
                  <td className="text-[var(--text-muted)]">{s.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
