"""
Loads the trained model + encoders once at startup and exposes a
predict_with_explanation() helper used by the /predict endpoint.
"""
import os
import glob
import joblib
import pandas as pd
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ml.preprocessing import FEATURE_COLUMNS, CATEGORICAL_COLUMNS, build_feature_matrix
from ml.explain import explain_prediction, build_explanation_text

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml_artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "model.joblib")
ENCODERS_PATH = os.path.join(ARTIFACT_DIR, "encoders.joblib")
META_PATH = os.path.join(ARTIFACT_DIR, "model_meta.joblib")
DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "datasets")

_model = None
_encoders = None
_meta = None
_background = None  # sample of encoded training rows, used as SHAP baseline


def is_model_loaded() -> bool:
    return _model is not None


def _load_background_sample():
    """Loads a small random sample of encoded training data to act as the
    SHAP baseline, so factor impacts reflect real feature variance instead
    of comparing a row against itself."""
    global _background
    candidates = [os.path.join(DATASET_DIR, "latest_upload.csv"),
                  os.path.join(DATASET_DIR, "synthetic_admissions.csv")]
    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                sample = df.sample(min(100, len(df)), random_state=42)
                X, _, _ = build_feature_matrix(sample, encoders=_encoders)
                _background = X
                return
            except Exception:
                continue
    _background = None


def load_model():
    global _model, _encoders, _meta
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODERS_PATH):
        _model = joblib.load(MODEL_PATH)
        _encoders = joblib.load(ENCODERS_PATH)
        _meta = joblib.load(META_PATH) if os.path.exists(META_PATH) else None
        _load_background_sample()
    return _model


def get_model_meta():
    return _meta


def predict_with_explanation(student_score: float, entrance_rank: int, category: str,
                              state: str, branch: str, cutoff: int, year: int = 2026):
    if _model is None:
        raise RuntimeError("Model not trained yet. Run ml/train.py or use the admin 'Train Model' action.")

    raw = pd.DataFrame([{
        "student_score": student_score,
        "entrance_rank": entrance_rank,
        "category": category,
        "state": state,
        "branch": branch,
        "cutoff": cutoff,
        "year": year,
    }])

    encoded = raw.copy()
    for col in CATEGORICAL_COLUMNS:
        le = _encoders[col]
        val = str(encoded.at[0, col])
        if val not in le.classes_:
            val = le.classes_[0]
        encoded[col] = le.transform([val])

    X_row = encoded[FEATURE_COLUMNS]
    probability = float(_model.predict_proba(X_row)[0][1])

    factors = explain_prediction(_model, X_row, background=_background)
    explanation_text = build_explanation_text(factors, probability)

    if probability >= 0.7:
        label = "High Chance"
    elif probability >= 0.4:
        label = "Moderate Chance"
    else:
        label = "Low Chance"

    return {
        "probability": round(probability, 4),
        "label": label,
        "factors": factors,
        "explanation_text": explanation_text,
    }
