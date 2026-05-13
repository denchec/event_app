import os

import httpx
import requests
from dotenv import load_dotenv

from api.schemas import RegisterOnEventRequest

load_dotenv()
HTTP_EVENTS_PROVIDER_URL = os.getenv("HTTP_EVENTS_PROVIDER_URL")
HTTPS_EVENTS_PROVIDER_URL = os.getenv("HTTPS_EVENTS_PROVIDER_URL")
PROVIDER_API_TOKEN = os.getenv("PROVIDER_API_TOKEN")


class EventsProviderClient:
    def _raise_for_known_http_error(self, status_code: int, response_text: str) -> None:
        errors = {
            301: "Redirect (301). Проверьте trailing slash в URL.",
            308: "Permanent Redirect (308). Проверьте trailing slash в URL.",
            400: "Bad Request (400). Некорректные данные или бизнес-ошибка.",
            401: "Unauthorized (401). Ошибка аутентификации.",
            404: "Not Found (404). Ресурс не найден.",
            429: "Too Many Requests (429). Превышен лимит запросов.",
            500: "Internal Server Error (500). Внутренняя ошибка сервера.",
        }
        message = errors.get(status_code)
        if message:
            raise RuntimeError(f"{message}\n{response_text}")

    def _validate_httpx_response(self, response: httpx.Response, expected_codes: set[int]) -> None:
        if response.status_code in expected_codes:
            return
        self._raise_for_known_http_error(response.status_code, response.text)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}") from exc
        raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

    def _validate_requests_response(self, response: requests.Response, expected_codes: set[int]) -> None:
        if response.status_code in expected_codes:
            return
        self._raise_for_known_http_error(response.status_code, response.text)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}") from exc
        raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

    async def get_events(
            self,
            date_from: str,
    ):
        url = f'{HTTP_EVENTS_PROVIDER_URL}/api/events/'
        headers = {'x-api-key': PROVIDER_API_TOKEN}
        params = {'changed_at': date_from}

        events = []
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            while True:
                response = await client.get(url=url, headers=headers, params=params)
                self._validate_httpx_response(response, expected_codes={200})

                data = response.json()
                events.extend(data['results'])

                if data['next'] is None:
                    break

                url = data['next']
                params = None

        return events

    async def get_event_seats(
            self,
            event_id: str
    ):
        url = f'{HTTP_EVENTS_PROVIDER_URL}/api/events/{event_id}/seats/'
        headers = {'x-api-key': PROVIDER_API_TOKEN}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url=url, headers=headers)

        self._validate_httpx_response(response, expected_codes={200})

        return response.json()['seats']

    async def register_on_event(
            self,
            register_info: RegisterOnEventRequest
    ):
        body = register_info.model_dump()
        event_id = body.pop("event_id")

        url = f'{HTTPS_EVENTS_PROVIDER_URL}/api/events/{event_id}/register/'  # HTTP request Permanently Redirected
        headers = {'x-api-key': PROVIDER_API_TOKEN}

        response = requests.post(url=url, headers=headers, json=body)

        self._validate_requests_response(response, expected_codes={200, 201})

        return response.json()["ticket_id"]

    async def delete_ticket(self, event_id: str, ticket_id: str):
        # HTTP request Permanently Redirected when using non-HTTPS provider URL.
        url = f"{HTTPS_EVENTS_PROVIDER_URL}/api/events/{event_id}/unregister/"
        headers = {"x-api-key": PROVIDER_API_TOKEN}
        body = {"ticket_id": ticket_id}

        response = requests.delete(url=url, headers=headers, json=body)

        self._validate_requests_response(response, expected_codes={200, 201})

        return response.json()
