"""Data models for iRail API responses."""

from datetime import datetime
from pydantic import BaseModel, Field


class Station(BaseModel):
    """Represents a Belgian railway station."""

    id: str
    uri: str
    name: str
    standardname: str
    country_code: str | None = None
    latitude: float
    longitude: float
    avg_stop_times: int | None = None
    linking_points: str | None = None


class Departure(BaseModel):
    """Represents a departure from a station."""

    id: str
    time: int  # Unix timestamp
    delay: int | None = 0
    platform: str | None = None
    platformchange: bool | None = False
    canceled: int | None = 0
    type: str = "P"  # P = passenger train
    vehicle: str  # Train ID (e.g., "BE.NMBS.IC1234")
    vehicle_uri: str
    destination: str
    destination_uri: str
    route: list[dict] | None = None
    alerts: list[str] | None = None

    def time_formatted(self) -> str:
        """Return formatted departure time."""
        dt = datetime.fromtimestamp(self.time)
        return dt.strftime("%H:%M")

    def delay_str(self) -> str:
        """Return formatted delay."""
        if not self.delay:
            return "On time"
        return f"{self.delay} min delay"


class Connection(BaseModel):
    """Represents a connection/route between two stations."""

    id: str
    departure: int  # Unix timestamp
    arrival: int  # Unix timestamp
    duration: int  # Seconds
    transfers: int
    vias: list[dict] | None = None
    alerts: list[str] | None = None


class Vehicle(BaseModel):
    """Represents a train vehicle with its details."""

    id: str
    uri: str
    name: str
    vehicle_type: str | None = None
    delay: int | None = 0
    platform: str | None = None
    platformchange: bool | None = False
    canceled: bool | None = False
    stops: list[dict] | None = None


class Disturbance(BaseModel):
    """Represents a network disturbance or planned work."""

    id: str
    title: str
    description: str | None = None
    link: str | None = None
    type: str  # "disturbance" or "planned"
    severity: str | None = None
    timestamp: int | None = None  # Unix timestamp
