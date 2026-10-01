from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Student Profile ----------
class ProfileIn(BaseModel):
    category: str = "General"
    state: Optional[str] = None
    tenth_pct: Optional[float] = None
    twelfth_pct: Optional[float] = None
    diploma_pct: Optional[float] = None
    entrance_exam: Optional[str] = None
    entrance_rank: Optional[int] = None
    preferred_branch: Optional[str] = None
    preferred_state: Optional[str] = None
    budget_max: Optional[float] = None


class ProfileOut(ProfileIn):
    id: int

    class Config:
        from_attributes = True


# ---------- College ----------
class CollegeIn(BaseModel):
    name: str
    branch: str
    state: str
    city: Optional[str] = None
    ownership: str = "Government"
    fees: float = 0
    exam: str = "General"


class CollegeOut(CollegeIn):
    id: int

    class Config:
        from_attributes = True


class CutoffIn(BaseModel):
    college_id: int
    year: int
    category: str = "General"
    closing_rank: int


# ---------- Prediction ----------
class PredictionRequest(BaseModel):
    entrance_rank: int
    category: str = "General"
    tenth_pct: Optional[float] = 75
    twelfth_pct: Optional[float] = 75
    college_id: Optional[int] = None  # if predicting for a specific college


class PredictionFactor(BaseModel):
    feature: str
    impact: float
    direction: str  # "positive" or "negative"


class PredictionOut(BaseModel):
    probability: float
    label: str
    factors: List[PredictionFactor]
    explanation_text: str


class CollegeMatch(BaseModel):
    college_id: int
    name: str
    branch: str
    estimated_chance: float
    previous_cutoff: int
    category_bucket: str  # "Safe" / "Target" / "Reach"
