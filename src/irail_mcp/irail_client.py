"""iRail API client for fetching Belgian railway data."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx

BASE_URL = "https://api.irail.be/v1"
USER_AGENT = "irail-mcp/0.1.0 (github.com/anthropics/irail-mcp)"
RATE_LIMIT = 3  # requests per second
RATE_LIMIT_DELAY = 1.0 / RATE_LIMIT  # delay between requests


class RateLimiter:
    """Simple rate limiter to respect iRail API limits."""

    def __init__(self, requests_per_second: float):
        self.delay = 1.0 / requests_per_second
        self.last_request = 0.0

    async def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        import time

        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self.last_request = time.time()


class iRailClient:
    """Client for interacting with the iRail API."""

    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.rate_limiter = RateLimiter(RATE_LIMIT)

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """Make a rate-limited request to the iRail API."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        await self.rate_limiter.wait()

        url = f"{BASE_URL}{path}"
        params = kwargs.pop("params", {})
        params.setdefault("format", "json")
        params.setdefault("lang", "en")

        try:
            response = await self.client.request(
                method, url, params=params, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise ValueError(
                    "Rate limit exceeded. iRail API allows 3 requests/second."
                )
            elif e.response.status_code == 404:
                raise ValueError("Station or resource not found.")
            elif e.response.status_code >= 500:
                raise ValueError(
                    f"iRail API server error ({e.response.status_code}). Please try again later."
                )
            raise

    async def get_liveboard(
        self,
        station: str,
        datetime_obj: datetime | None = None,
        arrival: bool = False,
        lang: str = "en",
    ) -> dict[str, Any]:
        """Get departures or arrivals for a station.

        Args:
            station: Station name or URI
            datetime_obj: Specific datetime (default: now)
            arrival: If True, get arrivals; else get departures
            lang: Language code

        Returns:
            Liveboard data with departures/arrivals.
        """
        if datetime_obj is None:
            datetime_obj = datetime.now()

        # Format: ddmmyy and hhmm
        date_str = datetime_obj.strftime("%d%m%y")
        time_str = datetime_obj.strftime("%H%M")

        params = {
            "station": station,
            "date": date_str,
            "time": time_str,
            "arrdep": "arrival" if arrival else "departure",
            "lang": lang,
        }

        return await self._request("GET", "/liveboard/", params=params)

    async def find_connections(
        self,
        from_station: str,
        to_station: str,
        datetime_obj: datetime | None = None,
        arrival_mode: bool = False,
        lang: str = "en",
    ) -> dict[str, Any]:
        """Find connections between two stations.

        Args:
            from_station: Starting station name or URI
            to_station: Destination station name or URI
            datetime_obj: Specific datetime (default: now)
            arrival_mode: If True, arrive at destination at this time; else depart from origin
            lang: Language code

        Returns:
            Connection data with multiple route options.
        """
        if datetime_obj is None:
            datetime_obj = datetime.now()

        date_str = datetime_obj.strftime("%d%m%y")
        time_str = datetime_obj.strftime("%H%M")

        params = {
            "from": from_station,
            "to": to_station,
            "date": date_str,
            "time": time_str,
            "timeSel": "depart" if not arrival_mode else "arrive",
            "lang": lang,
        }

        return await self._request("GET", "/connections/", params=params)

    async def get_vehicle(
        self,
        vehicle_id: str,
        datetime_obj: datetime | None = None,
        lang: str = "en",
    ) -> dict[str, Any]:
        """Get details about a specific train vehicle.

        Args:
            vehicle_id: Train ID (e.g., "BE.NMBS.IC1234" or just "IC1234")
            datetime_obj: Specific date (default: today)
            lang: Language code

        Returns:
            Vehicle data with all stops and current status.
        """
        if datetime_obj is None:
            datetime_obj = datetime.now()

        date_str = datetime_obj.strftime("%d%m%y")

        params = {
            "id": vehicle_id,
            "date": date_str,
            "lang": lang,
        }

        return await self._request("GET", "/vehicle/", params=params)

    async def get_disturbances(self, lang: str = "en") -> dict[str, Any]:
        """Get current network disturbances and planned works.

        Args:
            lang: Language code

        Returns:
            Dictionary with disturbances and planned works.
        """
        return await self._request("GET", "/disturbances/", params={"lang": lang})
