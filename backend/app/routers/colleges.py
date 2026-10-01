from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/colleges", tags=["Colleges"])


@router.get("", response_model=list[schemas.CollegeOut])
def list_colleges(
    state: Optional[str] = None,
    branch: Optional[str] = None,
    ownership: Optional[str] = None,
    max_fees: Optional[float] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.College)
    if state:
        q = q.filter(models.College.state == state)
    if branch:
        q = q.filter(models.College.branch == branch)
    if ownership:
        q = q.filter(models.College.ownership == ownership)
    if max_fees:
        q = q.filter(models.College.fees <= max_fees)
    return q.all()


def _latest_cutoff(db: Session, college_id: int, category: str = "General"):
    record = (
        db.query(models.CutoffRecord)
        .filter(models.CutoffRecord.college_id == college_id)
        .order_by(models.CutoffRecord.year.desc())
        .first()
    )
    return record.closing_rank if record else None


def match_colleges(db: Session, rank: int, category: str = "General",
                   state: Optional[str] = None, branch: Optional[str] = None,
                   ownership: Optional[str] = None):
    """Heuristic matcher shared by the predictor endpoint, chatbot and PDF report."""
    q = db.query(models.College)
    if state:
        q = q.filter(models.College.state == state)
    if branch:
        q = q.filter(models.College.branch == branch)
    if ownership:
        q = q.filter(models.College.ownership == ownership)

    matches = []
    for college in q.all():
        cutoff = _latest_cutoff(db, college.id, category)
        if not cutoff:
            continue
        ratio = rank / cutoff
        chance = round(max(0.02, min(0.97, 1 - (ratio - 0.5))), 2)
        if ratio <= 0.75:
            bucket = "Safe"
        elif ratio <= 1.05:
            bucket = "Target"
        else:
            bucket = "Reach"
        matches.append(schemas.CollegeMatch(
            college_id=college.id, name=college.name, branch=college.branch,
            estimated_chance=chance, previous_cutoff=cutoff, category_bucket=bucket,
        ))
    matches.sort(key=lambda m: m.estimated_chance, reverse=True)
    return matches


@router.get("/predictor", response_model=list[schemas.CollegeMatch])
def college_predictor(
    rank: int = Query(..., description="Student's entrance rank"),
    category: str = "General",
    state: Optional[str] = None,
    branch: Optional[str] = None,
    ownership: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return match_colleges(db, rank, category, state, branch, ownership)


@router.get("/compare")
def compare_colleges(ids: str = Query(..., description="Comma separated college ids, max 4"),
                     db: Session = Depends(get_db)):
    try:
        id_list = [int(i) for i in ids.split(",") if i.strip()][:4]
    except ValueError:
        raise HTTPException(status_code=400, detail="ids must be comma separated integers")
    out = []
    for cid in id_list:
        college = db.query(models.College).filter(models.College.id == cid).first()
        if not college:
            continue
        records = (db.query(models.CutoffRecord)
                   .filter(models.CutoffRecord.college_id == cid)
                   .order_by(models.CutoffRecord.year.asc()).all())
        out.append({
            "id": college.id, "name": college.name, "branch": college.branch,
            "state": college.state, "city": college.city, "ownership": college.ownership,
            "fees": college.fees, "exam": college.exam,
            "latest_cutoff": records[-1].closing_rank if records else None,
            "trend": [{"year": r.year, "closing_rank": r.closing_rank} for r in records],
        })
    return out


@router.get("/{college_id}/cutoff-trend")
def cutoff_trend(college_id: int, category: str = "General", db: Session = Depends(get_db)):
    records = (
        db.query(models.CutoffRecord)
        .filter(models.CutoffRecord.college_id == college_id, models.CutoffRecord.category == category)
        .order_by(models.CutoffRecord.year.asc())
        .all()
    )
    return [{"year": r.year, "closing_rank": r.closing_rank} for r in records]
