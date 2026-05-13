from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    seats_pattern = Column(String(255), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    events = relationship("Event", back_populates="place")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    place_id = Column(String(36), ForeignKey("places.id"), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    registration_deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False)
    number_of_visitors = Column(Integer, nullable=False, default=0)
    changed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    status_changed_at = Column(DateTime(timezone=True), nullable=False)

    place = relationship("Place", back_populates="events")


class EventTicket(Base):
    __tablename__ = "event_tickets"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(36), nullable=False)


class SyncState(Base):
    __tablename__ = "sync_state"

    source = Column(String(100), primary_key=True)
    last_sync_time = Column(DateTime(timezone=True), nullable=True)
    last_changed_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(20), nullable=False, default="idle")
    last_error = Column(String(500), nullable=True)

    changed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
