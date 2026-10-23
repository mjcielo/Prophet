
from database import SessionLocal
from models import Match

db = SessionLocal()

try:
    # Fetch all matches, ordered by kickoff time
    matches = db.query(Match).order_by(Match.kickoff).all()

    if matches:
        print("FOOTBALL MATCHES")
        print("-" * 40)

        for match in matches:
            print(f"Match ID: {match.id}")
            print(f"{match.home_team} vs {match.away_team}")
            print(f"Kickoff: {match.kickoff}")
            print(f"Status: {match.status}")
            print("-" * 40)
    else:
        print("No matches found.")

finally:
    db.close()
