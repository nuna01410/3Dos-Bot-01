import pytz

from datetime import datetime, timedelta


def parse_iso_to_pytz_utc(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.astimezone(pytz.UTC)


def get_sleep_duration(sleep_until: datetime, to_seconds: bool = False, to_minutes: bool = True) -> float:
    current_time = datetime.now(pytz.UTC)
    sleep_until = sleep_until.replace(tzinfo=pytz.UTC)

    if sleep_until > current_time:
        if to_seconds:
            return (sleep_until - current_time).total_seconds()
        elif to_minutes:
            return (sleep_until - current_time).total_seconds() / 60

    return 0


def get_sleep_until(minutes: int = 0, seconds: int = 0) -> datetime:
    current_time = datetime.now(pytz.UTC)
    sleep_until = current_time

    if minutes > 0:
        sleep_until = sleep_until + timedelta(minutes=minutes)

    if seconds > 0:
        sleep_until = sleep_until + timedelta(seconds=seconds)

    return sleep_until.replace(tzinfo=pytz.UTC)
