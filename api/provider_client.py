import os

import requests
from dotenv import load_dotenv

load_dotenv()
PROVIDER_API_TOKEN = os.getenv("PROVIDER_API_TOKEN")


class EventsProviderClient:
    async def events(
            self,
            date_from: str,
    ):
        url = 'http://events-provider.dev-2.python-labs.ru/api/events'
        headers = {'x-api-key': PROVIDER_API_TOKEN}
        params = {'changed_at': date_from}

        events = []
        while True:
            response = requests.get(url=url, headers=headers, params=params)
            data = response.json()

            if response.status_code != 200:
                raise RuntimeError(f"Request failed with status code {response.status_code}\n{response.text}")

            events.extend(data['results'])

            if data['next'] is None:
                break

            url = data['next']

        return events
