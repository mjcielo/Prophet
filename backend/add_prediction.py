from datetime import datetime
from database import SessionLocal
from models import Match, User, Prediction

db = SessionLocal()

try:
    # user
    user = db.query(User).filter(User.username == "akash_pro").first()

    # match
    match = db.query(Match).first()

    if not user:
        print("User not found!")

    elif not match:
        print("Match not found!")

    else:
        prediction = Prediction(
            user_id=user.id,
            match_id=match.id,
            predicted_home_score=2,
            predicted_away_score=1,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        print("Prediction added successfully!")
        print("Prediction ID:", prediction.id)
        print(f"Prediction: {user.username} predicted {match.home_team} {prediction.predicted_home_score} - {prediction.predicted_away_score} {match.away_team}")

except Exception as e:
    db.rollback()
    print("Something went wrong:", e)

finally:
    db.close()