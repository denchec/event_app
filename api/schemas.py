from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class GetEventRequest(BaseModel):
    date_from: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    city: str
    address: str


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    place: PlaceOut
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class GetEventResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventOut]
