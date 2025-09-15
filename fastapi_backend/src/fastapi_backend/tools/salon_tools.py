"""
salon_tools.py
Frontend-only helpers for Chainlit.
⚠️ No direct database calls here — backend (FastAPI) handles that.
"""

from agents import function_tool
from fastapi_backend.salon_data import services
from fastapi_backend.opening_hours import OPENING_HOURS
import re


@function_tool
def search_services(keyword: str) -> str:
    """
    Search for services in salon_data.py by keyword.
    - If keyword == "all", list all services grouped by category.
    - Otherwise, return services whose name or category matches the keyword.
    """
    keyword = keyword.strip().lower()

    # Special case: show everything
    if keyword == "all":
        grouped = {}
        for s in services:
            grouped.setdefault(s["category"], []).append(s)

        output = []
        for category, items in grouped.items():
            output.append(f"💎 **{category}** 💎\n─────────────────────────")
            for s in items:
                output.append(f"• {s['name']} — {s['price']} ({s['description']})")
            output.append("")  # spacing
        return "\n".join(output)

    # Otherwise filter
    filtered = [
        s for s in services
        if keyword in s["name"].lower() or keyword in s["category"].lower()
    ]

    if not filtered:
        return f"⚠️ No matching services found for '{keyword}'."

    output = []
    for s in filtered:
        output.append(f"• {s['name']} — {s['price']} ({s['description']})")
    return "\n".join(output)


def parse_duration(duration_str: str) -> int:
    """
    Convert service duration string (e.g. '2 hrs 15 mins') into total minutes.
    """
    hours = 0
    minutes = 0
    if "hr" in duration_str:
        match = re.search(r"(\d+)\s*hr", duration_str)
        if match:
            hours = int(match.group(1))
    if "min" in duration_str:
        match = re.search(r"(\d+)\s*min", duration_str)
        if match:
            minutes = int(match.group(1))
    return hours * 60 + minutes


def get_service_duration(service_name: str) -> int:
    """
    Look up a service duration from salon_data.py and return minutes.
    Default to 60 if not found.
    """
    for s in services:
        if s["name"].lower() == service_name.lower():
            return parse_duration(s["description"])
    return 60
