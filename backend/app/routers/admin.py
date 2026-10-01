import os
import io
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, ml_loader

router = APIRouter(prefix="/admin", tags=["Admin"])

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATASET_DIR = os.path.join(ROOT_DIR, "ml", "datasets")


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    return {
        "total_users": db.query(models.User).filter(models.User.role == "student").count(),
        "total_predictions": db.query(models.PredictionHistory).count(),
        "total_colleges": db.query(models.College).count(),
        "active_model": db.query(models.ModelVersion).filter(models.ModelVersion.is_active == True).first(),
    }


# ---------- College CRUD ----------
@router.post("/colleges", response_model=schemas.CollegeOut)
def add_college(payload: schemas.CollegeIn, db: Session = Depends(get_db), _admin=Depends(auth.require_admin)):
    college = models.College(**payload.model_dump())
    db.add(college)
    db.commit()
    db.refresh(college)
    return college


@router.put("/colleges/{college_id}", response_model=schemas.CollegeOut)
def edit_college(college_id: int, payload: schemas.CollegeIn, db: Session = Depends(get_db), _admin=Depends(auth.require_admin)):
    college = db.query(models.College).filter(models.College.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    for field, value in payload.model_dump().items():
        setattr(college, field, value)
    db.commit()
    db.refresh(college)
    return college


@router.delete("/colleges/{college_id}")
def delete_college(college_id: int, db: Session = Depends(get_db), _admin=Depends(auth.require_admin)):
    college = db.query(models.College).filter(models.College.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    db.delete(college)
    db.commit()
    return {"deleted": True}


@router.post("/cutoffs")
def add_cutoff(payload: schemas.CutoffIn, db: Session = Depends(get_db), _admin=Depends(auth.require_admin)):
    record = models.CutoffRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------- Dataset upload + training ----------
@router.post("/dataset/upload")
async def upload_dataset(file: UploadFile = File(...), _admin=Depends(auth.require_admin)):
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ml.preprocessing import validate_dataset, clean_dataset

    try:
        validate_dataset(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    df = clean_dataset(df)
    os.makedirs(DATASET_DIR, exist_ok=True)
    save_path = os.path.join(DATASET_DIR, "latest_upload.csv")
    df.to_csv(save_path, index=False)

    return {"message": "Dataset uploaded and validated", "rows": len(df), "path": save_path}


@router.post("/model/train")
def train_model(db: Session = Depends(get_db), _admin=Depends(auth.require_admin)):
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ml.train import train as run_training

    dataset_path = os.path.join(DATASET_DIR, "latest_upload.csv")
    if not os.path.exists(dataset_path):
        dataset_path = os.path.join(DATASET_DIR, "synthetic_admissions.csv")
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=400, detail="No dataset available. Upload one first or generate synthetic data.")

    try:
        best_name, results = run_training(dataset_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    # Deactivate old versions, save new one as active
    db.query(models.ModelVersion).update({"is_active": False})
    metrics = results[best_name]
    version = models.ModelVersion(
        version=f"v{db.query(models.ModelVersion).count() + 1}",
        algorithm=best_name,
        accuracy=metrics["accuracy"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1=metrics["f1"],
        roc_auc=metrics["roc_auc"],
        is_active=True,
    )
    db.add(version)
    db.commit()

    ml_loader.load_model()  # hot-reload the newly trained model

    return {"selected_model": best_name, "all_results": results}


@router.get("/model/status")
def model_status(db: Session = Depends(get_db), _admin=Depends(auth.require_admin)):
    active = db.query(models.ModelVersion).filter(models.ModelVersion.is_active == True).first()
    return {
        "loaded": ml_loader.is_model_loaded(),
        "active_version": active,
    }
