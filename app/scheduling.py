from datetime import datetime, date as date_cls, timedelta
from app import db
from app.models import Appointment, BlockedDate, ScheduleConfig

ACTIVE_STATUSES = ("Pending", "Approved")  # count against capacity
DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_schedule_config():
    cfg = ScheduleConfig.query.get(1)
    if not cfg:
        cfg = ScheduleConfig(id=1)
        db.session.add(cfg)
        db.session.commit()
    return cfg


def _working_days_set(cfg):
    return set(d.strip() for d in cfg.working_days.split(",") if d.strip())


def _generate_day_slots(cfg):
    """All slot start times for a working day, as time objects."""
    slots = []
    current = datetime.combine(date_cls.today(), cfg.day_start_time)
    end = datetime.combine(date_cls.today(), cfg.day_end_time)
    step = timedelta(minutes=cfg.slot_duration_minutes)
    while current + step <= end:
        slots.append(current.time())
        current += step
    return slots


def _full_day_blocked(target_date):
    return BlockedDate.query.filter_by(date=target_date, is_full_day=True).first() is not None


def _blocked_time_ranges(target_date):
    """Partial-day blocks for a date -> list of (start_time, end_time)."""
    rows = BlockedDate.query.filter_by(date=target_date, is_full_day=False).all()
    return [(r.start_time, r.end_time) for r in rows]


def _time_in_ranges(t, ranges):
    return any(start <= t < end for start, end in ranges)


def get_slots_for_date(target_date, service):
    """Returns list of dicts: {time, available, remaining} for a given date + service."""
    cfg = get_schedule_config()

    if target_date < date_cls.today():
        return []
    if DAY_ABBR[target_date.weekday()] not in _working_days_set(cfg):
        return []
    if _full_day_blocked(target_date):
        return []

    blocked_ranges = _blocked_time_ranges(target_date)
    all_slots = _generate_day_slots(cfg)

    existing = (
        Appointment.query
        .filter(Appointment.appointment_date == target_date)
        .filter(Appointment.status.in_(ACTIVE_STATUSES))
        .all()
    )
    booked_counts = {}
    for a in existing:
        booked_counts[a.appointment_time] = booked_counts.get(a.appointment_time, 0) + 1

    result = []
    for slot_time in all_slots:
        if _time_in_ranges(slot_time, blocked_ranges):
            continue
        booked = booked_counts.get(slot_time, 0)
        cap = service.max_appointments_per_slot
        result.append({
            "time": slot_time,
            "booked": booked,
            "capacity": cap,
            "available": booked < cap,
        })

    if target_date == date_cls.today():
        now = datetime.now()
        result = [s for s in result if datetime.combine(target_date, s["time"]) > now]
    return result

def get_day_status(target_date, service):
    """Returns 'available' | 'limited' | 'full' | 'unavailable' for calendar coloring."""
    if target_date < date_cls.today():
        return "unavailable"

    cfg = get_schedule_config()
    if DAY_ABBR[target_date.weekday()] not in _working_days_set(cfg):
        return "unavailable"
    if _full_day_blocked(target_date):
        return "unavailable"

    day_count = (
        Appointment.query
        .filter(Appointment.appointment_date == target_date)
        .filter(Appointment.status.in_(ACTIVE_STATUSES))
        .count()
    )
    if day_count >= cfg.max_appointments_per_day:
        return "full"

    slots = get_slots_for_date(target_date, service)
    if not slots:
        return "unavailable"

    available_slots = [s for s in slots if s["available"]]
    if not available_slots:
        return "full"
    if len(available_slots) <= max(1, len(slots) // 3):
        return "limited"
    return "available"


def get_month_availability(year, month, service):
    """Dict of {day_number: status} for the whole month, for the public calendar."""
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    return {
        day: get_day_status(date_cls(year, month, day), service)
        for day in range(1, days_in_month + 1)
    }


def is_slot_still_available(target_date, target_time, service):
    """Re-check right before commit, to prevent double-booking races."""
    if _full_day_blocked(target_date):
        return False
    if _time_in_ranges(target_time, _blocked_time_ranges(target_date)):
        return False
    booked = (
        Appointment.query
        .filter(
            Appointment.appointment_date == target_date,
            Appointment.appointment_time == target_time,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
        .count()
    )
    return booked < service.max_appointments_per_slot

# ── canonical time format ────────────────────────────────────────────────
# HH:MM (24-hour) is used for every hidden field, query param, and DB round-trip.
# It's locale-independent — unlike "%I:%M %p", which depends on the platform's
# AM/PM strings and was the source of inconsistent parsing across environments.
TIME_INPUT_FORMAT = "%H:%M"
TIME_DISPLAY_FORMAT = "%I:%M %p"


def parse_time_from_input(time_str):
    """Parse the canonical 24-hour HH:MM string used for all internal
    round-tripping (forms, query params, admin reschedule input)."""
    return datetime.strptime(time_str, TIME_INPUT_FORMAT).time()


def format_time_for_display(t):
    """The one place that converts a time object to a human-readable label."""
    return t.strftime(TIME_DISPLAY_FORMAT)