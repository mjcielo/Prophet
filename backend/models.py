
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Column,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id =Column(Integer, primary_key=True, index=True)
    username =Column(String(50), unique=True, nullable=False)
    email =Column(String(255), unique=True, nullable=False)
    password_hash =Column(String(255), nullable=False)
    created_at =Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="user")


class Match(Base):
    __tablename__ = "matches"

    id =Column(Integer, primary_key=True, index=True)
    home_team =Column(String(100), nullable=False)
    away_team =Column(String(100), nullable=False)
    kickoff =Column(DateTime, nullable=False)

    home_score =Column(Integer, nullable=True)
    away_score =Column(Integer, nullable=True)
    status =Column(String(20), default="scheduled", nullable=False)

    predictions = relationship("Prediction", back_populates="match")

    __table_args__ = (
        CheckConstraint("home_score IS NULL OR home_score >= 0"),
        CheckConstraint("away_score IS NULL OR away_score >= 0"),
        CheckConstraint("home_team != away_team"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id =Column(Integer, primary_key=True, index=True)
    user_id =Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id =Column(Integer, ForeignKey("matches.id"), nullable=False)
    predicted_home_score =Column(Integer, nullable=False)
    predicted_away_score =Column(Integer, nullable=False)
    created_at =Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")

    __table_args__ = (
        UniqueConstraint("user_id", "match_id", name="uq_user_match_prediction"),
        CheckConstraint("predicted_home_score >= 0"),
        CheckConstraint("predicted_away_score >= 0"),
    )
