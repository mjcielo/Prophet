from database import SessionLocal
from models import User

db = SessionLocal()

try:
    for user in db.query(User).all():
        print(user.id, user.username, user.email)
finally:
    db.close()