from collections import defaultdict
import sys
import os

# Add the correct path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'chainlit_frontend', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chainlit_frontend.booking_flow import BookingFlow
from chainlit_frontend.salon_data import services
import chainlit as cl
import httpx

os.environ["CHAINLIT_DISABLE_PERSISTENCE"] = "true"  # Force stateless mode for easier local testing

# Show a small startup message so you can see stateless mode is active
if not os.getenv("CHAINLIT_DB_URL"):
    print("Chainlit stateless mode: CHAINLIT_DB_URL is NOT set. Persistence disabled.")


# Global booking flow instance (1 per session)
booking_flow = BookingFlow()


API_BASE = os.getenv("API_BASE", "http://localhost:8000")
# Debug: Print to verify it's loaded
print(f"API_BASE loaded as: {API_BASE}")

# API_BASE = "https://asuno-salon-chatbot.onrender.com"

@cl.on_chat_start
async def on_chat_start():
    # Session ID is implicitly managed by the user's connection.
    # The backend will handle session state based on the ID we send.
    await cl.Message(
        content=(
            "💇‍♀️ **Welcome to Asuna Salon!** ✨\n\n"
            "Easily explore our beauty & styling services using the quick buttons below, "
            "or just tell me what you’re looking for.\n\n"
            "💡 Tip: Type **Hi** to connect with our our friendly Assistant **Aria**."
        ),
        actions=[
            cl.Action(name="explore", label="✨ Explore Services", payload={"intent": "explore"}),
            cl.Action(name="book", label="📅 Book Appointment", payload={"intent": "book"}),
            cl.Action(name="hours", label="⏰ Opening Hours", payload={"intent": "hours"}),
        ],
    ).send()

async def send_followup_buttons(content: str):
    """Reusable helper to show standard follow-up actions"""
    await cl.Message(
        content=content,
        actions=[
            cl.Action(name="book", label="📅 Book Appointment", payload={"intent": "book"}),
            cl.Action(name="explore", label="✨ Explore Services", payload={"intent": "explore"}),
            cl.Action(name="hours", label="⏰ Opening Hours", payload={"intent": "hours"}),
        ],
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("id")
    user_input = message.content.strip()
    lower_input = user_input.lower()

    # If user is in middle of booking (expecting a date or name)
    if "service" in booking_flow.state and "date" not in booking_flow.state:
        await booking_flow.provide_date(user_input)
        return
    elif "time" in booking_flow.state and "name" not in booking_flow.state:
        await booking_flow.finalize(user_input)
        return

    # Special case: user greets Aria
    if lower_input in ["hi", "hello", "hey"]:
        intro = (
            "👋 Hi there! I'm Aria, and I'm here to help you with your marketing questions.\n\n"
            "What's on your mind today?\n\n"
            "✨ To browse services, please use the **Explore Services** button below.\n"
            "📅 To schedule a visit, click the **Book Appointment** button.\n\n"
            "Or simply ask me a question, and I’ll be glad to guide you!"
        )
        await cl.Message(content=intro).send()
        await send_followup_buttons("✨ What would you like to do next?")
        return

    # Otherwise → forward to marketing agent Aria via API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/agent/run",
                json={"user_input": user_input, "session_id": session_id},
                timeout=60, # Extend timeout for potentially long-running agent
            )
            response.raise_for_status() # Raise an exception for bad status codes
            agent_response = response.json()
            await cl.Message(content=agent_response.get("response", "Sorry, something went wrong.")).send()

    except httpx.HTTPStatusError as e:
        await cl.Message(content=f"Sorry, the service is temporarily unavailable. Please try again later. (Error: {e.response.status_code})").send()
    except httpx.RequestError:
        await cl.Message(content="Sorry, I couldn't connect to the backend service. Please check if it's running.").send()
    except Exception as e:
        await cl.Message(content=f"An unexpected error occurred: {e}").send()

    await send_followup_buttons("✨ What would you like to do next?")

# ---------- ACTION BUTTON CALLBACKS ----------

def with_aria_footer(content: str) -> str:
    """Append the Aria reminder to any chatbot message."""
    return content + "\n\n💡 Just type *Hi* anytime to say hello to **Aria, our friendly Assistant**!"

@cl.action_callback("explore")
async def explore_action(action: cl.Action):
    """Instantly show all salon services with professional formatting."""
    # Group services by category
    grouped = defaultdict(list)
    for s in services:
        grouped[s["category"]].append(s)

    # Build formatted output
    parts = []
    for category, items in grouped.items():
        parts.append(f"💎 {category} 💎\n" + "─" * 25)
        for item in items:
            parts.append(
                f"• {item['name']} — {item['price']} ({item['description']})"
            )
        parts.append("")  # blank line after each category

    services_text = "\n".join(parts).strip()
    services_text += (
        "\nTo schedule your visit, please click the 📅 **Book Appointment** button below."
    )

    # await cl.Message(content=services_text).send()
    await cl.Message(content=with_aria_footer(services_text)).send()
    await send_followup_buttons("✨ What would you like to do next?")


@cl.action_callback("book")
async def book_action(action: cl.Action):
    """Trigger deterministic booking flow"""
    await booking_flow.start()

@cl.action_callback("hours")
async def hours_action(action: cl.Action):
    hours_text = (
        "⏰ **Opening Hours**\n\n"
        "Mon & Fri: Closed\n"
        "Sat & Sun: 10:00 AM – 6:30 PM\n"
        "Tues to Thurs: 9:30 AM – 6:30 PM"
    )
    await cl.Message(content=with_aria_footer(hours_text)).send()
    await send_followup_buttons("✨ What would you like to do next?")

@cl.action_callback("bf_select_category")
async def bf_select_category(action: cl.Action):
    category = action.payload.get("category")
    await booking_flow.select_category(category)


@cl.action_callback("bf_select_service")
async def bf_select_service(action: cl.Action):
    service = action.payload.get("service")
    await booking_flow.select_service(service)


@cl.action_callback("bf_select_time")
async def bf_select_time(action: cl.Action):
    time = action.payload.get("time")
    await booking_flow.select_time(time)

@cl.action_callback("bf_select_date")
async def bf_select_date(action: cl.Action):
    date = action.payload.get("date")
    await booking_flow.provide_date(date)

@cl.action_callback("exit_booking")
async def exit_booking(action: cl.Action):
    booking_flow.state.clear()
    await cl.Message(
        content="❌ Booking flow cancelled. You're back with Aria.",
        actions=[
            cl.Action(name="book", label="📅 Book Appointment", payload={"intent": "book"}),
            cl.Action(name="explore", label="✨ Explore Services", payload={"intent": "explore"}),
            cl.Action(name="hours", label="⏰ Opening Hours", payload={"intent": "hours"}),
        ],
    ).send()
