from datetime import date

from app.schemas.shared.base import Input
from app.schemas.shared.types import Name


class ChildMatch(Input):
    first_name: Name
    last_name: Name
    birth_date: date
