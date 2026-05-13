from typing import Annotated

from fastapi import APIRouter, Depends, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_events_paginated, get_event_details
from api.models import Event
from api.provider_client import EventsProviderClient
from api.schemas import GetEventResponse, EventOut, RegisterOnEventRequest
from api.sync_service import run_sync_once_with_session
from database import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    return {'status': 'ok'}


@router.post("/sync/trigger")
async def sync_events(
        db: AsyncSession = Depends(get_db)
):
    return await run_sync_once_with_session(db)


@router.get("/events", response_model=GetEventResponse)
async def get_events(
        events: Event = Depends(get_events_paginated)
):
    return events


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event_by_id(
        event_details: Event = Depends(get_event_details)
):
    return event_details


@router.get("/events/{event_id}/seats")
async def get_event_seats(
        event_id: Annotated[str, Path(title="The ID of the event to get")],
):
    event_seats = await EventsProviderClient().get_event_seats(event_id)

    return {
        "event_id": event_id,
        'available_seats': event_seats
    }


@router.post("/tickets")
async def register_on_event(
       register_info : Annotated[RegisterOnEventRequest, Body()],
):
    return await EventsProviderClient().register_on_event(register_info)