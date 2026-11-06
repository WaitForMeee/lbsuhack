"""Explicit reset of v2 demo account passwords only."""

import argparse

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User
from app.scripts.seed_demo import PASSWORD, demo_id


def main():
    parser = argparse.ArgumentParser(
        description="Reset demo account passwords to demo1234"
    )
    parser.add_argument("--confirm-reset", action="store_true", required=True)
    parser.parse_args()
    keys = [
        "alina",
        "mark",
        "olga",
        "school",
        "company",
        "admin",
        "school2",
        "academy",
        "ilya",
        "maria",
        "timofey",
    ]
    with SessionLocal.begin() as db:
        for user in db.scalars(
            select(User).where(User.id.in_([demo_id("user:" + key) for key in keys]))
        ):
            user.password_hash = hash_password(PASSWORD)


if __name__ == "__main__":
    main()
