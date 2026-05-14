from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_event_details, get_events_paginated
from api.models import Event, EventTicket
from api.provider_client import EventsProviderClient
from api.schemas import EventOut, GetEventResponse, RegisterOnEventRequest
from api.sync_service import run_sync_once_with_session
from database import get_db

router = APIRouter()

SEATS_CACHE_TTL_SECONDS = 30
seats_cache: dict[str, dict[str, object]] = {}


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/sync/trigger")
async def sync_events(db: Annotated[AsyncSession, Depends(get_db)]):
    return await run_sync_once_with_session(db)


@router.get("/events", response_model=GetEventResponse)
async def get_events(events: Annotated[Event, Depends(get_events_paginated)]):
    return events


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event_by_id(event_details: Annotated[Event, Depends(get_event_details)]):
    return event_details


@router.get("/events/{event_id}/seats")
async def get_event_seats(
    event_id: Annotated[str, Path(title="The ID of the event to get")],
):
    now = datetime.now(timezone.utc)
    cached = seats_cache.get(event_id)

    if cached is not None:
        expires_at = cached["expires_at"]
        if isinstance(expires_at, datetime) and now < expires_at:
            return {
                "event_id": event_id,
                "available_seats": cached["seats"],
            }

    event_seats = await EventsProviderClient().get_event_seats(event_id)

    seats_cache[event_id] = {
        "expires_at": now + timedelta(seconds=SEATS_CACHE_TTL_SECONDS),
        "seats": event_seats,
    }

    return {"event_id": event_id, "available_seats": event_seats}


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def register_on_event(
    register_info: Annotated[RegisterOnEventRequest, Body()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event_seats = await EventsProviderClient().get_event_seats(register_info.event_id)
    if register_info.seat not in event_seats:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The seat is already taken",
        )

    ticket_id = await EventsProviderClient().register_on_event(register_info)

    ticket = await db.get(EventTicket, ticket_id)
    if ticket is None:
        ticket = EventTicket(id=ticket_id, event_id=register_info.event_id)
        db.add(ticket)
        await db.commit()

    return {"ticket_id": ticket_id}


@router.delete("/tickets/{ticket_id}")
async def delete_ticket(
    ticket_id: Annotated[str, Path(title="The ID of the event to get")],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await db.get(EventTicket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no registration for this ticket",
        )

    response_info = await EventsProviderClient().delete_ticket(
        ticket.event_id, ticket_id
    )

    if response_info:
        await db.delete(ticket)
        await db.commit()

    return {"success": True}
