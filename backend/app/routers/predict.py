import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, ml_loader

router = APIRouter(prefix="/predict", tags=["Prediction"])


@router.post("", response_model=schemas.PredictionOut)
def predict_admission(
    payload: schemas.PredictionRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if not ml_loader.is_model_loaded():
        raise HTTPException(
            status_code=503,
            detail="Prediction model is not trained yet. Ask an admin to train the model first.",
        )

    college = None
    cutoff = 40000
    branch = "CSE"
    state = "UP"
    if payload.college_id:
        college = db.query(models.College).filter(models.College.id == payload.college_id).first()
        if not college:
            raise HTTPException(status_code=404, detail="College not found")
        branch = college.branch
        state = college.state
        latest_cutoff = (
            db.query(models.CutoffRecord)
            .filter(models.CutoffRecord.college_id == college.id)
            .order_by(models.CutoffRecord.year.desc())
            .first()
        )
        if latest_cutoff:
            cutoff = latest_cutoff.closing_rank

    academic_score = (payload.tenth_pct or 75) * 0.4 + (payload.twelfth_pct or 75) * 0.6

    result = ml_loader.predict_with_explanation(
        student_score=academic_score,
        entrance_rank=payload.entrance_rank,
        category=payload.category,
        state=state,
        branch=branch,
        cutoff=cutoff,
    )

    history = models.PredictionHistory(
        user_id=current_user.id,
        college_id=payload.college_id,
        input_snapshot=json.dumps(payload.model_dump()),
        probability=result["probability"],
        label=result["label"],
        explanation=json.dumps(result["factors"]),
    )
    db.add(history)
    db.commit()

    return schemas.PredictionOut(**result)


@router.get("/history")
def prediction_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(models.PredictionHistory)
        .filter(models.PredictionHistory.user_id == current_user.id)
        .order_by(models.PredictionHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "probability": r.probability,
            "label": r.label,
            "created_at": r.created_at,
            "college_id": r.college_id,
        }
        for r in records
    ]
