from typing import Literal

from app.schemas.achievements.responses import AchievementOut
from app.schemas.events.responses import EventOut
from app.schemas.partnerships.responses import PartnershipOut
from app.schemas.shared.base import Output, QueueSection
from app.schemas.students.responses import ProfileOut


class AchievementReview(AchievementOut):
    student: ProfileOut
    status: Literal["pending", "confirmed", "rejected"]


class QueueOut(Output):
    events: QueueSection[EventOut]
    partnership_requests: QueueSection[PartnershipOut]
    achievements: QueueSection[AchievementReview]
