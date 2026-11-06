from datetime import date

from app.schemas.organizations.responses import OrganizationOut
from app.schemas.shared.base import Output


class SchoolIndicator(Output):
    subject: str
    direction: str
    criterion: str
    count: int
    source: str
    period: str
    level: str
    updated: date
    confirmation: str = "подтверждено"


class SchoolDirectoryOut(OrganizationOut):
    type: str = "Школа"
    region: str
    programs: list[str]
    partnerships: list[str]
    events: list[str]
    achievements: list[str]
    history: list[str]
    admission: str = "Сведения о поступлении не добавлены."
    contacts: str = "Контакты не добавлены."
    indicators: list[SchoolIndicator]
    gap: str
