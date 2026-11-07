import hashlib
import hmac
from datetime import UTC
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.core.errors import fail
from app.models import FamilyInvitation, ParentChild, ParentLink, User
from app.models.shared.mixins import now


def signing_key():
    return hmac.new(get_settings().jwt_secret.encode(), b"talenthub:family-invitation:v1", hashlib.sha256).digest()


def invitation_view(invitation):
    if invitation is None:
        return {"invitation": None}
    stamp = invitation.created_at.replace(tzinfo=UTC) if invitation.created_at.tzinfo is None else invitation.created_at
    token = jwt.encode(
        {"purpose": "family_invitation", "parent": str(invitation.parent_user_id), "jti": str(invitation.id), "iat": int(stamp.timestamp())},
        signing_key(), algorithm=get_settings().jwt_algorithm,
    )
    return {"invitation": {"token": token, "created_at": stamp}}


def invitation_parent(token):
    try:
        claims = jwt.decode(token, signing_key(), algorithms=[get_settings().jwt_algorithm], options={"require": ["purpose", "parent", "jti", "iat"]})
        if claims["purpose"] != "family_invitation":
            raise ValueError("Invalid purpose")
        return UUID(claims["parent"]), UUID(claims["jti"])
    except (InvalidTokenError, ValueError, TypeError, KeyError):
        fail(404, "invalid_invitation", "Ссылка недействительна или удалена")


def accept_invitation(db, student, token):
    parent_id, invitation_id = invitation_parent(token)
    # All creation, deletion and acceptance lock the same parent row first.
    parent = db.get(User, parent_id)
    if parent is None:
        fail(404, "invalid_invitation", "Ссылка недействительна или удалена")
    db.refresh(parent, with_for_update=True)
    invitation = db.get(FamilyInvitation, parent_id)
    if not parent.is_active or parent.role != "parent" or invitation is None or invitation.id != invitation_id:
        fail(404, "invalid_invitation", "Ссылка недействительна или удалена")
    already = db.get(ParentChild, (parent_id, student.id)) is not None
    if not already:
        db.add(ParentChild(parent_user_id=parent_id, student_user_id=student.id))
    if db.get(ParentLink, parent_id) is None:
        db.add(ParentLink(parent_user_id=parent_id, student_user_id=student.id, linked_at=now()))
    db.commit()
    return {"joined": True, "already_joined": already}
