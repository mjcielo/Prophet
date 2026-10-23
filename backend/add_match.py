from datetime import datetime
from database import SessionLocal
from models import Match

db = SessionLocal()

try:
    match = Match(
        home_team="Manchester United",
        away_team="Liverpool",
        kickoff=datetime(2026, 11, 1, 20, 0),
        status="Scheduled",
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    print("Match added successfully!")
    print("Match ID:", match.id)
    print(f"Match: {match.home_team} vs {match.away_team} ")
    print("Kickoff:", match.kickoff)
    print("Status:", match.status)

except Exception as e:
    db.rollback()
    print("Something went wrong:", e)

finally:
    db.close()