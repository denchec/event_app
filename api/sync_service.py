from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Event, Place, SyncState
from api.provider_client import EventsProviderClient
from api.utils import _parse_dt
from database import SessionLocal

SYNC_SOURCE = "events_provider"
FIRST_SYNC_CHANGED_AT = "2000-01-01"


async def _run_sync(db: AsyncSession) -> dict:
    sync_state = await db.get(SyncState, SYNC_SOURCE)
    if sync_state is None:
        sync_state = SyncState(source=SYNC_SOURCE, sync_status="idle")
        db.add(sync_state)
        await db.flush()

    if sync_state.sync_status == "running":
        return {
            "sync_status": "running",
            "last_sync_time": sync_state.last_sync_time,
            "last_changed_at": sync_state.last_changed_at,
            "skipped": True,
        }

    date_from = (
        sync_state.last_changed_at.date().isoformat()
        if sync_state.last_changed_at is not None
        else FIRST_SYNC_CHANGED_AT
    )

    sync_state.sync_status = "running"
    sync_state.last_sync_time = datetime.now(timezone.utc)
    sync_state.last_error = None
    await db.commit()

    try:
        events = await EventsProviderClient().get_events(date_from)
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

        return {
            "sync_status": sync_state.sync_status,
            "last_sync_time": sync_state.last_sync_time,
            "last_changed_at": sync_state.last_changed_at,
            "processed_events": len(events),
            "date_from": date_from,
            "skipped": False,
        }
    except Exception as exc:
        await db.rollback()

        failed_state = await db.get(SyncState, SYNC_SOURCE)
        if failed_state is None:
            failed_state = SyncState(source=SYNC_SOURCE, sync_status="failed")
            db.add(failed_state)

        failed_state.sync_status = "failed"
        failed_state.last_sync_time = datetime.now(timezone.utc)
        failed_state.last_error = str(exc)[:500]
        await db.commit()
        raise


async def run_sync_once() -> dict:
    async with SessionLocal() as db:
        return await _run_sync(db)


async def run_sync_once_with_session(db: AsyncSession) -> dict:
    return await _run_sync(db)
