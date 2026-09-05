from typing import Dict, Any, Optional
from pydantic import BaseModel

class ClassificationMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    pr_auc: float
    roc_auc: float
    confusion_matrix: Dict[str, int]

class BusinessMetrics(BaseModel):
    revenue_at_risk: float
    expected_recoverable: float
    actual_recovered: float
    recovery_rate: float
    false_recommendation_rate: float

class EvaluationMetrics(BaseModel):
    classification: ClassificationMetrics
    business: BusinessMetrics

class DatasetSizes(BaseModel):
    train: int
    val: int
    test: int

class ModelComparisonMetrics(BaseModel):
    baseline: EvaluationMetrics
    ml: EvaluationMetrics

class EvaluationReport(BaseModel):
    ml_justified: bool
    justification_reason: str
    selected_model: str
    model_version: str
    dataset_sizes: DatasetSizes
    metrics: ModelComparisonMetrics
