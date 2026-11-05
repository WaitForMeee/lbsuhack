from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db_session
from app.models.organizations.organization import Organization, OrganizationType
from app.models.partnerships.partnership import OpportunityDirection, OpportunityStatus, Partnership, PartnershipOpportunity, PartnershipResponse, ResponseStatus
from app.routes.auth.dependencies import OrganizationUser
from app.schemas.partnerships.partnership import OpportunityCreate, OpportunityRead, PartnershipRead, ResponseCreate, ResponseUpdate
from app.services.partnerships.partnership import accept_response, confirm_partnership, opportunity_to_read, partnership_to_read

router = APIRouter(tags=["partnerships"])


def opportunity_query():
    return select(PartnershipOpportunity).options(joinedload(PartnershipOpportunity.creator_organization), joinedload(PartnershipOpportunity.target_organization), selectinload(PartnershipOpportunity.responses).joinedload(PartnershipResponse.responder_organization))


@router.get("/partnership-opportunities", response_model=list[OpportunityRead])
def list_opportunities(session: Annotated[Session, Depends(get_db_session)], user: OrganizationUser, mine: bool = False, incoming: bool = False) -> list[OpportunityRead]:
    query = opportunity_query()
    if mine: query = query.where(PartnershipOpportunity.creator_organization_id == user.organization_id)
    elif incoming: query = query.where(or_(PartnershipOpportunity.target_organization_id == user.organization_id, PartnershipOpportunity.responses.any(responder_organization_id=user.organization_id)))
    else:
        query = query.where(PartnershipOpportunity.status == OpportunityStatus.OPEN, or_(PartnershipOpportunity.target_organization_id.is_(None), PartnershipOpportunity.target_organization_id == user.organization_id))
    return [opportunity_to_read(session, item) for item in session.scalars(query.order_by(PartnershipOpportunity.created_at.desc())).unique()]


