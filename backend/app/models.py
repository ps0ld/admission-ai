from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")  # "student" or "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    predictions = relationship("PredictionHistory", back_populates="user")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    category = Column(String, default="General")
    state = Column(String, nullable=True)
    tenth_pct = Column(Float, nullable=True)
    twelfth_pct = Column(Float, nullable=True)
    diploma_pct = Column(Float, nullable=True)
    entrance_exam = Column(String, nullable=True)
    entrance_rank = Column(Integer, nullable=True)
    preferred_branch = Column(String, nullable=True)
    preferred_state = Column(String, nullable=True)
    budget_max = Column(Float, nullable=True)

    user = relationship("User", back_populates="profile")


class College(Base):
    __tablename__ = "colleges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    state = Column(String, nullable=False)
    city = Column(String, nullable=True)
    ownership = Column(String, default="Government")  # Government / Private
    fees = Column(Float, default=0)
    exam = Column(String, default="General")

    cutoffs = relationship("CutoffRecord", back_populates="college")


class CutoffRecord(Base):
    __tablename__ = "cutoff_records"
    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    year = Column(Integer, nullable=False)
    category = Column(String, default="General")
    closing_rank = Column(Integer, nullable=False)

    college = relationship("College", back_populates="cutoffs")


class PredictionHistory(Base):
    __tablename__ = "prediction_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True)
    input_snapshot = Column(Text)  # JSON string of inputs used
    probability = Column(Float)
    label = Column(String)
    explanation = Column(Text)  # JSON string of SHAP factors
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="predictions")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)
    algorithm = Column(String, nullable=False)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    roc_auc = Column(Float)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime(timezone=True), server_default=func.now())


class SavedCollege(Base):
    __tablename__ = "saved_colleges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    college = relationship("College")
