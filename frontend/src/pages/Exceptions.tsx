import { AlertTriangle, Filter, Download } from "lucide-react";

const PLACEHOLDER_EXCEPTIONS = [
  { id: "EXC-001", type: "Amount Mismatch",  counterparty: "Razorpay",    amount: "$450.00",  severity: "High",   age: "2h" },
  { id: "EXC-002", type: "Duplicate Entry",  counterparty: "HDFC Bank",   amount: "$1,200.00", severity: "Medium", age: "4h" },
  { id: "EXC-003", type: "Missing Reference",counterparty: "Stripe US",   amount: "$780.00",  severity: "Low",    age: "6h" },
];

const SEVERITY_BADGE: Record<string, string> = {
  High:   "badge-danger",
  Medium: "badge-warning",
  Low:    "badge-info",
};

export function Exceptions() {
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Exceptions</h1>
          <p className="page-subtitle">Review and resolve reconciliation exceptions</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost"><Filter size={14} />Filter</button>
          <button className="btn-ghost"><Download size={14} />Export</button>
        </div>
      </div>

      {/* Summary pills */}
      <div className="flex flex-wrap gap-3">
        {[
          { label: "Open",     count: 47, cls: "badge-danger" },
          { label: "In Review",count: 12, cls: "badge-warning" },
          { label: "Resolved", count: 238, cls: "badge-success" },
        ].map(({ label, count, cls }) => (
          <div key={label} className="card px-4 py-3 flex items-center gap-3">
            <span className={`badge ${cls}`}>{label}</span>
            <span className="text-lg font-bold font-mono text-[var(--text-primary)]">{count}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="px-5 py-4 border-b border-[var(--border)]">
          <h2 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <AlertTriangle size={15} className="text-amber-500" />
            Open Exceptions — Sample Data
          </h2>
        </div>
        <div className="table-wrapper border-0 rounded-none">
          <table className="lp-table">
            <thead>
              <tr>
                <th>Exception ID</th>
                <th>Type</th>
                <th>Counterparty</th>
                <th className="text-right">Amount</th>
                <th>Severity</th>
                <th>Age</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {PLACEHOLDER_EXCEPTIONS.map((ex) => (
                <tr key={ex.id}>
                  <td><code className="text-xs font-mono text-[var(--navy)]">{ex.id}</code></td>
                  <td>{ex.type}</td>
                  <td>{ex.counterparty}</td>
                  <td className="text-right font-mono">{ex.amount}</td>
                  <td><span className={`badge ${SEVERITY_BADGE[ex.severity]}`}>{ex.severity}</span></td>
                  <td className="text-[var(--text-muted)]">{ex.age}</td>
                  <td>
                    <button className="text-xs font-medium text-[var(--accent-blue)] hover:underline">
                      Review →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
