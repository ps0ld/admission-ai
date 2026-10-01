from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models, ml_loader
from app.routers import auth_router, students, predict, colleges, admin, saved, report, chatbot

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Admission AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(students.router)
app.include_router(predict.router)
app.include_router(colleges.router)
app.include_router(admin.router)
app.include_router(saved.router)
app.include_router(report.router)
app.include_router(chatbot.router)


def _bootstrap():
    """Seeds demo data and trains a first model if missing (needed on hosts with
    ephemeral disks like Render free tier). Failures are logged, never fatal."""
    import os, sys, subprocess
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from app.database import SessionLocal
        from app import auth
        db = SessionLocal()
        if db.query(models.College).count() == 0:
            subprocess.run([sys.executable, "seed.py"], cwd=os.path.join(root, "backend"), check=False)
        db.close()
    except Exception as e:
        print("Seed bootstrap failed:", e)

    if not ml_loader.is_model_loaded():
        try:
            data = os.path.join(root, "ml", "datasets", "synthetic_admissions.csv")
            if not os.path.exists(data) and not os.path.exists(os.path.join(root, "ml", "datasets", "latest_upload.csv")):
                subprocess.run([sys.executable, os.path.join(root, "ml", "generate_synthetic_data.py")], check=True)
            subprocess.run([sys.executable, os.path.join(root, "ml", "train.py")], cwd=root, check=True)
            ml_loader.load_model()
        except Exception as e:
            print("Model bootstrap failed:", e)


@app.on_event("startup")
def startup_event():
    ml_loader.load_model()
    _bootstrap()


@app.get("/")
def root():
    return {
        "service": "Admission AI",
        "status": "running",
        "model_loaded": ml_loader.is_model_loaded(),
    }


@app.get("/health")
def health():
    return {"status": "ok"}
