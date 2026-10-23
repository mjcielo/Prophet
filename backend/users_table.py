from database import SessionLocal
import models

db = SessionLocal()

try:
    users = db.query(models.User).all()

    for user in users:
        print(f"ID: {user.id}, Username: {user.username}")
finally:
    db.close()