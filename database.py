import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

load_dotenv()


def _resolve_database_url() -> str:
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION_STRING")
    if not database_url:
        raise RuntimeError("DATABASE_URL (or POSTGRES_CONNECTION_STRING) is not set")

    if database_url.startswith("postgres://"):
        return "postgresql+asyncpg://" + database_url[len("postgres://"):]

    if database_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + database_url[len("postgresql://"):]

    return database_url


DATABASE_URL = _resolve_database_url()
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
