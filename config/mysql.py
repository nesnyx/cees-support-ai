from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+asyncmy://bara:kodecesar1234@localhost:3306/cees_ai"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,  # <-- TAMBAHAN PALING KRUSIAL
    expire_on_commit=False, # <-- Praktik terbaik untuk async, mencegah error setelah commit
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with SessionLocal() as session:
        yield session


