import { type LucideIcon } from "lucide-react";

interface PhasePlaceholderProps {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  phase: string;
  description: string;
  features: string[];
}

/**
 * Honest placeholder for pages not yet implemented.
 * Does NOT display any financial metrics or fabricated values.
 */
export function PhasePlaceholder({
  icon: Icon,
  title,
  subtitle,
  phase,
  description,
  features,
}: PhasePlaceholderProps) {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">{subtitle}</p>
        </div>
        <span className="badge badge-neutral">{phase}</span>
      </div>

      {/* Main placeholder card */}
      <div className="card p-10 flex flex-col items-center justify-center text-center gap-5 min-h-[320px] animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-[var(--accent-violet-light)] dark:bg-violet-900/20 flex items-center justify-center">
          <Icon size={28} className="text-[var(--accent-violet)]" />
        </div>
        <div className="max-w-md">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
            {title}
          </h2>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            {description}
          </p>
        </div>

        {/* Features preview */}
        <div className="w-full max-w-sm mt-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)] mb-3">
            Coming in {phase}
          </p>
          <ul className="space-y-2 text-left">
            {features.map((f) => (
              <li
                key={f}
                className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-violet)] flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Honest data notice */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface-2)] p-4 text-sm text-[var(--text-muted)]">
        No financial data is displayed here yet. All metrics will be derived from
        real transaction records once the data pipeline is implemented.
      </div>
    </div>
  );
}
