"""
Run this once after first install to create the initial admin account:

    python seed_admin.py

Then log in from the frontend with the printed credentials and create
further inspector / viewer accounts from the Admin Panel.
"""

import getpass

from app.database import SessionLocal, Base, engine
from app import models, auth as auth_utils

Base.metadata.create_all(bind=engine)


def main():
    db = SessionLocal()
    try:
        email = input("Admin email [admin@metrology.gov.in]: ").strip() or "admin@metrology.gov.in"
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            print(f"A user with email {email} already exists. Aborting.")
            return

        name = input("Admin name [System Administrator]: ").strip() or "System Administrator"
        password = getpass.getpass("Admin password [admin123]: ") or "admin123"

        user = models.User(
            name=name,
            email=email,
            hashed_password=auth_utils.hash_password(password),
            role=models.UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        print(f"\nAdmin user created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
