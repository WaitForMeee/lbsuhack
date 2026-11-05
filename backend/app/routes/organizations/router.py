from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.organizations.organization import Organization, OrganizationType
from app.routes.auth.dependencies import OrganizationUser
from app.schemas.organizations.organization import OrganizationRead, OrganizationUpdate
from app.services.organizations.organization import organization_to_read

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
def list_organizations(session: Annotated[Session, Depends(get_db_session)], search: str | None = None, type: OrganizationType | None = None) -> list[OrganizationRead]:
    query = select(Organization).order_by(Organization.name)
    if search:
        pattern = f"%{search.strip()}%"; query = query.where(or_(Organization.name.ilike(pattern), Organization.description.ilike(pattern), Organization.directions.ilike(pattern)))
    if type: query = query.where(Organization.type == type)
    return [organization_to_read(session, item) for item in session.scalars(query)]


@router.get("/me", response_model=OrganizationRead)
def my_organization(user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> OrganizationRead:
    organization = session.get(Organization, user.organization_id)
    if organization is None: raise HTTPException(404, "Организация не найдена")
    return organization_to_read(session, organization)


@router.put("/me", response_model=OrganizationRead)
def update_organization(payload: OrganizationUpdate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> OrganizationRead:
    organization = session.get(Organization, user.organization_id)
    if organization is None: raise HTTPException(404, "Организация не найдена")
    for key, value in payload.model_dump().items(): setattr(organization, key, value)
    try: session.commit()
    except IntegrityError as exc: session.rollback(); raise HTTPException(409, "Организация с таким названием уже существует") from exc
    return organization_to_read(session, organization)


@router.get("/{organization_id}", response_model=OrganizationRead)
def get_organization(organization_id: UUID, session: Annotated[Session, Depends(get_db_session)]) -> OrganizationRead:
    organization = session.get(Organization, organization_id)
    if organization is None: raise HTTPException(404, "Организация не найдена")
    return organization_to_read(session, organization)
