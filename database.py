import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

load_dotenv()

POSTGRES_DATABASE_NAME = os.getenv("POSTGRES_DATABASE_NAME")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = (f"postgresql+asyncpg://{POSTGRES_USERNAME}:"
                f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:"
                f"{POSTGRES_PORT}/{POSTGRES_DATABASE_NAME}")
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
