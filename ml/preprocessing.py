import pandas as pd
from sklearn.preprocessing import LabelEncoder

FEATURE_COLUMNS = ["student_score", "entrance_rank", "category", "state", "branch", "cutoff", "year"]
CATEGORICAL_COLUMNS = ["category", "state", "branch"]
TARGET_COLUMN = "admitted"

REQUIRED_COLUMNS = FEATURE_COLUMNS + [TARGET_COLUMN, "college"]


def validate_dataset(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    if df[TARGET_COLUMN].nunique() < 2:
        raise ValueError("Target column 'admitted' must contain both 0 and 1 values")
    return True


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    df = df[(df["entrance_rank"] > 0) & (df["cutoff"] > 0)]
    df["student_score"] = df["student_score"].clip(0, 100)
    return df.reset_index(drop=True)


def encode_features(df: pd.DataFrame, encoders: dict | None = None):
    """
    Encodes categorical columns with LabelEncoder.
    If `encoders` is passed (from a saved model), reuse them for inference.
    Otherwise fit new encoders (training time) and return them.
    """
    df = df.copy()
    fitted = encoders is None
    if fitted:
        encoders = {}

    for col in CATEGORICAL_COLUMNS:
        if fitted:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
        else:
            le = encoders[col]
            # unseen categories at inference time -> map to a fallback class
            df[col] = df[col].astype(str).map(
                lambda v: v if v in le.classes_ else le.classes_[0]
            )
            df[col] = le.transform(df[col])

    return df, encoders


def build_feature_matrix(df: pd.DataFrame, encoders: dict | None = None):
    validate_dataset(df) if encoders is None else None
    df = clean_dataset(df)
    df_encoded, encoders = encode_features(df, encoders)
    X = df_encoded[FEATURE_COLUMNS]
    y = df_encoded[TARGET_COLUMN] if TARGET_COLUMN in df_encoded.columns else None
    return X, y, encoders
