"""
Generates SHAP-based explanations for a single prediction so the API
can answer "why this probability?" instead of showing a black-box number.
"""
import shap
import pandas as pd
import numpy as np

FRIENDLY_NAMES = {
    "student_score": "Academic score",
    "entrance_rank": "Entrance rank",
    "category": "Category",
    "state": "State",
    "branch": "Branch",
    "cutoff": "Previous cutoff",
    "year": "Year",
}


def explain_prediction(model, X_row: pd.DataFrame, background: pd.DataFrame | None = None):
    """
    X_row: single-row DataFrame of encoded features for the prediction being explained.
    background: a small sample of encoded training data used as the SHAP baseline.
    Returns a list of {feature, impact, direction} sorted by absolute impact.
    """
    if background is None or len(background) == 0:
        background = X_row  # fallback baseline

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_row)
        values = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]
    except Exception:
        # Fall back to a model-agnostic explainer for non-tree models (e.g. Logistic Regression)
        explainer = shap.Explainer(model.predict_proba, background)
        shap_values = explainer(X_row)
        values = shap_values.values[0][:, 1] if shap_values.values.ndim == 3 else shap_values.values[0]

    factors = []
    for col, val in zip(X_row.columns, values):
        factors.append({
            "feature": FRIENDLY_NAMES.get(col, col),
            "impact": round(float(val), 4),
            "direction": "positive" if val >= 0 else "negative",
        })

    factors.sort(key=lambda f: abs(f["impact"]), reverse=True)
    return factors


def build_explanation_text(factors: list, probability: float) -> str:
    top = factors[:3]
    parts = []
    for f in top:
        verb = "increases" if f["direction"] == "positive" else "reduces"
        parts.append(f"{f['feature']} {verb} your admission chance")
    joined = "; ".join(parts)
    return f"Estimated admission probability is {round(probability * 100, 1)}%. {joined}."
