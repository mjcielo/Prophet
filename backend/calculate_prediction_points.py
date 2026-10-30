
from database import SessionLocal
from models import Prediction, Match
from scoring import calculate_points

db = SessionLocal()

try:
    match_id = int(input("Enter finished match ID: "))

    match = (
        db.query(Match)
        .filter(Match.id == match_id)
        .first()
    )

    if not match:
        print("Match not found!")

    elif match.status != "finished":
        print("This match is not marked as finished yet.")

    elif match.home_score is None or match.away_score is None:
        print("This match does not have a final score yet.")

    else:
        predictions = (
            db.query(Prediction)
            .filter(Prediction.match_id == match_id)
            .all()
        )

        if not predictions:
            print("No predictions found for this match.")

        else:
            print("\nMatch:", match.home_team, "vs", match.away_team)
            print(
                "Actual score:",
                match.home_score,
                "-",
                match.away_score
            )
            print("\n--- Prediction Results ---")

            for prediction in predictions:
                prediction.points = calculate_points(
                    prediction.predicted_home_score,
                    prediction.predicted_away_score,
                    match.home_score,
                    match.away_score
                )

                print(
                    f"User ID: {prediction.user_id} | "
                    f"Predicted: "
                    f"{prediction.predicted_home_score}-"
                    f"{prediction.predicted_away_score} | "
                    f"Points: {prediction.points}"
                )

            db.commit()
            print("\nPoints saved successfully!")

except ValueError:
    print("Please enter a valid numeric match ID.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
