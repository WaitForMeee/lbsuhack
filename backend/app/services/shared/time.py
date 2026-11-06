from datetime import datetime
from zoneinfo import ZoneInfo


def today():
    return datetime.now(ZoneInfo("Europe/Minsk")).date()
