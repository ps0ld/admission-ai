from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth

router = APIRouter(prefix="/saved", tags=["Saved Colleges"])


def _serialize(db: Session, saved: models.SavedCollege):
    c = saved.college
    latest = (db.query(models.CutoffRecord)
              .filter(models.CutoffRecord.college_id == c.id)
              .order_by(models.CutoffRecord.year.desc()).first())
    return {
        "college_id": c.id, "name": c.name, "branch": c.branch, "state": c.state,
        "city": c.city, "ownership": c.ownership, "fees": c.fees,
        "latest_cutoff": latest.closing_rank if latest else None,
    }


@router.get("")
def list_saved(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    rows = (db.query(models.SavedCollege)
            .filter(models.SavedCollege.user_id == user.id)
            .order_by(models.SavedCollege.created_at.desc()).all())
    return [_serialize(db, r) for r in rows]


@router.post("/{college_id}")
def save_college(college_id: int, user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(get_db)):
    if not db.query(models.College).filter(models.College.id == college_id).first():
        raise HTTPException(status_code=404, detail="College not found")
    existing = db.query(models.SavedCollege).filter(
        models.SavedCollege.user_id == user.id, models.SavedCollege.college_id == college_id).first()
    if not existing:
        db.add(models.SavedCollege(user_id=user.id, college_id=college_id))
        db.commit()
    return {"saved": True}


@router.delete("/{college_id}")
def unsave_college(college_id: int, user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(get_db)):
    db.query(models.SavedCollege).filter(
        models.SavedCollege.user_id == user.id, models.SavedCollege.college_id == college_id).delete()
    db.commit()
    return {"saved": False}
