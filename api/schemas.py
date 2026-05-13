from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    seats_pattern: str


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


class RegisterOnEventRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=36)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    seat: str = Field(min_length=1, max_length=20)
