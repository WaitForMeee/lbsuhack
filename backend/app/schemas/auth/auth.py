from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.organizations.organization import OrganizationType
from app.models.users.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    role: UserRole
    grade: int | None = Field(default=None, ge=1, le=11)
    region: str = Field(default="Минск", min_length=2, max_length=120)
    organization_name: str | None = Field(default=None, min_length=2, max_length=200)
    organization_type: OrganizationType | None = None
    organization_description: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_role_fields(self) -> "RegisterRequest":
        if self.role == UserRole.STUDENT:
            if self.organization_name is not None or self.organization_type is not None:
                raise ValueError("Учащемуся не нужна организация")
            return self
        if not self.organization_name:
            raise ValueError("Укажите название организации")
        if self.role == UserRole.INSTITUTION_REPRESENTATIVE:
            self.organization_type = OrganizationType.INSTITUTION
        elif self.organization_type not in {OrganizationType.COMPANY, OrganizationType.ACADEMY}:
            raise ValueError("Выберите компанию или академию")
        return self


class OrganizationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: OrganizationType


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    organization_id: UUID | None
    organization: OrganizationSummary | None
