
from database import SessionLocal
from models import Prediction
from scoring import calculate_points

db = SessionLocal()

try:
    # Find a saved prediction
    prediction = (
        db.query(Prediction)
        .filter(Prediction.id == 1)
        .first()
    )

    if not prediction:
        print("Prediction not found!")

    else:
        # Get the match linked to this prediction
        match = prediction.match

        # Check whether the match has a final score
        if match.home_score is None or match.away_score is None:
            print("This match does not have a final score yet.")

        elif match.status != "finished":
            print("This match is not marked as finished yet.")

        else:
            # Calculate points using saved scores
            points = calculate_points(
                prediction.predicted_home_score,
                prediction.predicted_away_score,
                match.home_score,
                match.away_score
            )

            print("Match:", match.home_team, "vs", match.away_team)
            print(
                "Predicted score:",
                prediction.predicted_home_score,
                "-",
                prediction.predicted_away_score
            )
            print(
                "Actual score:",
                match.home_score,
                "-",
                match.away_score
            )
            print("Points earned:", points)

finally:
    db.close()
