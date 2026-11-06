from datetime import UTC, datetime

from app.services.shared import time as common


def test_deadline_uses_minsk_calendar_day(monkeypatch):
    class Clock:
        @classmethod
        def now(cls, tz):
            # Still November 6 in UTC; already November 7 in Minsk.
            return datetime(2026, 11, 6, 21, 1, tzinfo=UTC).astimezone(tz)

    monkeypatch.setattr(common, "datetime", Clock)
    assert common.today().isoformat() == "2026-11-07"
