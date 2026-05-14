from collections.abc import AsyncIterator

from api.provider_client import EventsProviderClient


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, date_from: str):
        self._client = client
        self._date_from = date_from

    def __aiter__(self) -> AsyncIterator[dict]:
        return _EventsPaginatorIterator(self._client, self._date_from)


class _EventsPaginatorIterator:
    def __init__(self, client: EventsProviderClient, date_from: str):
        self._client = client
        self._date_from = date_from
        self._next_page_url: str | None = None
        self._page_results: list[dict] = []
        self._result_index = 0
        self._is_first_page = True
        self._is_finished = False

    async def __anext__(self) -> dict:
        while self._result_index >= len(self._page_results):
            if self._is_finished or (
                not self._is_first_page and self._next_page_url is None
            ):
                raise StopAsyncIteration

            data = await self._client.get_events_page(
                date_from=self._date_from if self._is_first_page else None,
                next_page_url=self._next_page_url,
            )

            self._page_results = data.get("results", [])
            self._result_index = 0
            self._next_page_url = data.get("next")
            self._is_first_page = False
            self._is_finished = self._next_page_url is None and not self._page_results

        event = self._page_results[self._result_index]
        self._result_index += 1
        return event
