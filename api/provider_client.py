import os

import requests
from dotenv import load_dotenv

from api.schemas import RegisterOnEventRequest

load_dotenv()
HTTP_EVENTS_PROVIDER_URL = os.getenv("HTTP_EVENTS_PROVIDER_URL")
HTTPS_EVENTS_PROVIDER_URL = os.getenv("HTTPS_EVENTS_PROVIDER_URL")
EVENTS_PROVIDER_BASE_URL = os.getenv("EVENTS_PROVIDER_BASE_URL")


class EventsProviderClient:
    async def get_events(
            self,
            date_from: str,
    ):
        url = f'{EVENTS_PROVIDER_BASE_URL}/api/events/'
        headers = {'x-api-key': HTTP_EVENTS_PROVIDER_URL}
        params = {'changed_at': date_from}

        events = []
        while True:
            response = requests.get(url=url, headers=headers, params=params)

            if response.status_code != 200:
                raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

            data = response.json()
            events.extend(data['results'])

            if data['next'] is None:
                break

            url = data['next']

        return events

    async def get_event_seats(
            self,
            event_id: str
    ):
        url = f'{EVENTS_PROVIDER_BASE_URL}/api/events/{event_id}/seats/'
        headers = {'x-api-key': HTTP_EVENTS_PROVIDER_URL}

        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

        return response.json()['seats']

    async def register_on_event(
            self,
            register_info: RegisterOnEventRequest
    ):
        body = register_info.model_dump()
        event_id = body.pop("event_id")

        url = f'{HTTPS_EVENTS_PROVIDER_URL}/api/events/{event_id}/register/'  # HTTP request Permanently Redirected
        headers = {'x-api-key': HTTP_EVENTS_PROVIDER_URL}

        response = requests.post(url=url, headers=headers, json=body, allow_redirects=False)

        if response.status_code not in [200, 201]:
            raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

        return response.json()
