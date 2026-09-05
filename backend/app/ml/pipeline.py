"""
RevTrace Phase 6 — ML Recovery Prediction Pipeline.
Uses scikit-learn to train Logistic Regression and Random Forest models.
Compares against the Phase 5 deterministic baseline.
Saves evaluation metrics to a JSON artifact for the frontend.
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    roc_auc_score, average_precision_score, confusion_matrix
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "revtrace.db"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


def load_data() -> pd.DataFrame:
    """Load data from SQLite: join transactions and recovery_opportunities."""
    query = """
        SELECT 
            t.transaction_id,
            t.amount,
            t.payment_method,
            t.failure_reason,
            t.retry_count,
            t.previous_payment_history,
            t.recurring_payment,
            t.timestamp,
            t.ground_truth_recoverable,
            t.ground_truth_recovered_amount,
            o.revenue_at_risk,
            o.recovery_probability AS baseline_probability
        FROM transactions t
        JOIN recovery_opportunities o ON t.transaction_id = o.transaction_id
        WHERE t.payment_status = 'failed'
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn)
        
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Sort chronologically for temporal split
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def calculate_business_metrics(df: pd.DataFrame, prob_col: str, threshold: float = 0.5) -> dict:
    """Calculate business metrics for a given probability column."""
    # Predictions
    preds = (df[prob_col] > threshold).astype(int)
    
    # Revenue at risk
    total_at_risk = df['revenue_at_risk'].sum()
    
    # Expected Recoverable
    # Expected recovery for recommended actions (pred == 1)
    expected_recoverable = (df['revenue_at_risk'] * df[prob_col]).sum()
    
    # Actual Recovered (for those we recommended to recover)
    # We simulate this by taking ground_truth_recovered_amount where pred == 1
    actual_recovered = df.loc[preds == 1, 'ground_truth_recovered_amount'].sum()
    
    # Recovery Rate (Actual / Expected) - handling div by 0
    recovery_rate = actual_recovered / expected_recoverable if expected_recoverable > 0 else 0.0
    
    # False Recommendation Rate: % of recommendations where ground truth was not recoverable
    recommended = preds.sum()
    false_recommendations = ((preds == 1) & (df['ground_truth_recoverable'] == 0)).sum()
    false_rec_rate = false_recommendations / recommended if recommended > 0 else 0.0
    
    return {
        "revenue_at_risk": round(total_at_risk, 2),
        "expected_recoverable": round(expected_recoverable, 2),
        "actual_recovered": round(actual_recovered, 2),
        "recovery_rate": round(recovery_rate, 4),
        "false_recommendation_rate": round(false_rec_rate, 4)
    }


def evaluate_model(y_true, y_prob, y_pred, df_test, prob_col) -> dict:
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    b_metrics = calculate_business_metrics(df_test, prob_col)
    
    return {
        "classification": {
            "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
            "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
            "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
            "pr_auc": round(average_precision_score(y_true, y_prob), 4),
            "roc_auc": round(roc_auc_score(y_true, y_prob), 4),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
        },
        "business": b_metrics
    }


def main():
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} failed transactions.")
    
    # Features and Target
    numeric_features = ['amount', 'retry_count']
    categorical_features = ['payment_method', 'failure_reason', 'previous_payment_history']
    boolean_features = ['recurring_payment']
    
    X = df[numeric_features + categorical_features + boolean_features]
    y = df['ground_truth_recoverable'].astype(int)
    
    # Temporal Split: 70% Train, 15% Val, 15% Test
    n = len(df)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)
    
    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]
    df_test = df.iloc[val_end:].copy()
    
    print(f"Split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('bool', 'passthrough', boolean_features)
        ])
    
    # ── Models ──
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    }
    
    results = {}
    best_model_name = None
    best_val_auc = -1
    best_pipeline = None
    
    for name, model in models.items():
        print(f"Training {name}...")
        pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])
        pipeline.fit(X_train, y_train)
        
        # Validation
        val_probs = pipeline.predict_proba(X_val)[:, 1]
        val_auc = roc_auc_score(y_val, val_probs)
        print(f"{name} Val ROC-AUC: {val_auc:.4f}")
        
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_model_name = name
            best_pipeline = pipeline
            
    print(f"Selected Model: {best_model_name} (Val ROC-AUC: {best_val_auc:.4f})")
    
    # ── Evaluation on Test Set ──
    
    # 1. Baseline Evaluation
    # Note: deterministic baseline probability was calculated in Phase 5
    baseline_probs = df_test['baseline_probability']
    baseline_preds = (baseline_probs > 0.5).astype(int)
    
    baseline_results = evaluate_model(y_test, baseline_probs, baseline_preds, df_test, 'baseline_probability')
    
    # 2. ML Evaluation
    ml_probs = best_pipeline.predict_proba(X_test)[:, 1]
    ml_preds = best_pipeline.predict(X_test)
    df_test['ml_probability'] = ml_probs
    
    ml_results = evaluate_model(y_test, ml_probs, ml_preds, df_test, 'ml_probability')
    
    # Justification logic: We select ML if it materially improves PR-AUC by > 0.05
    ml_pr_auc = ml_results['classification']['pr_auc']
    base_pr_auc = baseline_results['classification']['pr_auc']
    improvement = ml_pr_auc - base_pr_auc
    
    ml_justified = bool(improvement > 0.05)
    
    if ml_justified:
        justification_reason = f"ML ({best_model_name}) materially improved PR-AUC by {improvement:.4f} over baseline."
    else:
        justification_reason = f"ML ({best_model_name}) did not materially improve PR-AUC (improvement: {improvement:.4f}). Falling back to deterministic."
    
    # Save results
    report = {
        "ml_justified": ml_justified,
        "justification_reason": justification_reason,
        "selected_model": best_model_name,
        "model_version": "1.0.0-ml",
        "dataset_sizes": {
            "train": len(X_train),
            "val": len(X_val),
            "test": len(X_test)
        },
        "metrics": {
            "baseline": baseline_results,
            "ml": ml_results
        }
    }
    
    with open(ARTIFACTS_DIR / "evaluation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    joblib.dump(best_pipeline, ARTIFACTS_DIR / "model.pkl")
    print("Evaluation complete. Artifacts saved.")


if __name__ == "__main__":
    main()
