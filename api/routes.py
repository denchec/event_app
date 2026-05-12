from fastapi import APIRouter, Depends

from api.dependencies import get_events

router = APIRouter()


@router.get("/health")
async def health_check():
    return {'status': 'ok'}


@router.get("/events")
async def events(
        date_from: str,
        page: int = 1,
        page_size: int = 20
):
    return await get_events(date_from, page, page_size)
