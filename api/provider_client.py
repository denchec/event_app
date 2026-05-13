import os

import requests
from dotenv import load_dotenv

load_dotenv()
PROVIDER_API_TOKEN = os.getenv("PROVIDER_API_TOKEN")
EVENTS_PROVIDER_BASE_URL = os.getenv("EVENTS_PROVIDER_BASE_URL")


class EventsProviderClient:
    async def get_events(
            self,
            date_from: str,
    ):
        url = f'{EVENTS_PROVIDER_BASE_URL}/api/events/'
        headers = {'x-api-key': PROVIDER_API_TOKEN}
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
        headers = {'x-api-key': PROVIDER_API_TOKEN}

        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

        return response.json()['seats']
