from agents import Runner, SQLiteSession
from collections import defaultdict
from .opening_hours import OPENING_HOURS
from .booking_flow import BookingFlow
from .salon_data import services
import chainlit as cl, httpx, os

os.environ["CHAINLIT_DISABLE_PERSISTENCE"] = "true"  # Force stateless mode for easier local testing

# Show a small startup message so you can see stateless mode is active
if not os.getenv("CHAINLIT_DB_URL"):
    print("Chainlit stateless mode: CHAINLIT_DB_URL is NOT set. Persistence disabled.")


# Global booking flow instance (1 per session)
booking_flow = BookingFlow()

API_BASE = "http://localhost:8000"  # backend running locally or deployed



@cl.on_chat_start
async def on_chat_start():
    # Each user session gets a unique session ID for the agent's memory
    session_id = cl.user_session.get("id")
    cl.user_session.set("agent_session", SQLiteSession(session_id))
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
    agent_session = cl.user_session.get("agent_session")
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

    # Otherwise → forward to marketing agent Aria
    result = await Runner.run(
        aria,
        user_input,
        session=agent_session,
        run_config=config,
    )
    await cl.Message(content=result.final_output).send()
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
