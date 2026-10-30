
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine
import models
from auth import router as auth_router, get_db, get_current_user


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prophet API")

# Connect registration and login routes from auth.py
app.include_router(auth_router)


# Request model for creating a prediction
class PredictionCreate(BaseModel):
    match_id: int
    predicted_home_score: int = Field(ge=0)
    predicted_away_score: int = Field(ge=0)


# Home endpoint
@app.get("/")
def hello_world():
    return {"message": "Welcome to Prophet!"}


# List matches
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


# Create a prediction (requires a valid token)
@app.post("/predictions")
def create_prediction(
    prediction: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    match = db.query(models.Match).filter(
        models.Match.id == prediction.match_id
    ).first()

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found"
        )

    # Predictions are allowed only before kickoff
    if (
        match.status != "scheduled"
        or match.kickoff <= datetime.now()
    ):
        raise HTTPException(
            status_code=400,
            detail="Predictions are closed for this match"
        )

    # Prevent duplicate predictions by the same user
    existing = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id,
        models.Prediction.match_id == prediction.match_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already predicted this match"
        )

    new_prediction = models.Prediction(
        user_id=current_user.id,
        match_id=prediction.match_id,
        predicted_home_score=prediction.predicted_home_score,
        predicted_away_score=prediction.predicted_away_score
    )

    try:
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

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save prediction"
        )


# Get the logged-in user's predictions
@app.get("/users/{user_id}/predictions")
def get_user_predictions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Prevent users from viewing another user's predictions
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot view another user's predictions"
        )

    predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).all()

    return [
        {
            "prediction_id": prediction.id,
            "match_id": prediction.match.id,
            "home_team": prediction.match.home_team,
            "away_team": prediction.match.away_team,
            "predicted_home_score": prediction.predicted_home_score,
            "predicted_away_score": prediction.predicted_away_score,
            "match_status": prediction.match.status
        }
        for prediction in predictions
    ]
