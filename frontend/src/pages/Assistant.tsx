/**
 * RevTrace — Phase 7: AI Investigation Assistant Page.
 *
 * Architecture:
 *   - User picks a transaction ID and asks a question
 *   - Request goes to POST /api/assistant/investigate
 *   - Agent calls read-only DB tools, synthesizes a grounded report
 *   - UI renders structured report with evidence, decision band, recommendation
 *   - Full tool audit trail is available in a collapsible panel
 *   - Degraded mode: shows raw DB data if LLM is unavailable
 */
import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Bot,
  Search,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  RefreshCw,
  Cpu,
  Database,
  TrendingUp,
  MessageSquare,
  Lightbulb,
  Target,
  Activity,
  Info,
} from "lucide-react";
import { assistantApi } from "@/api/assistant";
import type { InvestigationReport, AssistantHealthResponse } from "@/types";

// ── Helpers ──────────────────────────────────────────────────────────────────

const BAND_STYLES: Record<string, { bg: string; text: string; border: string; label: string }> = {
  GREEN: {
    bg: "bg-emerald-500/15",
    text: "text-emerald-400",
    border: "border-emerald-500/40",
    label: "GREEN — High Confidence",
  },
  AMBER: {
    bg: "bg-amber-500/15",
    text: "text-amber-400",
    border: "border-amber-500/40",
    label: "AMBER — Moderate Confidence",
  },
  RED: {
    bg: "bg-red-500/15",
    text: "text-red-400",
    border: "border-red-500/40",
    label: "RED — Low Confidence / Unrecoverable",
  },
};

const PRESET_QUESTIONS = [
  "Why is this a high recovery opportunity?",
  "What caused this revenue leakage?",
  "What recovery action is recommended?",
  "What is the customer's payment history?",
  "How does this compare to similar cases?",
];

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ report }: { report: InvestigationReport }) {
  if (report.not_found) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gray-500/15 text-gray-400 border border-gray-500/30">
        <XCircle className="h-3.5 w-3.5" />
        Transaction Not Found
      </span>
    );
  }
  if (report.llm_unavailable) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
        <AlertTriangle className="h-3.5 w-3.5" />
        Degraded Mode — Raw DB Data
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
      <CheckCircle2 className="h-3.5 w-3.5" />
      AI Investigation Complete
    </span>
  );
}

