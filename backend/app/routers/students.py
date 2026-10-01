from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/profile", tags=["Student Profile"])


@router.get("", response_model=schemas.ProfileOut)
def get_profile(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if not profile:
        profile = models.StudentProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("", response_model=schemas.ProfileOut)
def update_profile(
    payload: schemas.ProfileIn,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if not profile:
        profile = models.StudentProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
