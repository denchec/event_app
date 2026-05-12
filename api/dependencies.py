from api.provider_client import EventsProviderClient


async def get_events(
        date_from: str,
):
    events = await EventsProviderClient().get_events(date_from)

    return events