function DecisionBandCard({ band, probability }: { band?: string; probability?: number }) {
  if (!band) return null;
  const styles = BAND_STYLES[band] ?? BAND_STYLES.AMBER;
  return (
    <div className={`rounded-xl border ${styles.border} ${styles.bg} p-4 flex items-center justify-between`}>
      <div>
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
          Decision Band
        </p>
        <p className={`text-2xl font-bold ${styles.text}`}>{styles.label}</p>
      </div>
      {probability !== undefined && probability !== null && (
        <div className="text-right">
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
            Recovery Probability
          </p>
          <p className={`text-3xl font-bold ${styles.text}`}>
            {(probability * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">DB-verified score</p>
        </div>
      )}
    </div>
  );
}

function EvidencePanel({ evidence }: { evidence: string[] }) {
  if (!evidence || evidence.length === 0) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-blue-500/15">
          <Database className="h-4 w-4 text-blue-400" />
        </div>
        <h3 className="font-semibold text-foreground text-sm">Evidence (DB-Verified)</h3>
      </div>
      <ul className="space-y-2.5">
        {evidence.map((point, i) => (
          <li key={i} className="flex gap-3 text-sm text-muted-foreground leading-relaxed">
            <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex items-center justify-center">
              {i + 1}
            </span>
            <span>{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RecommendationPanel({
  recommendation,
  revenueImpact,
  confidenceNote,
}: {
  recommendation?: string;
  revenueImpact?: string;
  confidenceNote?: string;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {recommendation && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 rounded-lg bg-purple-500/15">
              <Target className="h-4 w-4 text-purple-400" />
            </div>
            <h3 className="font-semibold text-foreground text-sm">Recommendation</h3>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{recommendation}</p>
        </div>
      )}
      {revenueImpact && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 rounded-lg bg-red-500/15">
              <TrendingUp className="h-4 w-4 text-red-400" />
            </div>
            <h3 className="font-semibold text-foreground text-sm">Revenue Impact</h3>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{revenueImpact}</p>
        </div>
      )}
      {confidenceNote && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 rounded-lg bg-amber-500/15">
              <Lightbulb className="h-4 w-4 text-amber-400" />
            </div>
            <h3 className="font-semibold text-foreground text-sm">Confidence Note</h3>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{confidenceNote}</p>
        </div>
      )}
    </div>
  );
}

function ToolAuditTrail({ logs }: { report: InvestigationReport; logs: InvestigationReport["tool_calls_log"] }) {
  const [expanded, setExpanded] = useState(false);
  if (!logs || logs.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3 text-sm font-medium text-muted-foreground hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4" />
          <span>Tool Audit Trail ({logs.length} call{logs.length !== 1 ? "s" : ""})</span>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded && (
        <div className="border-t border-border divide-y divide-border">
          {logs.map((log, i) => (
            <div key={i} className="px-5 py-3 flex items-start gap-4 text-sm">
              <span className="text-xs text-muted-foreground font-mono w-4 mt-0.5 flex-shrink-0">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <code className="text-xs font-mono px-1.5 py-0.5 rounded bg-muted text-foreground">
                    {log.tool_name}
                  </code>
                  <span className="text-xs text-muted-foreground">
                    {JSON.stringify(log.arguments)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Result: <span className="text-foreground">{log.result_summary}</span>
                </p>
              </div>
              <span className="text-xs text-muted-foreground flex-shrink-0 mt-0.5">
                {new Date(log.called_at).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function NotFoundState({ transactionId }: { transactionId: string }) {
  return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-8 text-center">
      <XCircle className="h-10 w-10 text-red-400 mx-auto mb-3" />
      <h3 className="font-semibold text-foreground mb-2">Transaction Not Found</h3>
      <p className="text-sm text-muted-foreground max-w-md mx-auto">
        No transaction with ID <code className="font-mono text-foreground bg-muted px-1.5 py-0.5 rounded">{transactionId}</code> was found in the database.
        The AI agent does not invent data — verify the ID from the Opportunities or Transactions pages.
      </p>
    </div>
  );
}

// ── Health indicator ──────────────────────────────────────────────────────────

function LLMStatusBadge({ health }: { health: AssistantHealthResponse | null }) {
  if (!health) return null;
  return (
    <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
      health.status === "ready"
        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
        : "bg-amber-500/10 text-amber-400 border-amber-500/30"
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${health.status === "ready" ? "bg-emerald-400" : "bg-amber-400"} animate-pulse`} />
      <span>{health.status === "ready" ? `Gemini ${health.llm_model}` : "Degraded mode"}</span>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function Assistant() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [transactionId, setTransactionId] = useState(searchParams.get("txn") ?? "");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<AssistantHealthResponse | null>(null);

  // Fetch LLM health on mount
  useEffect(() => {
    assistantApi.health().then(setHealth).catch(() => null);
  }, []);

  // Pre-fill from URL param (navigated from Opportunities page)
  useEffect(() => {
    const txn = searchParams.get("txn");
    const q = searchParams.get("q");
    if (txn) setTransactionId(txn);
    if (q) setQuestion(q);
  }, [searchParams]);

  const handleInvestigate = useCallback(async () => {
    if (!transactionId.trim() || !question.trim()) return;
    setLoading(true);
    setError(null);
    setReport(null);

    // Update URL so the investigation is shareable
    setSearchParams({ txn: transactionId.trim() });

    try {
      const result = await assistantApi.investigate({
        transaction_id: transactionId.trim(),
        question: question.trim(),
      });
      setReport(result);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } }; message?: string })
          ?.response?.data?.detail ??
        (e as { message?: string })?.message ??
        "Investigation failed. Is the backend running?";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [transactionId, question, setSearchParams]);

  // Auto-submit if both params are in the URL
  useEffect(() => {
    const txn = searchParams.get("txn");
    const q = searchParams.get("q");
    if (txn && q && !report && !loading) {
      setTransactionId(txn);
      setQuestion(q);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto w-full">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-blue-500/20 border border-violet-500/20">
              <Bot className="h-5 w-5 text-violet-400" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">AI Investigation Agent</h1>
          </div>
          <p className="text-sm text-muted-foreground ml-14">
            Structured LLM investigation grounded exclusively in verified database records.
            The agent cannot invent data, modify balances, or execute recovery actions.
          </p>
        </div>
        <LLMStatusBadge health={health} />
      </div>

      {/* ── LLM degraded notice ─────────────────────────────────────────────── */}
      {health && health.status !== "ready" && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 flex items-start gap-3 text-sm">
          <Info className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-400 mb-0.5">Running in degraded mode</p>
            <p className="text-muted-foreground">{health.message}</p>
          </div>
        </div>
      )}

      {/* ── Investigation form ──────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card p-5 flex flex-col gap-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="sm:col-span-1">
            <label htmlFor="txn-id-input" className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wide">
              Transaction ID
            </label>
            <input
              id="txn-id-input"
              type="text"
              value={transactionId}
              onChange={(e) => setTransactionId(e.target.value)}
              placeholder="e.g. TXN10291"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
              onKeyDown={(e) => e.key === "Enter" && handleInvestigate()}
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="question-input" className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wide">
              Investigation Question
            </label>
            <input
              id="question-input"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about this transaction…"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
              onKeyDown={(e) => e.key === "Enter" && handleInvestigate()}
            />
          </div>
        </div>

        {/* Preset question chips */}
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
            Preset Questions
          </p>
          <div className="flex flex-wrap gap-2">
            {PRESET_QUESTIONS.map((q) => (
              <button
                key={q}
                id={`preset-${q.slice(0, 20).replace(/\s/g, "-").toLowerCase()}`}
                onClick={() => setQuestion(q)}
                className={`px-3 py-1.5 rounded-lg text-xs border transition-all ${
                  question === q
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground hover:border-border"
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        <button
          id="investigate-btn"
          onClick={handleInvestigate}
          disabled={loading || !transactionId.trim() || !question.trim()}
          className="self-end flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-violet-600 to-blue-600 text-white hover:from-violet-500 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-violet-500/20 hover:shadow-violet-500/30"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              Investigating…
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              Investigate
            </>
          )}
        </button>
      </div>

      {/* ── Loading skeleton ────────────────────────────────────────────────── */}
      {loading && (
        <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="relative">
              <div className="w-10 h-10 rounded-full border-2 border-violet-500/30 border-t-violet-500 animate-spin" />
              <Bot className="h-4 w-4 text-violet-400 absolute inset-0 m-auto" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Agent Investigating…</p>
              <p className="text-xs text-muted-foreground">Calling DB tools and synthesizing report</p>
            </div>
          </div>
          <div className="space-y-3">
            {["Fetching transaction data…", "Retrieving opportunity scoring…", "Checking customer history…", "Synthesizing grounded report…"].map((step, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-muted-foreground">
                <Cpu className="h-3.5 w-3.5 text-violet-400 animate-pulse" />
                <span style={{ animationDelay: `${i * 0.4}s` }}>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Error state ─────────────────────────────────────────────────────── */}
      {error && !loading && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 flex items-start gap-3 text-sm">
          <AlertTriangle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-400 mb-0.5">Investigation Failed</p>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      )}

      {/* ── Investigation Report ────────────────────────────────────────────── */}
      {report && !loading && (
        <div className="flex flex-col gap-4 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
          {/* Report header */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <div>
                <code className="text-xs font-mono text-muted-foreground">{report.transaction_id}</code>
                <p className="text-sm font-medium text-foreground">"{report.question}"</p>
              </div>
            </div>
            <StatusBadge report={report} />
          </div>

          {/* Not found */}
          {report.not_found ? (
            <NotFoundState transactionId={report.transaction_id} />
          ) : (
            <>
              {/* Decision band + probability */}
              <DecisionBandCard band={report.decision_band} probability={report.recovery_probability} />

              {/* Evidence */}
              <EvidencePanel evidence={report.evidence} />

              {/* Recommendation + Revenue Impact + Confidence */}
              <RecommendationPanel
                recommendation={report.recommendation}
                revenueImpact={report.revenue_impact}
                confidenceNote={report.confidence_note}
              />

              {/* Degraded mode error note */}
              {report.llm_unavailable && report.error_message && (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 flex items-start gap-3 text-xs">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-muted-foreground">{report.error_message}</p>
                </div>
              )}

              {/* Tool audit trail */}
              <ToolAuditTrail report={report} logs={report.tool_calls_log} />

              {/* Data integrity note */}
              <p className="text-xs text-muted-foreground text-center py-1">
                All financial figures cited above are sourced from immutable database records via read-only tool calls.
                This agent cannot modify balances, execute recovery actions, or bypass approval controls.
              </p>
            </>
          )}
        </div>
      )}

      {/* ── Empty state ─────────────────────────────────────────────────────── */}
      {!report && !loading && !error && (
        <div className="rounded-xl border border-dashed border-border p-10 text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-violet-500/10 to-blue-500/10 border border-violet-500/20">
              <Search className="h-8 w-8 text-violet-400" />
            </div>
          </div>
          <h3 className="font-semibold text-foreground mb-2">Start an Investigation</h3>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto mb-6">
            Enter a transaction ID (e.g. from the Opportunities page) and ask a question.
            The agent retrieves verified DB data and synthesizes a grounded report.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-left max-w-lg mx-auto">
            {[
              { icon: ShieldAlert, title: "Read-only", desc: "Cannot modify balances or execute recovery" },
              { icon: Database, title: "DB-grounded", desc: "All figures trace back to real records" },
              { icon: Activity, title: "Audit trail", desc: "Every tool call logged for compliance" },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-lg border border-border bg-card p-3 flex gap-2.5">
                <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">{title}</p>
                  <p className="text-muted-foreground mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
