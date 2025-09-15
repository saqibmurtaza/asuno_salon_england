# asuna_salon_backend/database.py
import os
from supabase import Client, create_client
from fastapi_backend.settings import settings
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# NOTE: Assuming your settings file contains these keys for Supabase
supabase_url = settings.NEXT_PUBLIC_SUPABASE_URL
supabase_key = settings.NEXT_PUBLIC_SUPABASE_ANON_KEY
supabase_secret_key = settings.SUPABASE_SECRET_KEY

# Initialize Supabase clients (optional, but good practice for full integration)
# Use the public key for client-side operations and the secret key for privileged operations
supabase_public: Client = create_client(supabase_url, supabase_key)
supabase_admin: Client = create_client(supabase_url, supabase_secret_key)

# Replace 'postgresql' with 'postgresql+asyncpg' to use the asyncpg driver
connection_string = str(settings.DIRECT_URL.replace('postgresql', 'postgresql+asyncpg'))

# Configure async engine with production optimizations
async_engine = create_async_engine(
    connection_string,
    echo=True, # Set to False in production
    future=True,
    # Crucial for PgBouncer/Supavisor transaction mode: disable prepared statement cache
    connect_args={"statement_cache_size": 0},
    
    # Recommended for pooled connections:
    pool_pre_ping=True, # Pings connections before use
    pool_recycle=3600 # Recycles connections after 1 hour
)

# Define an async sessionmaker
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Function to create database tables
async def create_db_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependency to get an async session for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
