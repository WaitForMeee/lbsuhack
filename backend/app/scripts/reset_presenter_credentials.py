"""Explicitly rotate private presenter credentials without resetting activity."""

import argparse

from app.core.demo import demo_id
from app.db.session import SessionLocal
from app.models import User
from app.scripts.presenter_demo import PRESENTER_USERS, fresh_credential, print_credentials


def reset_presenter_credentials(db):
    users = [db.get(User, demo_id("user:" + key)) for key in PRESENTER_USERS]
    if any(user is None for user in users):
        raise ValueError("Сначала выполните ./seed_demo.sh: закрытый набор создан не полностью")
    return [fresh_credential(user) for user in users]


def main():
    parser = argparse.ArgumentParser(description="Перевыпустить доступы закрытых аккаунтов без сброса данных")
    parser.add_argument("--confirm-reset", action="store_true", required=True)
    parser.parse_args()
    with SessionLocal.begin() as db:
        credentials = reset_presenter_credentials(db)
    print_credentials(credentials)


if __name__ == "__main__":
    main()
