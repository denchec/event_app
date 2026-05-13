from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from api.models import EventTicket
from api.routes import (
    delete_ticket,
    get_event_seats,
    health_check,
    register_on_event,
    seats_cache,
)
from api.schemas import RegisterOnEventRequest


@pytest.fixture(autouse=True)
def clear_seats_cache():
    seats_cache.clear()
    yield
    seats_cache.clear()


@pytest.mark.asyncio
async def test_health_check_returns_ok_status():
    result = await health_check()
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_event_seats_returns_cached_value():
    event_id = "event-1"
    seats_cache[event_id] = {
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=60),
        "seats": ["A1", "A2"],
    }

    with patch("api.routes.EventsProviderClient") as mock_client_cls:
        result = await get_event_seats(event_id)

    assert result == {"event_id": event_id, "available_seats": ["A1", "A2"]}
    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_get_event_seats_loads_from_provider_and_caches():
    event_id = "event-2"

    mock_client = AsyncMock()
    mock_client.get_event_seats = AsyncMock(return_value=["B1", "B2"])

    with patch("api.routes.EventsProviderClient", return_value=mock_client):
        result = await get_event_seats(event_id)

    assert result == {"event_id": event_id, "available_seats": ["B1", "B2"]}
    assert seats_cache[event_id]["seats"] == ["B1", "B2"]


@pytest.mark.asyncio
async def test_register_on_event_raises_conflict_when_seat_unavailable():
    db = AsyncMock()
    request_data = RegisterOnEventRequest(
        event_id="event-1",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        seat="A9",
    )

    mock_client = AsyncMock()
    mock_client.get_event_seats = AsyncMock(return_value=["A1", "A2"])

    with patch("api.routes.EventsProviderClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc:
            await register_on_event(request_data, db)

    assert exc.value.status_code == 409
    assert exc.value.detail == "The seat is already taken"


@pytest.mark.asyncio
async def test_register_on_event_creates_ticket_when_missing_in_db():
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.add = Mock()

    request_data = RegisterOnEventRequest(
        event_id="event-1",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        seat="A1",
    )

    mock_client = AsyncMock()
    mock_client.get_event_seats = AsyncMock(return_value=["A1", "A2"])
    mock_client.register_on_event = AsyncMock(return_value="ticket-42")

    with patch("api.routes.EventsProviderClient", return_value=mock_client):
        result = await register_on_event(request_data, db)

    assert result == {"ticket_id": "ticket-42"}
    db.add.assert_called_once()
    added_ticket = db.add.call_args[0][0]
    assert isinstance(added_ticket, EventTicket)
    assert added_ticket.id == "ticket-42"
    assert added_ticket.event_id == "event-1"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_ticket_raises_not_found_when_absent_in_db():
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await delete_ticket("ticket-404", db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "There is no registration for this ticket"


@pytest.mark.asyncio
async def test_delete_ticket_calls_provider_and_removes_ticket():
    db = AsyncMock()
    ticket = EventTicket(id="ticket-1", event_id="event-1")
    db.get = AsyncMock(return_value=ticket)

    mock_client = AsyncMock()
    mock_client.delete_ticket = AsyncMock(return_value={"success": True})

    with patch("api.routes.EventsProviderClient", return_value=mock_client):
        result = await delete_ticket("ticket-1", db)

    assert result == {"success": True}
    mock_client.delete_ticket.assert_awaited_once_with("event-1", "ticket-1")
    db.delete.assert_awaited_once_with(ticket)
    db.commit.assert_awaited_once()
