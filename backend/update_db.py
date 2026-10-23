
from database import SessionLocal
from models import User

db = SessionLocal()

try:
    # Find the existing user
    user = db.query(User).filter(User.username == "akash").first()

    if user:
        # Update the username
        user.username = "akash_pro"

        # Save the change
        db.commit()

        print("Username updated successfully!")
        print("New username:", user.username)
    else:
        print("User not found!")

except Exception as e:
    db.rollback()
    print("Something went wrong:", e)

finally:
    db.close()
