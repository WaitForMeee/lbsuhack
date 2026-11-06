from app.schemas.registrations.responses import RegistrationOut
from app.schemas.shared.base import Output
from app.schemas.students.responses import ProfileOut, SuccessOut


class ChildOut(SuccessOut):
    profile: ProfileOut
    applications: list[RegistrationOut]


class ChildEnvelope(Output):
    child: ChildOut | None
