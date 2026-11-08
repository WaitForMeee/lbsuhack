from uuid import UUID, uuid4

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.demo import demo_preview, preview_only
from app.core.errors import fail
from app.models import Achievement, Event, PartnershipRequest, StudentProfile, User, Organization
from sqlalchemy.exc import IntegrityError
from app.core.security import hash_password
from app.schemas.auth.access import OrganizationAccountCreate, OrganizationAccountOut, OrganizationCredentialOut
from app.schemas.shared.base import Items
from app.services.organizations.credentials import account_view, issue_token
import secrets
from app.models.shared.mixins import now
from app.routes.shared.dependencies import DB, Moderator
from app.schemas.events.responses import EventOut
from app.schemas.moderation.requests import ModerationDecision
from app.schemas.moderation.responses import AchievementReview, QueueOut
from app.schemas.partnerships.responses import PartnershipOut
from app.services.events.views import event_view
from app.services.notifications.service import notify
from app.services.partnerships.views import partnership_view
from app.services.shared.repository import get
from app.services.students.views import profile_view
from app.services.users.views import user_view

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get("/organization-accounts", response_model=Items[OrganizationAccountOut])
def organization_accounts(db: DB, user: Moderator):
    accounts = db.scalars(select(User).where(User.role.in_(["school", "company"])).order_by(User.created_at, User.id))
    return {"items": [account_view(db, account) for account in accounts]}


@router.post("/organization-accounts", response_model=OrganizationCredentialOut, status_code=201)
@demo_preview
def create_organization_account(data: OrganizationAccountCreate, db: DB, user: Moderator):
    organization = db.get(Organization, data.organization_id) if data.organization_id else None
    if data.organization_id and organization is None:
        fail(422, "invalid_organization", "Организация не найдена")
    if preview_only(user):
        if db.scalar(select(User.id).where(User.email == str(data.email).lower().strip())) is not None:
            fail(409, "email_taken", "Email уже занят")
        organization = organization or Organization(
            **data.organization.model_dump(), id=uuid4(), description="", directions=[]
        )
        account = User(
            id=uuid4(), email=str(data.email).lower().strip(),
            first_name=data.first_name, last_name=data.last_name,
            role="school" if organization.kind == "school" else "company",
            organization_id=organization.id,
        )
        return {"account": {"user": user_view(db, account), "organization": organization,
                            "has_token": True}, "token": "th_preview_" + secrets.token_urlsafe(32)}
    try:
        if organization is None:
            organization = Organization(**data.organization.model_dump())
            db.add(organization)
            db.flush()
        account = User(
            email=str(data.email).lower().strip(), first_name=data.first_name,
            last_name=data.last_name, password_hash=hash_password(secrets.token_urlsafe(32)),
            role="school" if organization.kind == "school" else "company",
            organization_id=organization.id, credential_version=0,
        )
        token = issue_token(account)
        db.add(account)
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        fail(409, "email_taken", "Email уже занят")
    return {"account": account_view(db, account), "token": token}


@router.post("/organization-accounts/{identity}/token", response_model=OrganizationCredentialOut)
@demo_preview
def rotate_organization_token(identity: UUID, db: DB, user: Moderator):
    account = db.scalar(select(User).where(User.id == identity, User.role.in_(["school", "company"])).with_for_update())
    if account is None:
        fail(404, "not_found", "Аккаунт организации не найден")
    if preview_only(user):
        return {"account": account_view(db, account), "token": "th_preview_" + secrets.token_urlsafe(32)}
    token = issue_token(account)
    db.commit()
    return {"account": account_view(db, account), "token": token}


def achievement_view(db, a):
    return dict(
        id=a.id,
        title=a.title,
        event_id=a.event_id,
        status=a.status,
        student=profile_view(db, a.student_user_id),
    )


def section(db, model, column, renderer):
    rows = list(
        db.scalars(
            select(model)
            .where(column == "pending")
            .order_by(model.created_at, model.id)
        )
    )
    return dict(
        items=[renderer(r) for r in rows],
        decided_count=db.scalar(
            select(func.count())
            .select_from(model)
            .where(model.reviewed_at.is_not(None))
        ),
    )


@router.get("/queue", response_model=QueueOut)
def queue(db: DB, user: Moderator):
    return dict(
        events=section(db, Event, Event.status, lambda e: event_view(db, e, user)),
        partnership_requests=section(
            db,
            PartnershipRequest,
            PartnershipRequest.moderation_status,
            lambda p: partnership_view(db, p, user),
        ),
        achievements=section(
            db, Achievement, Achievement.status, lambda a: achievement_view(db, a)
        ),
    )


def review(db, model, identity, user, decision):
    row = get(db, model, identity, lock=True)
    field = "moderation_status" if model is PartnershipRequest else "status"
    target = (
        {
            "Event": "published",
            "PartnershipRequest": "approved",
            "Achievement": "confirmed",
        }[model.__name__]
        if decision == "approve"
        else "rejected"
    )
    # reviewed_at survives lifecycle changes, so retrying approve after completion remains idempotent.
    if row.reviewed_at is not None:
        approved = getattr(row, field) != "rejected"
        if approved == (decision == "approve"):
            return row
        fail(409, "decision_conflict", "Решение модератора уже принято")
    if getattr(row, field) != "pending":
        fail(409, "decision_conflict", "Запись уже рассмотрена")
    if preview_only(user):
        return row
    setattr(row, field, target)
    row.reviewed_by = user.id
    row.reviewed_at = now()
    if model is Event and decision == "approve":
        keys = {i.id for i in row.interests}
        for p in db.scalars(select(StudentProfile)):
            if keys.intersection(i.id for i in p.interests):
                notify(
                    db,
                    student_id=p.user_id,
                    event_id=row.id,
                    type="interest",
                    title="Новое мероприятие по интересам",
                    body=row.title,
                    key=f"publication:{row.id}:{p.user_id}",
                )
    db.commit()
    return row


@router.post("/events/{identity}/decision", response_model=EventOut)
@demo_preview
def event_decision(identity: UUID, data: ModerationDecision, db: DB, user: Moderator):
    return event_view(db, review(db, Event, identity, user, data.decision), user)


@router.post("/partnership-requests/{identity}/decision", response_model=PartnershipOut)
@demo_preview
def partnership_decision(
    identity: UUID, data: ModerationDecision, db: DB, user: Moderator
):
    return partnership_view(
        db, review(db, PartnershipRequest, identity, user, data.decision), user
    )


@router.post("/achievements/{identity}/decision", response_model=AchievementReview)
@demo_preview
def achievement_decision(
    identity: UUID, data: ModerationDecision, db: DB, user: Moderator
):
    return achievement_view(db, review(db, Achievement, identity, user, data.decision))
