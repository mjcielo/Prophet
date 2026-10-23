
from database import SessionLocal
from models import Match

db = SessionLocal()

try:
    # Find the match by its ID
    match = db.query(Match).filter(Match.id == 1).first()

    if not match:
        print("Match not found!")

    else:
        # Enter the final score
        match.home_score = 2
        match.away_score = 1

        # Mark the match as finished
        match.status = "finished"

        db.commit()

        print("Match result saved!")
        print(f"{match.home_team} {match.home_score} - {match.away_score} {match.away_team}")
        print("Status:", match.status)

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
