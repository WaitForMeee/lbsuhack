from typing import Literal

from fastapi import APIRouter
from sqlalchemy import select

from app.models import Interest, Organization
from app.routes.shared.dependencies import DB
from app.schemas.organizations.responses import OrganizationOut
from app.schemas.reference.responses import ReferenceOut
from app.schemas.shared.base import Items
from app.services.shared.text import normalize

router = APIRouter(tags=["reference"])


@router.get("/reference-data", response_model=ReferenceOut)
def reference(db: DB):
    interests = list(
        db.scalars(
            select(Interest)
            .where(Interest.is_suggested.is_(True))
            .order_by(Interest.name)
        )
    )
    olympiad = ["Математика", "Информатика", "Физика", "Биология", "Химия"]
    return dict(
        grades=list(range(7, 12)),
        cities=["Минск", "Брест", "Гродно", "Гомель", "Витебск", "Могилёв"],
        formats=["offline", "online", "hybrid"],
        event_kinds=["olympiad", "project"],
        interests=interests,
        direction_groups=dict(olympiad=olympiad, project=[i.name for i in interests]),
    )


@router.get("/organizations", response_model=Items[OrganizationOut])
def organizations(
    db: DB, kind: Literal["school", "company", "academy"] | None = None, q: str = ""
):
    return dict(
        items=[
            o
            for o in db.scalars(
                select(Organization).order_by(Organization.name, Organization.id)
            )
            if (not kind or o.kind == kind)
            and normalize(q) in normalize(o.name + " " + o.city)
        ]
    )
