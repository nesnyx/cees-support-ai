from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PG_DATABASE_URL = os.getenv("PG_DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, 
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with SessionLocal() as session:
        yield session



sync_database_url = DATABASE_URL.replace("+asyncmy", "+pymysql")
sync_engine = create_engine(sync_database_url)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


