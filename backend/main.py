from fastapi import FastAPI, Depends, HTTPException
from database import Base, engine, SessionLocal
import models
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")

app = FastAPI(title="Prophet API")

class PredictionCreate(BaseModel):
    user_id: int
    match_id: int
    predicted_home_score: int = Field(ge=0)
    predicted_away_score: int = Field(ge=0)


@app.get("/")
def hello_world():
    return {"message": "Welcome to Prophet!"}



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/matches")
def get_matches(db: Session = Depends(get_db)):
    matches = db.query(models.Match).order_by(
        models.Match.kickoff
    ).all()

    return [
        {
            "id": match.id,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "kickoff": match.kickoff.isoformat(),
            "home_score": match.home_score,
            "away_score": match.away_score,
            "status": match.status
        }
        for match in matches
    ]



@app.post("/predictions")
def create_prediction(
    prediction: PredictionCreate,
    db: Session = Depends(get_db)
):
    # Check whether the user exists
    user = db.query(models.User).filter(
        models.User.id == prediction.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check whether the match exists
    match = db.query(models.Match).filter(
        models.Match.id == prediction.match_id
    ).first()

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found"
        )

    # Predictions are allowed only before kickoff
    if match.status != "scheduled" or match.kickoff <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Predictions are closed for this match"
        )

    # Prevent duplicate predictions
    existing = db.query(models.Prediction).filter(
        models.Prediction.user_id == prediction.user_id,
        models.Prediction.match_id == prediction.match_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already predicted this match"
        )

    new_prediction = models.Prediction(
        user_id=prediction.user_id,
        match_id=prediction.match_id,
        predicted_home_score=prediction.predicted_home_score,
        predicted_away_score=prediction.predicted_away_score
    )

    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)

    return {
        "message": "Prediction saved successfully",
        "prediction_id": new_prediction.id,
        "user_id": new_prediction.user_id,
        "match_id": new_prediction.match_id,
        "predicted_home_score": new_prediction.predicted_home_score,
        "predicted_away_score": new_prediction.predicted_away_score
    }
