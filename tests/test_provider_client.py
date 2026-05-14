from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import requests

from api.provider_client import EventsProviderClient
from api.schemas import RegisterOnEventRequest


@pytest.mark.asyncio
async def test_get_events_collects_all_pages():
    client = EventsProviderClient()

    first_response = Mock(spec=httpx.Response)
    first_response.status_code = 200
    first_response.json.return_value = {
        "results": [{"id": "event-1"}],
        "next": "https://provider.example/api/events/?page=2",
    }

    second_response = Mock(spec=httpx.Response)
    second_response.status_code = 200
    second_response.json.return_value = {
        "results": [{"id": "event-2"}],
        "next": None,
    }

    async_client = AsyncMock()
    async_client.get = AsyncMock(side_effect=[first_response, second_response])

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = async_client

    with patch("api.provider_client.httpx.AsyncClient", return_value=context_manager):
        events = await client.get_events("2026-01-01T00:00:00Z")

    assert events == [{"id": "event-1"}, {"id": "event-2"}]
    assert async_client.get.await_count == 2


@pytest.mark.asyncio
async def test_get_event_seats_returns_seats_list():
    client = EventsProviderClient()

    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"seats": ["A1", "A2"]}

    async_client = AsyncMock()
    async_client.get = AsyncMock(return_value=response)

    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = async_client

    with patch("api.provider_client.httpx.AsyncClient", return_value=context_manager):
        seats = await client.get_event_seats("event-1")

    assert seats == ["A1", "A2"]


@pytest.mark.asyncio
async def test_register_on_event_returns_ticket_id():
    client = EventsProviderClient()
    request_data = RegisterOnEventRequest(
        event_id="event-1",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        seat="A1",
    )

    response = Mock(spec=requests.Response)
    response.status_code = 201
    response.json.return_value = {"ticket_id": "ticket-42"}

    with patch("api.provider_client.requests.post", return_value=response) as mock_post:
        ticket_id = await client.register_on_event(request_data)

    assert ticket_id == "ticket-42"
    assert mock_post.called


@pytest.mark.asyncio
async def test_delete_ticket_returns_provider_response():
    client = EventsProviderClient()

    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {"success": True}

    with patch("api.provider_client.requests.delete", return_value=response):
        result = await client.delete_ticket("event-1", "ticket-1")

    assert result == {"success": True}


def test_validate_httpx_response_raises_runtime_error_for_known_code():
    client = EventsProviderClient()
    response = Mock(spec=httpx.Response)
    response.status_code = 404
    response.text = "not found"

    with pytest.raises(RuntimeError) as exc:
        client._validate_httpx_response(response, expected_codes={200})

    assert "Not Found (404)" in str(exc.value)
    assert "not found" in str(exc.value)


def test_validate_requests_response_raises_runtime_error_for_unknown_code():
    client = EventsProviderClient()
    response = Mock(spec=requests.Response)
    response.status_code = 418
    response.text = "teapot"
    response.raise_for_status.side_effect = requests.HTTPError("teapot")

    with pytest.raises(RuntimeError) as exc:
        client._validate_requests_response(response, expected_codes={200})

    assert "Request failed with status code 418" in str(exc.value)
    assert "teapot" in str(exc.value)
