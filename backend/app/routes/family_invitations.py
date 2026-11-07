from fastapi import APIRouter

from app.routes.shared.dependencies import DB, Student
from app.schemas.auth.access import FamilyJoined, SecretInput
from app.services.parents.invitations import accept_invitation

router = APIRouter(prefix="/family-invitations", tags=["parents"])


@router.post("/accept", response_model=FamilyJoined)
def accept(data: SecretInput, db: DB, user: Student):
    return accept_invitation(db, user, data.token)
