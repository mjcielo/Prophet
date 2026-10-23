
from database import SessionLocal
from models import Prediction

db = SessionLocal()

try:
    predictions = db.query(Prediction).all()

    if predictions:
        print("ALL MATCH PREDICTIONS")
        print("-" * 40)

        for prediction in predictions:
            print("Username:", prediction.user.username)
            print(
                "Match:",
                prediction.match.home_team,
                "vs",
                prediction.match.away_team
            )
            print(
                "Predicted Score:",
                prediction.predicted_home_score,
                "-",
                prediction.predicted_away_score
            )
            print("-" * 40)

    else:
        print("No predictions found.")

finally:
    db.close()
