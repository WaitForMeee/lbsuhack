"""Explicitly delete only the seeded fixture and dependent records, preserving unrelated users."""

import argparse

from sqlalchemy import delete, or_, select, update

from app.db.session import SessionLocal
from app.models import (
    Achievement,
    ChildSuggestion,
    Event,
    EventRegistration,
    Notification,
    ParentChild,
    ParentLink,
    PartnershipRequest,
    PartnershipResponse,
    StudentProfile,
    User,
    event_interests,
    student_interests,
)
from app.scripts.seed_demo import demo_id, seed_demo
from app.scripts.presenter_demo import PRESENTER_ORGS, PRESENTER_USERS, print_credentials


def reset_demo(db):
    org_keys = [
        "school",
        "school2",
        "school3",
        "school4",
        "company",
        "academy",
        "robolab",
        "chem",
        "nano",
    ]
    user_keys = [
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
    org_keys.extend(PRESENTER_ORGS)
    user_keys.extend(PRESENTER_USERS)
    credentials = {}
    for key in user_keys:
        user = db.get(User, demo_id("user:" + key))
        if user is not None:
            credentials[key] = {field: getattr(user, field) for field in (
                "email", "password_hash", "organization_token_hash", "credential_version"
            )}
    org_ids = [demo_id("org:" + key) for key in org_keys]
    user_ids = [demo_id("user:" + key) for key in user_keys]
    # Custom accounts may have joined a demo school. Preserve them and the organization.
    event_ids = list(
        db.scalars(select(Event.id).where(Event.organizer_id.in_(org_ids)))
    )
    request_ids = list(
        db.scalars(
            select(PartnershipRequest.id).where(
                or_(
                    PartnershipRequest.sender_org_id.in_(org_ids),
                    PartnershipRequest.target_org_id.in_(org_ids),
                )
            )
        )
    )
    db.execute(
        delete(ChildSuggestion).where(
            or_(
                ChildSuggestion.parent_user_id.in_(user_ids),
                ChildSuggestion.student_user_id.in_(user_ids),
                ChildSuggestion.event_id.in_(event_ids),
            )
        )
    )
    db.execute(
        delete(ParentChild).where(
            or_(
                ParentChild.parent_user_id.in_(user_ids),
                ParentChild.student_user_id.in_(user_ids),
            )
        )
    )
    db.execute(
        delete(ParentLink).where(
            or_(
                ParentLink.parent_user_id.in_(user_ids),
                ParentLink.student_user_id.in_(user_ids),
            )
        )
    )
    for model in (Notification, Achievement, EventRegistration):
        db.execute(
            delete(model).where(
                or_(model.student_user_id.in_(user_ids), model.event_id.in_(event_ids))
            )
        )
    db.execute(
        delete(PartnershipResponse).where(
            or_(
                PartnershipResponse.request_id.in_(request_ids),
                PartnershipResponse.school_id.in_(org_ids),
            )
        )
    )
    db.execute(delete(PartnershipRequest).where(PartnershipRequest.id.in_(request_ids)))
    db.execute(delete(event_interests).where(event_interests.c.event_id.in_(event_ids)))
    db.execute(delete(Event).where(Event.id.in_(event_ids)))
    # Reviews on unrelated records must survive deletion of a demo moderator.
    for model in (Event, Achievement, PartnershipRequest):
        db.execute(
            update(model)
            .where(model.reviewed_by.in_(user_ids))
            .values(reviewed_by=None)
        )
    db.execute(
        delete(student_interests).where(
            student_interests.c.student_user_id.in_(user_ids)
        )
    )
    db.execute(delete(StudentProfile).where(StudentProfile.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.id.in_(user_ids)))
    db.expire_all()
    return seed_demo(db, credential_overrides=credentials)


def main():
    parser = argparse.ArgumentParser(
        description="Reset demo accounts, their events and dependent demo activity in DATABASE_URL."
    )
    parser.add_argument("--confirm-reset", action="store_true", required=True)
    parser.parse_args()
    with SessionLocal.begin() as db:
        result = reset_demo(db)
    print({key: value for key, value in result.items() if key != "credentials"})
    print_credentials(result["credentials"])


if __name__ == "__main__":
    main()
