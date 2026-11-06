from app.models import Organization
from app.schemas.organizations.responses import OrganizationOut


def org_view(db, identity):
    return (
        OrganizationOut.model_validate(db.get(Organization, identity)).model_dump()
        if identity
        else None
    )
