from datetime import date
from uuid import UUID

from app.schemas.achievements.responses import AchievementOut, AttendanceOut
from app.schemas.organizations.responses import SchoolOut
from app.schemas.registrations.responses import RegistrationOut
from app.schemas.shared.base import Output


class ProfileOut(Output):
    id: UUID
    first_name: str
    last_name: str
    birth_date: date
    school: SchoolOut
    grade: int | None
    city: str | None
    interests: list[str]
    profile_complete: bool


class SuccessOut(Output):
    attendances: list[AttendanceOut]
    achievements: list[AchievementOut]


class StudentRow(Output):
    id: UUID
    first_name: str
    last_name: str
    grade: int | None
    interests: list[str]
    application_count: int
    attendance_count: int
    achievement_count: int
    applications: list[RegistrationOut]
    attendances: list[AttendanceOut]
    achievements: list[AchievementOut]
