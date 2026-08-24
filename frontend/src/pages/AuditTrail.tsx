import { ClipboardList, Shield, Search } from "lucide-react";

const AUDIT_EVENTS = [
  { id: "AUD-001", user: "system",       action: "Auto-match completed",     entity: "BATCH-2024-0823-01", time: "09:14:22", type: "info" },
  { id: "AUD-002", user: "priya.s",      action: "Exception resolved",       entity: "EXC-001",            time: "09:32:10", type: "success" },
  { id: "AUD-003", user: "system",       action: "Settlement batch created",  entity: "SET-002",            time: "10:00:00", type: "info" },
  { id: "AUD-004", user: "admin",        action: "Rule configuration updated",entity: "RULE-007",           time: "11:18:44", type: "warning" },
  { id: "AUD-005", user: "raj.k",        action: "Manual match applied",      entity: "TXN-004",            time: "12:05:33", type: "success" },
];

const TYPE_BADGE: Record<string, string> = {
  info:    "badge-info",
  success: "badge-success",
  warning: "badge-warning",
  danger:  "badge-danger",
};

export function AuditTrail() {
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Trail</h1>
          <p className="page-subtitle">Immutable log of all system and user actions</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost"><Search size={14} />Search logs</button>
          <span className="badge badge-success gap-1.5">
            <Shield size={11} />
            Tamper-proof
          </span>
        </div>
      </div>

      <div className="card">
        <div className="px-5 py-4 border-b border-[var(--border)] flex items-center gap-2">
          <ClipboardList size={15} className="text-[var(--text-secondary)]" />
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            Audit Events — Today (sample)
          </h2>
        </div>
        <div className="table-wrapper border-0 rounded-none">
          <table className="lp-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>User</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Type</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {AUDIT_EVENTS.map((ev) => (
                <tr key={ev.id}>
                  <td><code className="text-xs font-mono text-[var(--navy)]">{ev.id}</code></td>
                  <td>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-[var(--bg-surface-3)] flex items-center justify-center text-[10px] font-bold uppercase">
                        {ev.user[0]}
                      </span>
                      <span className="text-[var(--text-primary)]">{ev.user}</span>
                    </span>
                  </td>
                  <td>{ev.action}</td>
                  <td><code className="text-xs font-mono">{ev.entity}</code></td>
                  <td><span className={`badge ${TYPE_BADGE[ev.type]}`}>{ev.type}</span></td>
                  <td className="text-[var(--text-muted)] font-mono text-xs">{ev.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
