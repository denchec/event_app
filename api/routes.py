from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_events
from api.models import Place, Event, SyncState
from api.utils import _parse_dt
from database import get_db

router = APIRouter()
SYNC_SOURCE = "events_provider"


@router.get("/health")
async def health_check():
    return {'status': 'ok'}


@router.get("/sync/trigger")
async def sync_events(
        events: list = Depends(get_events),
        db: AsyncSession = Depends(get_db)
):
    sync_state = await db.get(SyncState, SYNC_SOURCE)
    if sync_state is None:
        sync_state = SyncState(source=SYNC_SOURCE, sync_status="idle")
        db.add(sync_state)

    sync_state.sync_status = "running"
    sync_state.last_sync_time = datetime.now(timezone.utc)
    sync_state.last_error = None
    await db.commit()

    try:
        max_changed_at = sync_state.last_changed_at

        for event_data in events:
            place_data = event_data["place"]

            place = await db.get(Place, place_data["id"])
            if place is None:
                place = Place(id=place_data["id"])
                db.add(place)

            place.name = place_data["name"]
            place.city = place_data["city"]
            place.address = place_data["address"]
            place.seats_pattern = place_data["seats_pattern"]
            place.changed_at = _parse_dt(place_data["changed_at"])
            place.created_at = _parse_dt(place_data["created_at"])

            event = await db.get(Event, event_data["id"])
            if event is None:
                event = Event(id=event_data["id"])
                db.add(event)

            event.name = event_data["name"]
            event.place_id = place.id
            event.event_time = _parse_dt(event_data["event_time"])
            event.registration_deadline = _parse_dt(event_data["registration_deadline"])
            event.status = event_data["status"]
            event.number_of_visitors = event_data["number_of_visitors"]
            event.changed_at = _parse_dt(event_data["changed_at"])
            event.created_at = _parse_dt(event_data["created_at"])
            event.status_changed_at = _parse_dt(event_data["status_changed_at"])

            if max_changed_at is None or event.changed_at > max_changed_at:
                max_changed_at = event.changed_at

        sync_state.sync_status = "success"
        sync_state.last_changed_at = max_changed_at
        sync_state.last_error = None
        await db.commit()
    except Exception as exc:
        await db.rollback()

        failed_state = await db.get(SyncState, SYNC_SOURCE)
        if failed_state is None:
            failed_state = SyncState(source=SYNC_SOURCE)
            db.add(failed_state)

        failed_state.sync_status = "failed"
        failed_state.last_sync_time = datetime.now(timezone.utc)
        failed_state.last_error = str(exc)[:500]
        await db.commit()

        raise exc

    return
