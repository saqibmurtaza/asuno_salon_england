from fastapi import FastAPI
from contextlib import asynccontextmanager
from asuno_salon_england.backend.database import create_db_tables
from fastapi.middleware.cors import CORSMiddleware
from asuno_salon_england.backend.models.booking_models import Booking, BookingCreate, BookingOut
from asuno_salon_england.backend.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from asuno_salon_england.backend.utils import get_service_duration, generate_time_slots
from asuno_salon_england.chainlit_frontend.opening_hours import OPENING_HOURS
import logging
from .agents.config_agents import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asuna_salon")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Asuna Salon backend...")
    logger.info("CREATING DATABASE TABLES...")
    await create_db_tables()
    logger.info("Database tables created successfully.")
    
    yield
    logger.info("Shutting down Asuna Salon backend...")

# FastAPI application
app = FastAPI(
    lifespan=lifespan,
    title="Asuna Salon Backend",
    version="1.0.0",
)

servers=[
        {
            "url": "http://localhost:8001",
            "description": "Local development server",
        },
        {
            "url": "https://your-backend-api.vercel.app",  # Replace with real domain if deployed
            "description": "Production server",
        }
    ]


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://curated-shop-ruby.vercel.app",
    "https://curated-shop-australia.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)


# --------- ENDPOINTS---------

@app.get("/")
async def root():
    return {"message": "Welcome to Asuna Salon API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/bookings", response_model=BookingOut)
async def create_booking(data: BookingCreate, db: AsyncSession = Depends(get_db)):
    """Create a new booking with a unique reference code."""
    base_ref = f"ASU-{data.date.strftime('%Y%m%d')}"
    result = await db.execute(select(Booking).where(Booking.date == data.date))
    bookings_today = result.scalars().all()
    suffix = len(bookings_today) + 1
    reference = f"{base_ref}-{suffix:03d}"

    new_booking = Booking(
        service=data.service,
        category=data.category,
        date=data.date,
        time=data.time,
        client_name=data.client_name,
        reference=reference,
    )
    db.add(new_booking)

    try:
        await db.commit()
        await db.refresh(new_booking)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not save booking: {str(e)}")

    return new_booking



@app.get("/bookings/available-times/{date}")
async def get_available_times(
    date: str, 
    service: str, 
    db: AsyncSession = Depends(get_db)):
    try:
        service_minutes = get_service_duration(service)
        check_date = datetime.strptime(date, "%Y-%m-%d").date()

        for _ in range(14):  # look up to 14 days ahead
            weekday = check_date.weekday()
            hours = OPENING_HOURS.get(weekday)

            if not hours:
                check_date += timedelta(days=1)
                continue

            all_slots = generate_time_slots(hours["start"], hours["end"], service_minutes)

            result = await db.execute(
                select(Booking.time).where(Booking.date == check_date)
            )
            booked = [row[0] for row in result.fetchall()]
            available = [t for t in all_slots if t not in booked]

            if available:
                return {"date": str(check_date), "available": available}

            check_date += timedelta(days=1)

        return {"date": None, "available": []}

    except Exception as e:
        # Never leak raw tracebacks
        return {"date": None, "available": [], "error": str(e)}

# --------- ENDPOINTS  ---------

app.get("/agent/config")
async def get_config():
    return {"config": config}

app.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    