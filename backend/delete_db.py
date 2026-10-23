
from database import SessionLocal
from models import User

db = SessionLocal()

try:
    # Find the existing user
    user = db.query(User).filter(User.username == "akash").first()

    if user:
        # mark for deletion
        db.delete(user)

        # Save the change
        db.commit()

        print("User deleted successfully!")
    else:
        print("User not found!")

except Exception as e:
    db.rollback()
    print("Something went wrong:", e)

finally:
    db.close()
