import { RefreshCcw, Upload, Filter } from "lucide-react";

export function Reconciliation() {
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">Reconciliation</h1>
          <p className="page-subtitle">Match and reconcile payment records across sources</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost">
            <Filter size={14} />
            Filter
          </button>
          <button className="btn-ghost">
            <Upload size={14} />
            Import
          </button>
          <button className="btn-primary">
            <RefreshCcw size={14} />
            Run Reconciliation
          </button>
        </div>
      </div>

      {/* Placeholder state */}
      <div className="card p-12 flex flex-col items-center justify-center text-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
          <RefreshCcw size={24} className="text-blue-500" />
        </div>
        <div>
          <p className="text-base font-semibold text-[var(--text-primary)]">
            Reconciliation Engine
          </p>
          <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-sm">
            Business logic will be implemented in Phase 2. This view will show
            auto-matching results, rule configuration, and manual review workflows.
          </p>
        </div>
        <span className="badge badge-info">Coming in Phase 2</span>
      </div>
    </div>
  );
}