@router.get("/partnership-opportunities/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: UUID, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> OpportunityRead:
    item = session.scalar(opportunity_query().where(PartnershipOpportunity.id == opportunity_id))
    if item is None: raise HTTPException(404, "Запрос не найден")
    if item.target_organization_id and item.target_organization_id not in {user.organization_id, item.creator_organization_id}: raise HTTPException(403, "Запрос адресован другой организации")
    return opportunity_to_read(session, item)


@router.post("/partnership-opportunities", response_model=OpportunityRead, status_code=201)
def create_opportunity(payload: OpportunityCreate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> OpportunityRead:
    organization = session.get(Organization, user.organization_id)
    if organization is None: raise HTTPException(404, "Организация не найдена")
    if payload.direction == OpportunityDirection.INSTITUTION_SEEKS_ORGANIZATION and organization.type != OrganizationType.INSTITUTION: raise HTTPException(403, "Это направление доступно только учреждениям")
    if payload.direction == OpportunityDirection.ORGANIZATION_SEEKS_INSTITUTION and organization.type == OrganizationType.INSTITUTION: raise HTTPException(403, "Это направление доступно компаниям и академиям")
    if payload.target_organization_id == organization.id: raise HTTPException(400, "Нельзя адресовать запрос себе")
    target = session.get(Organization, payload.target_organization_id) if payload.target_organization_id else None
    if payload.target_organization_id and target is None: raise HTTPException(404, "Адресат не найден")
    if target and payload.direction == OpportunityDirection.INSTITUTION_SEEKS_ORGANIZATION and target.type == OrganizationType.INSTITUTION: raise HTTPException(400, "Учреждение должно выбрать компанию или академию")
    if target and payload.direction == OpportunityDirection.ORGANIZATION_SEEKS_INSTITUTION and target.type != OrganizationType.INSTITUTION: raise HTTPException(400, "Компания или академия должна выбрать учреждение")
    item = PartnershipOpportunity(creator_organization_id=organization.id, **payload.model_dump())
    session.add(item); session.commit()
    return opportunity_to_read(session, session.scalar(opportunity_query().where(PartnershipOpportunity.id == item.id)))


@router.post("/partnership-opportunities/{opportunity_id}/responses", response_model=OpportunityRead, status_code=201)
def respond(opportunity_id: UUID, payload: ResponseCreate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> OpportunityRead:
    item = session.scalar(opportunity_query().where(PartnershipOpportunity.id == opportunity_id))
    if item is None: raise HTTPException(404, "Запрос не найден")
    if item.status != OpportunityStatus.OPEN: raise HTTPException(409, "Запрос закрыт")
    if item.creator_organization_id == user.organization_id: raise HTTPException(400, "Нельзя откликнуться на свой запрос")
    if item.target_organization_id and item.target_organization_id != user.organization_id: raise HTTPException(403, "Запрос адресован другой организации")
    responder = session.get(Organization, user.organization_id)
    if item.direction == OpportunityDirection.INSTITUTION_SEEKS_ORGANIZATION and responder.type == OrganizationType.INSTITUTION: raise HTTPException(403, "На этот запрос отвечают компании и академии")
    if item.direction == OpportunityDirection.ORGANIZATION_SEEKS_INSTITUTION and responder.type != OrganizationType.INSTITUTION: raise HTTPException(403, "На эту инициативу отвечают учреждения")
    session.add(PartnershipResponse(opportunity_id=item.id, responder_organization_id=user.organization_id, message=payload.message))
    try: session.commit()
    except IntegrityError as exc: session.rollback(); raise HTTPException(409, "Отклик уже отправлен") from exc
    session.expire_all()
    return opportunity_to_read(session, session.scalar(opportunity_query().where(PartnershipOpportunity.id == item.id)))


@router.patch("/partnership-responses/{response_id}", response_model=OpportunityRead)
def update_response(response_id: UUID, payload: ResponseUpdate, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> OpportunityRead:
    response = session.scalar(select(PartnershipResponse).options(joinedload(PartnershipResponse.opportunity).selectinload(PartnershipOpportunity.responses)).where(PartnershipResponse.id == response_id))
    if response is None: raise HTTPException(404, "Отклик не найден")
    if payload.status == ResponseStatus.ACCEPTED:
        if response.opportunity.creator_organization_id != user.organization_id: raise HTTPException(403, "Принять отклик может только автор")
        try: accept_response(session, response)
        except ValueError as exc: raise HTTPException(409, str(exc)) from exc
    elif payload.status == ResponseStatus.REJECTED:
        if response.opportunity.creator_organization_id != user.organization_id: raise HTTPException(403, "Отклонить отклик может только автор")
        if response.status != ResponseStatus.PENDING: raise HTTPException(409, "Отклик уже обработан")
        response.status = ResponseStatus.REJECTED
    elif payload.status == ResponseStatus.WITHDRAWN:
        if response.responder_organization_id != user.organization_id: raise HTTPException(403, "Отозвать можно только свой отклик")
        if response.status != ResponseStatus.PENDING: raise HTTPException(409, "Отклик уже обработан")
        response.status = ResponseStatus.WITHDRAWN
    else: raise HTTPException(400, "Недопустимый статус")
    session.commit()
    return opportunity_to_read(session, session.scalar(opportunity_query().where(PartnershipOpportunity.id == response.opportunity_id)))


@router.get("/partnerships", response_model=list[PartnershipRead])
def list_partnerships(user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> list[PartnershipRead]:
    query = select(Partnership).options(joinedload(Partnership.opportunity), joinedload(Partnership.organization_a), joinedload(Partnership.organization_b)).where(or_(Partnership.organization_a_id == user.organization_id, Partnership.organization_b_id == user.organization_id)).order_by(Partnership.created_at.desc())
    return [partnership_to_read(session, item) for item in session.scalars(query).unique()]


@router.post("/partnerships/{partnership_id}/confirm-completion", response_model=PartnershipRead)
def confirm_completion(partnership_id: UUID, user: OrganizationUser, session: Annotated[Session, Depends(get_db_session)]) -> PartnershipRead:
    item = session.scalar(select(Partnership).options(joinedload(Partnership.opportunity), joinedload(Partnership.organization_a), joinedload(Partnership.organization_b)).where(Partnership.id == partnership_id))
    if item is None: raise HTTPException(404, "Партнёрство не найдено")
    try: confirm_partnership(session, item, user.organization_id)
    except PermissionError as exc: raise HTTPException(403, str(exc)) from exc
    session.commit(); return partnership_to_read(session, item)
