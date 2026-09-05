import { api } from "@/api/client";

export interface ConfusionMatrix {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
}

export interface ClassificationMetrics {
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  roc_auc: number;
  confusion_matrix: ConfusionMatrix;
}

export interface BusinessMetrics {
  revenue_at_risk: number;
  expected_recoverable: number;
  actual_recovered: number;
  recovery_rate: number;
  false_recommendation_rate: number;
}

export interface EvaluationMetrics {
  classification: ClassificationMetrics;
  business: BusinessMetrics;
}

export interface DatasetSizes {
  train: number;
  val: number;
  test: number;
}

export interface EvaluationReport {
  ml_justified: boolean;
  justification_reason: string;
  selected_model: string;
  model_version: string;
  dataset_sizes: DatasetSizes;
  metrics: {
    baseline: EvaluationMetrics;
    ml: EvaluationMetrics;
  };
}

export const evaluationApi = {
  getResults: (): Promise<EvaluationReport> =>
    api.get<EvaluationReport>("/api/evaluation/results"),

  runPipeline: (): Promise<{ status: string; message: string; output: string }> =>
    api.post("/api/evaluation/run", null),
};
