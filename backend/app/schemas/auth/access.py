from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import EmailStr, Field, model_validator

from app.schemas.shared.base import Input, Output
from app.schemas.shared.types import Name
from app.schemas.users.responses import UserOut
from app.schemas.organizations.responses import OrganizationOut


class SecretInput(Input):
    token: str = Field(min_length=1, max_length=2048)


class OrganizationLogin(SecretInput):
    expected_role: Literal["school", "company"] | None = None


class InvitationOut(Output):
    token: str
    created_at: datetime


class InvitationEnvelope(Output):
    invitation: InvitationOut | None


class FamilyJoined(Output):
    joined: bool
    already_joined: bool


class NewOrganization(Input):
    kind: Literal["school", "company", "academy"]
    name: str = Field(min_length=1, max_length=200)
    city: Name


class OrganizationAccountCreate(Input):
    organization_id: UUID | None = None
    organization: NewOrganization | None = None
    first_name: Name
    last_name: Name
    email: EmailStr

    @model_validator(mode="after")
    def exactly_one_organization(self) -> Self:
        if (self.organization_id is None) == (self.organization is None):
            raise ValueError("Выберите существующую организацию или укажите новую")
        return self


class OrganizationAccountOut(Output):
    user: UserOut
    organization: OrganizationOut
    has_token: bool


class OrganizationCredentialOut(Output):
    account: OrganizationAccountOut
    token: str
