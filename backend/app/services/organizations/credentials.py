import hashlib
import secrets

from app.models import Organization
from app.services.users.views import user_view


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token(user, token=None):
    token = token or "th_org_" + secrets.token_urlsafe(32)
    user.organization_token_hash = token_hash(token)
    user.credential_version += 1
    return token


def account_view(db, user):
    return dict(user=user_view(db, user), organization=db.get(Organization, user.organization_id), has_token=user.organization_token_hash is not None)
