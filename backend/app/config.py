import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./admission_ai.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
MODEL_PATH = os.getenv("MODEL_PATH", "./ml_artifacts/model.joblib")
ENCODER_PATH = os.getenv("ENCODER_PATH", "./ml_artifacts/encoders.joblib")
