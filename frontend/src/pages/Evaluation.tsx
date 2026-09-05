import { useEffect, useState, useCallback } from "react";
import { CheckSquare, Play, AlertCircle, CheckCircle2, XCircle, BarChart3, TrendingUp } from "lucide-react";
import { evaluationApi, EvaluationReport } from "@/api/evaluation";

const formatINR = (v: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(v);

export function Evaluation() {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await evaluationApi.getResults();
      setReport(data);
    } catch (e: any) {
      if (e.response?.status === 404) {
        // Not run yet
        setReport(null);
      } else {
        setError("Failed to load evaluation results.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const handleRunEvaluation = async () => {
    setRunning(true);
    setError(null);
    try {
      await evaluationApi.runPipeline();
      await fetchResults();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to run evaluation pipeline.");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center text-muted-foreground">
        Loading evaluation data...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Model Evaluation</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Compare deterministic baseline against supervised ML models.
          </p>
        </div>
        <button
          onClick={handleRunEvaluation}
          disabled={running}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm bg-primary text-primary-foreground hover:opacity-90 transition-opacity font-medium disabled:opacity-50"
        >
          <Play className="h-4 w-4" />
          {running ? "Running Pipeline..." : "Run ML Pipeline"}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {!report ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-12 text-center flex flex-col items-center justify-center">
          <CheckSquare className="h-10 w-10 text-muted-foreground mb-4 opacity-50" />
          <h2 className="text-lg font-semibold text-foreground mb-1">No Evaluation Data</h2>
          <p className="text-sm text-muted-foreground mb-4 max-w-md">
            The ML pipeline has not been run yet. Click the button above to train models and evaluate against the Phase 5 deterministic baseline.
          </p>
          <button
            onClick={handleRunEvaluation}
            disabled={running}
            className="px-4 py-2 rounded-lg text-sm bg-primary text-primary-foreground hover:opacity-90 transition-opacity font-medium disabled:opacity-50"
          >
            {running ? "Running Pipeline..." : "Run Evaluation Pipeline"}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Justification Banner */}
          <div className={`rounded-xl border p-5 flex items-start gap-4 shadow-sm ${
            report.ml_justified 
              ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800" 
              : "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800"
          }`}>
            <div className="mt-0.5">
              {report.ml_justified ? (
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              ) : (
                <XCircle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              )}
            </div>
            <div>
              <h3 className={`text-lg font-semibold ${report.ml_justified ? "text-green-800 dark:text-green-300" : "text-yellow-800 dark:text-yellow-300"}`}>
                {report.ml_justified ? "ML Model Justified" : "ML Model Not Justified"}
              </h3>
              <p className={`text-sm mt-1 ${report.ml_justified ? "text-green-700 dark:text-green-400" : "text-yellow-700 dark:text-yellow-400"}`}>
                {report.justification_reason}
              </p>
              <div className="flex gap-4 mt-3">
                <span className="text-xs font-mono bg-white/50 dark:bg-black/20 px-2 py-1 rounded">
                  Selected Model: {report.selected_model}
                </span>
                <span className="text-xs font-mono bg-white/50 dark:bg-black/20 px-2 py-1 rounded">
                  Version: {report.model_version}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Statistical Metrics */}
            <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
              <div className="px-5 py-4 border-b border-border bg-muted/30 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                <h3 className="font-semibold">Classification Metrics</h3>
              </div>
              <div className="p-0 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/10">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Metric</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">Baseline</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">ML ({report.selected_model})</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">Diff</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { key: "pr_auc", label: "PR-AUC (Primary)" },
                      { key: "roc_auc", label: "ROC-AUC" },
                      { key: "precision", label: "Precision" },
                      { key: "recall", label: "Recall" },
                      { key: "f1", label: "F1 Score" },
                    ].map((m) => {
                      const base = (report.metrics.baseline.classification as any)[m.key];
                      const ml = (report.metrics.ml.classification as any)[m.key];
                      const diff = ml - base;
                      return (
                        <tr key={m.key} className="border-b border-border last:border-0 hover:bg-muted/30">
                          <td className="px-4 py-3 font-medium text-foreground">{m.label}</td>
                          <td className="px-4 py-3 text-right font-mono">{base.toFixed(4)}</td>
                          <td className="px-4 py-3 text-right font-mono font-semibold">{ml.toFixed(4)}</td>
                          <td className={`px-4 py-3 text-right font-mono ${diff > 0 ? "text-green-600 dark:text-green-400" : diff < 0 ? "text-red-600 dark:text-red-400" : "text-muted-foreground"}`}>
                            {diff > 0 ? "+" : ""}{diff.toFixed(4)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Business Metrics */}
            <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
              <div className="px-5 py-4 border-b border-border bg-muted/30 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                <h3 className="font-semibold">Business Impact</h3>
              </div>
              <div className="p-0 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/10">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Metric</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">Baseline</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">ML ({report.selected_model})</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { key: "expected_recoverable", label: "Expected Recovery", format: formatINR },
                      { key: "actual_recovered", label: "Actual Recovered (Sim)", format: formatINR },
                      { key: "recovery_rate", label: "Recovery Rate", format: (v: number) => `${(v * 100).toFixed(1)}%` },
                      { key: "false_recommendation_rate", label: "False Rec. Rate (Waste)", format: (v: number) => `${(v * 100).toFixed(1)}%` },
                    ].map((m) => {
                      const base = (report.metrics.baseline.business as any)[m.key];
                      const ml = (report.metrics.ml.business as any)[m.key];
                      return (
                        <tr key={m.key} className="border-b border-border last:border-0 hover:bg-muted/30">
                          <td className="px-4 py-3 font-medium text-foreground">{m.label}</td>
                          <td className="px-4 py-3 text-right font-mono">{m.format(base)}</td>
                          <td className="px-4 py-3 text-right font-mono font-semibold">{m.format(ml)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="p-4 bg-muted/10 border-t border-border mt-auto">
                <p className="text-xs text-muted-foreground text-center">
                  Total test set revenue at risk: <span className="font-semibold text-foreground">{formatINR(report.metrics.ml.business.revenue_at_risk)}</span>
                </p>
              </div>
            </div>
          </div>
          
          <div className="text-xs text-muted-foreground text-center">
            Dataset split — Train: {report.dataset_sizes.train} | Val: {report.dataset_sizes.val} | Test: {report.dataset_sizes.test}
          </div>
        </div>
      )}
    </div>
  );
}
