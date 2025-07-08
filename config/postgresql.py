from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text

import os
from dotenv import load_dotenv
load_dotenv()
# Ganti sesuai konfigurasi PostgreSQL kamu
DATABASE_URL = "postgresql+asyncpg://user_production:kodecesar1234@arisbara.cloud:3499/cees_db"

# Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Session
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base untuk deklarasi model
Base = declarative_base()

# Dependency FastAPI
async def get_db():
    async with async_session() as session:
        await session.execute(text("SET search_path TO data"))
        yield session