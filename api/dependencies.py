from typing import Annotated

from fastapi import Depends, Request, Path, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models import Event
from api.schemas import GetEventRequest, GetEventResponse, EventOut
from database import get_db


async def get_events_paginated(
    request: Request,
    query: Annotated[GetEventRequest, Depends()],
    db: AsyncSession = Depends(get_db),
):
    base_stmt = select(Event).options(selectinload(Event.place))
    if query.date_from is not None:
        base_stmt = base_stmt.where(Event.event_time >= query.date_from)

    base_stmt = base_stmt.order_by(Event.event_time.asc(), Event.id.asc())

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (query.page - 1) * query.page_size
    page_stmt = base_stmt.offset(offset).limit(query.page_size)
    items = (await db.execute(page_stmt)).scalars().all()

    has_previous = query.page > 1
    has_next = offset + query.page_size < total

    previous_url = (
        str(request.url.include_query_params(page=query.page - 1, page_size=query.page_size))
        if has_previous else None
    )
    next_url = (
        str(request.url.include_query_params(page=query.page + 1, page_size=query.page_size))
        if has_next else None
    )

    results = [EventOut.model_validate(event) for event in items]

    return GetEventResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results,
    )


async def get_event_details(
    event_id: Annotated[str, Path(title="The ID of the event to get")],
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).options(selectinload(Event.place)).where(Event.id == event_id)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event
