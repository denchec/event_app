from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.provider_client import EventsProviderClient
from database import get_db


async def get_events(
        date_from: str,
        page: int = 1,
        page_size: int = 20,
        db: AsyncSession = Depends(get_db)
):
    events = await EventsProviderClient().events(date_from)

    pass
