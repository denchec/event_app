import pytest
from unittest.mock import AsyncMock

from api.events_paginator import EventsPaginator


@pytest.mark.asyncio
async def test_events_paginator_yields_events_from_all_pages():
    mock_client = AsyncMock()
    mock_client.get_events_page = AsyncMock(
        side_effect=[
            {
                "results": [{"id": "event-1"}],
                "next": "https://provider.example/api/events/?page=2",
            },
            {
                "results": [{"id": "event-2"}, {"id": "event-3"}],
                "next": None,
            },
        ]
    )

    events = []
    async for event in EventsPaginator(mock_client, "2026-01-01"):
        events.append(event)

    assert events == [{"id": "event-1"}, {"id": "event-2"}, {"id": "event-3"}]
    assert mock_client.get_events_page.await_count == 2


@pytest.mark.asyncio
async def test_events_paginator_finishes_on_empty_first_page():
    mock_client = AsyncMock()
    mock_client.get_events_page = AsyncMock(
        return_value={"results": [], "next": None}
    )

    events = []
    async for event in EventsPaginator(mock_client, "2026-01-01"):
        events.append(event)

    assert events == []
    assert mock_client.get_events_page.await_count == 1
