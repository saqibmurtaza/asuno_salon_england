from asuno_salon_birmingham.chainlit_frontend.salon_data import services
from datetime import datetime, timedelta


# --------- UTILITIES ---------
def parse_duration(duration_str: str) -> int:
    """Convert '2 hrs 15 mins' → total minutes."""
    hours = 0
    minutes = 0
    if "hr" in duration_str:
        import re
        match = re.search(r"(\d+)\s*hr", duration_str)
        if match:
            hours = int(match.group(1))
    if "min" in duration_str:
        import re
        match = re.search(r"(\d+)\s*min", duration_str)
        if match:
            minutes = int(match.group(1))
    return hours * 60 + minutes


def get_service_duration(service_name: str) -> int:
    """Look up service duration from salon_data.py."""
    for s in services:
        if s["name"].lower() == service_name.lower():
            return parse_duration(s["description"])
    return 60


def generate_time_slots(start: str, end: str, service_minutes: int):
    """Generate available start times between open/close respecting service duration."""
    slots = []
    current = datetime.strptime(start, "%H:%M")
    closing = datetime.strptime(end, "%H:%M")

    while current + timedelta(minutes=service_minutes) <= closing:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=service_minutes)

    return slots
