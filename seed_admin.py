"""
Run this once to create (or re-enable) the initial admin account in MongoDB:

    python seed_admin.py

Then log in from the frontend with the printed credentials and create
further inspector / viewer accounts from the Admin Panel.

Note: the API also creates a bootstrap admin automatically on first start when
the users collection is empty (ADMIN_EMAIL / ADMIN_PASSWORD in .env), so this
script is only needed when you want to choose the credentials yourself.
"""

import getpass
import sys

from app import crud, database, models
from app import auth as auth_utils


def main():
    if not database.init_db():
        print("MongoDB is not reachable - check MONGODB_URI in .env", file=sys.stderr)
        return 1

    email = input("Admin email [admin@metrology.gov.in]: ").strip() or "admin@metrology.gov.in"
    existing = crud.get_user_by_email(email)
    if existing:
        print(f"A user with email {email} already exists. Aborting.")
        return 1

    name = input("Admin name [System Administrator]: ").strip() or "System Administrator"
    password = getpass.getpass("Admin password [admin123]: ") or "admin123"

    crud.create_user(
        name=name,
        email=email,
        hashed_password=auth_utils.hash_password(password),
        role=models.UserRole.ADMIN.value,
    )
    crud.add_audit_log(None, "ADMIN_SEEDED", f"Admin account {email} created via seed script")
    print(f"\nAdmin user created: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
