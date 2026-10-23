
from database import SessionLocal
from models import User

db = SessionLocal()

# Find a user by username
user = db.query(User).filter(User.username == "akash_pro").first()

if user:
    print("User found!")
    print("ID:", user.id)
    print("Username:", user.username)
    print("Email:", user.email)
    print("Password Hash:", user.password_hash)
else:
    print("User not found!")

db.close()
