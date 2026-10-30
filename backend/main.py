from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import Base, engine
import models
from auth import router as auth_router, get_db, get_current_user
from scoring import calculate_points


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prophet API")

# Connect registration and login routes from auth.py
app.include_router(auth_router)


# -----------------------------------------
# REQUEST MODELS
# -----------------------------------------

class PredictionCreate(BaseModel):
    match_id: int
    predicted_home_score: int = Field(ge=0)
    predicted_away_score: int = Field(ge=0)


class MatchResultUpdate(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


# -----------------------------------------
# HOME
# -----------------------------------------

@app.get("/")
def hello_world():
    return {"message": "Welcome to Prophet!"}


# -----------------------------------------
# LIST ALL MATCHES
# -----------------------------------------

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


# -----------------------------------------
# CREATE A PREDICTION
# -----------------------------------------

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

    # Predictions allowed only before kickoff
    if (
        match.status != "scheduled"
        or match.kickoff <= datetime.now()
    ):
        raise HTTPException(
            status_code=400,
            detail="Predictions are closed for this match"
        )

    # Prevent duplicate predictions
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


# -----------------------------------------
# ADMIN: UPDATE MATCH RESULT AND CALCULATE POINTS
# -----------------------------------------

@app.put("/matches/{match_id}/result")
def update_match_result(
    match_id: int,
    result: MatchResultUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Temporary development admin check
    if current_user.id != 1:
        raise HTTPException(
            status_code=403,
            detail="Only admin users can update match results"
        )

    match = db.query(models.Match).filter(
        models.Match.id == match_id
    ).first()

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found"
        )

    match.home_score = result.home_score
    match.away_score = result.away_score
    match.status = "completed"

    predictions = db.query(models.Prediction).filter(
        models.Prediction.match_id == match_id
    ).all()

    for prediction in predictions:
        prediction.points = calculate_points(
            prediction.predicted_home_score,
            prediction.predicted_away_score,
            match.home_score,
            match.away_score
        )

    try:
        db.commit()

        return {
            "message": "Match result updated and points calculated",
            "match_id": match.id,
            "final_score": {
                "home": match.home_score,
                "away": match.away_score
            },
            "predictions_updated": len(predictions),
            "results": [
                {
                    "user_id": prediction.user_id,
                    "predicted_score": (
                        f"{prediction.predicted_home_score}-"
                        f"{prediction.predicted_away_score}"
                    ),
                    "points": prediction.points
                }
                for prediction in predictions
            ]
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update match result and points"
        )


# -----------------------------------------
# USER: VIEW OWN PREDICTIONS AND POINTS
# -----------------------------------------

@app.get("/users/{user_id}/predictions")
def get_user_predictions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Users can only view their own predictions
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
            "actual_home_score": prediction.match.home_score,
            "actual_away_score": prediction.match.away_score,
            "match_status": prediction.match.status,
            "points": prediction.points
        }
        for prediction in predictions
    ]


# -----------------------------------------
# PUBLIC: LEADERBOARD
# -----------------------------------------

@app.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):

    leaderboard = db.query(
        models.User.id.label("user_id"),
        models.User.username.label("username"),
        func.coalesce(
            func.sum(models.Prediction.points), 0
        ).label("total_points")
    ).outerjoin(
        models.Prediction,
        models.User.id == models.Prediction.user_id
    ).group_by(
        models.User.id,
        models.User.username
    ).order_by(
        func.coalesce(
            func.sum(models.Prediction.points), 0
        ).desc(),
        models.User.id
    ).all()

    return [
        {
            "rank": index,
            "user_id": user.user_id,
            "username": user.username,
            "total_points": user.total_points
        }
        for index, user in enumerate(leaderboard, start=1)
    ]