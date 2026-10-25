import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
import models


# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is not set"
    )

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prophet API")


# Request models
class PredictionCreate(BaseModel):
    match_id: int
    predicted_home_score: int = Field(ge=0)
    predicted_away_score: int = Field(ge=0)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create a JWT access token
def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# Verify a JWT and extract the user ID
def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


# Identify the currently authenticated user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
):
    user_id = verify_access_token(credentials.credentials)

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


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


# Register a new user
@app.post("/register", status_code=201)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # Normalize email for consistent comparisons
    normalized_email = str(user.email).strip().lower()

    existing_user = db.query(models.User).filter(
        (models.User.username == user.username)
        | (models.User.email == normalized_email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    hashed_password = password_hash.hash(user.password)

    new_user = models.User(
        username=user.username,
        email=normalized_email,
        password_hash=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not register user"
        )


# Log in and return a JWT
@app.post("/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    normalized_email = str(user_data.email).strip().lower()

    user = db.query(models.User).filter(
        models.User.email == normalized_email
    ).first()

    if not user or not password_hash.verify(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }
