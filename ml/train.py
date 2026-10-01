"""
Trains multiple models (Logistic Regression, Random Forest, XGBoost),
compares them on held-out validation data, and saves the best one.

Run: python ml/train.py ml/datasets/synthetic_admissions.csv
"""
import sys
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.preprocessing import build_feature_matrix

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "ml_artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)


def evaluate(model, X_val, y_val):
    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)[:, 1]
    return {
        "accuracy": round(accuracy_score(y_val, preds), 4),
        "precision": round(precision_score(y_val, preds, zero_division=0), 4),
        "recall": round(recall_score(y_val, preds, zero_division=0), 4),
        "f1": round(f1_score(y_val, preds, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_val, probs), 4),
    }


def train(dataset_path: str):
    df = pd.read_csv(dataset_path)
    X, y, encoders = build_feature_matrix(df)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1000),
        "random_forest": RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42),
        "xgboost": XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            eval_metric="logloss", random_state=42
        ),
    }

    results = {}
    fitted_models = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        metrics = evaluate(model, X_val, y_val)
        results[name] = metrics
        fitted_models[name] = model
        print(f"{name}: {metrics}")

    # Select best model by ROC-AUC (a reasonable default for imbalanced admit/reject data)
    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    best_model = fitted_models[best_name]
    print(f"\nSelected model: {best_name} (ROC-AUC={results[best_name]['roc_auc']})")

    joblib.dump(best_model, os.path.join(ARTIFACT_DIR, "model.joblib"))
    joblib.dump(encoders, os.path.join(ARTIFACT_DIR, "encoders.joblib"))
    joblib.dump({"name": best_name, "metrics": results[best_name], "all_results": results},
                os.path.join(ARTIFACT_DIR, "model_meta.joblib"))

    return best_name, results


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "synthetic_admissions.csv")
    train(path)
