from datetime import datetime, timedelta
from chainlit_frontend.salon_data import services
import chainlit as cl, httpx

# API_BASE = "http://localhost:8001"  # ⬅️ replace with prod URL when deployed
API_BASE = "https://asuno-salon-chatbot.onrender.com"

class BookingFlow:
    """
    Deterministic booking flow for Asuna Salon.
    Delegates persistence to backend API.
    """

    def __init__(self):
        self.state = {}
        self.categories = sorted(set(s["category"] for s in services))

    async def start(self):
        """Step 1: Show categories"""
        self.state.clear()
        await cl.Message(
            content="📅 **Select a Luxury Category to Begin Booking**",
            actions=[
                cl.Action(
                    name="bf_select_category",
                    label=f"💎 {c}",
                    payload={"category": c},
                )
                for c in self.categories
            ],
        ).send()

    async def select_category(self, category: str):
        """Step 2: Show services in chosen category"""
        self.state["category"] = category
        filtered = [s for s in services if s["category"] == category]

        await cl.Message(
            content=(
                f"💎 **{category}**\n"
                "─────────────────────────\n"
                "Please choose a service:"
            ),
            actions=[
                *[
                    cl.Action(
                        name="bf_select_service",
                        label=f"{s['name']} — {s['price']} ({s['description']})",
                        payload={"service": s["name"]},
                    )
                    for s in filtered
                ],
                cl.Action(
                    name="exit_booking",
                    label="❌ Exit Booking",
                    payload={"intent": "exit"},
                ),
            ],
        ).send()

    async def select_service(self, service: str):
        """Step 3: Confirm service and show date options"""
        self.state["service"] = service
        chosen = next(s for s in services if s["name"] == service)

        today = datetime.today()
        date_options = [
            (today + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, 8)
        ]

        await cl.Message(
            content=(
                f"✅ {chosen['name']} selected\n"
                f"💰 {chosen['price']}   ⏱ {chosen['description']}\n\n"
                "📅 Please select your preferred date:"
            ),
            actions=[
                *[
                    cl.Action(
                        name="bf_select_date",
                        label=d,
                        payload={"date": d},
                    )
                    for d in date_options
                ],
                cl.Action(
                    name="exit_booking",
                    label="❌ Exit Booking",
                    payload={"intent": "exit"},
                ),
            ],
        ).send()

    async def provide_date(self, date: str):
        """Step 4: Fetch available slots from backend API"""
        service_name = self.state.get("service")
        if not service_name:
            # user clicked date without selecting service
            await cl.Message(
                content="⚠️ I couldn't find the service you want to book. Please select a service first."
            ).send()
            await self.start()
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{API_BASE}/bookings/available-times/{date}",
                    params={"service": service_name},
                )
                resp.raise_for_status()

                # Defensive JSON parsing
                content_type = resp.headers.get("content-type", "")
                if "application/json" not in content_type.lower():
                    # Unexpected content type, avoid JSONDecodeError
                    await cl.Message(
                        content="⚠️ Unexpected response from booking server. Please try again later."
                    ).send()
                    return

                try:
                    result = resp.json()
                except ValueError:
                    await cl.Message(
                        content="⚠️ Booking server returned invalid data. Please try again later."
                    ).send()
                    return

        except httpx.RequestError:
            await cl.Message(
                content="⚠️ Could not reach the booking server. Please try again shortly."
            ).send()
            return
        except httpx.HTTPStatusError as e:
            body = ""
            try:
                body = e.response.text
            except Exception:
                body = f"HTTP {e.response.status_code}"
            await cl.Message(
                content=f"⚠️ Failed to fetch available times: {body}"
            ).send()
            return

        # Validate structure
        if not isinstance(result, dict):
            await cl.Message(
                content="⚠️ Unexpected response from booking server. Please try again later."
            ).send()
            return

        available = result.get("available", []) or []
        result_date = result.get("date")

        if not available:
            await cl.Message(
                content="⚠️ Sorry, no available slots in the next 14 days. Please try a later date."
            ).send()
            return

        # Save date & show available times
        self.state["date"] = result_date

        await cl.Message(
            content=f"📅 Available times on {result_date}:",
            actions=[
                *[
                    cl.Action(
                        name="bf_select_time",
                        label=t,
                        payload={"time": t, "date": result_date},
                    )
                    for t in available
                ],
                cl.Action(
                    name="exit_booking",
                    label="❌ Exit Booking",
                    payload={"intent": "exit"},
                ),
            ],
        ).send()

    async def select_time(self, time: str):
        """Step 5: Show summary and ask for client name"""
        # Defensive checks
        if "service" not in self.state or "date" not in self.state:
            await cl.Message(
                content="⚠️ Booking state lost. Let's start again."
            ).send()
            await self.start()
            return

        self.state["time"] = time
        service = self.state["service"]
        date = self.state["date"]

        await cl.Message(
            content=(
                f"📋 Appointment Summary\n"
                f"- Service: {service}\n"
                f"- Date: {date}\n"
                f"- Time: {time}\n\n"
                "👉 To complete your booking, may I have your name?"
            ),
            actions=[
                cl.Action(
                    name="exit_booking",
                    label="❌ Exit Booking",
                    payload={"intent": "exit"},
                ),
            ],
        ).send()

    async def finalize(self, name: str):
        """Step 6: Send booking request to backend"""
        # Ensure state is valid
        if not all(k in self.state for k in ("service", "date", "time")):
            await cl.Message(
                content="⚠️ Booking data incomplete. Please start again."
            ).send()
            self.state.clear()
            return

        self.state["name"] = name

        booking_data = {
            "service": self.state["service"],
            "category": self.state.get("category"),
            "date": self.state["date"],
            "time": self.state["time"],
            "client_name": name,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{API_BASE}/bookings", json=booking_data)
                resp.raise_for_status()

                # Defensive JSON parsing
                content_type = resp.headers.get("content-type", "")
                if "application/json" not in content_type.lower():
                    await cl.Message(
                        content="⚠️ Booking server returned unexpected response. Please contact support."
                    ).send()
                    self.state.clear()
                    return

                try:
                    result = resp.json()
                except ValueError:
                    await cl.Message(
                        content="⚠️ Booking server returned invalid data. Please contact support."
                    ).send()
                    self.state.clear()
                    return
        except httpx.RequestError:
            await cl.Message(
                content="⚠️ Could not reach the booking server. Please try again shortly."
            ).send()
            return
        except httpx.HTTPStatusError as e:
            body = ""
            try:
                body = e.response.text
            except Exception:
                body = f"HTTP {e.response.status_code}"
            await cl.Message(
                content=f"⚠️ Booking failed: {body}"
            ).send()
            return

        # Expect reference in response (be defensive)
        reference = None
        if isinstance(result, dict):
            reference = result.get("reference")

        if not reference:
            await cl.Message(
                content="⚠️ Booking was created but we did not receive a confirmation reference. Please contact the salon."
            ).send()
            self.state.clear()
            return

        await cl.Message(
            content=(
                "🎉 **Booking Confirmed!**\n\n"
                f"📋 Appointment Summary\n"
                f"- Service: {self.state['service']}\n"
                f"- Date: {self.state['date']}\n"
                f"- Time: {self.state['time']}\n"
                f"- Client: {name}\n"
                f"- Reference: {reference}\n\n"
                "✅ You'll receive a reminder 24 hours before your appointment."
            ),
            actions=[
                cl.Action(name="book", label="📅 Book Another Appointment", payload={"intent": "book"}),
                cl.Action(name="explore", label="✨ Explore Services", payload={"intent": "explore"}),
                cl.Action(name="hours", label="⏰ Opening Hours", payload={"intent": "hours"}),
            ],
        ).send()

        self.state.clear()