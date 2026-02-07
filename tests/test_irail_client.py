"""Tests for iRail client."""

import pytest
from datetime import datetime, timedelta

from irail_mcp.irail_client import iRailClient, RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter functionality."""
    limiter = RateLimiter(10)  # 10 requests per second

    import time
    start = time.time()

    # Make 5 requests with rate limiting
    for _ in range(5):
        await limiter.wait()

    elapsed = time.time() - start
    # Should take at least 0.4 seconds (4 intervals of 0.1s)
    assert elapsed >= 0.35


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client context manager."""
    async with iRailClient() as client:
        assert client.client is not None


@pytest.mark.asyncio
async def test_datetime_formatting():
    """Test datetime string formatting for API calls."""
    from irail_mcp.server import parse_datetime

    # Test with explicit date and time
    dt = parse_datetime("2024-02-07", "14:30")
    assert dt.year == 2024
    assert dt.month == 2
    assert dt.day == 7
    assert dt.hour == 14
    assert dt.minute == 30

    # Test with "today"
    dt = parse_datetime("today", "12:00")
    today = datetime.now()
    assert dt.year == today.year
    assert dt.month == today.month
    assert dt.day == today.day

    # Test with "tomorrow"
    dt = parse_datetime("tomorrow", "12:00")
    tomorrow = datetime.now() + timedelta(days=1)
    assert dt.day == tomorrow.day

    # Test with relative date
    dt = parse_datetime("+3 days", "12:00")
    future = datetime.now() + timedelta(days=3)
    assert dt.day == future.day


def test_format_departure():
    """Test departure formatting with realistic iRail API data."""
    from irail_mcp.server import format_departure

    now = str(int(datetime.now().timestamp()))
    dep = {
        "id": "0",
        "station": "Antwerpen-Centraal",
        "stationinfo": {
            "name": "Antwerpen-Centraal",
            "id": "BE.NMBS.008821006",
            "locationX": "4.421101",
            "locationY": "51.2172",
        },
        "time": now,
        "delay": "300",  # 5 minutes in seconds, as a string
        "platform": "3",
        "platforminfo": {"name": "3", "normal": "1"},
        "canceled": "0",
        "vehicle": "BE.NMBS.IC1832",
    }

    result = format_departure(dep)
    assert "to Antwerpen-Centraal" in result
    assert "(+5min)" in result
    assert "Platform 3" in result


def test_format_departure_on_time():
    """Test departure formatting when on time."""
    from irail_mcp.server import format_departure

    now = str(int(datetime.now().timestamp()))
    dep = {
        "id": "1",
        "station": "Bruxelles-Central",
        "stationinfo": {"name": "Brussels-Central"},
        "time": now,
        "delay": "0",
        "platform": "1",
        "canceled": "0",
        "vehicle": "BE.NMBS.S32087",
    }

    result = format_departure(dep)
    assert "to Brussels-Central" in result
    assert "(+" not in result  # No delay


def test_format_departure_canceled():
    """Test departure formatting when canceled — string "1"."""
    from irail_mcp.server import format_departure

    now = str(int(datetime.now().timestamp()))
    dep = {
        "id": "2",
        "station": "Gent-Sint-Pieters",
        "stationinfo": {"name": "Gent-Sint-Pieters"},
        "time": now,
        "delay": "0",
        "platform": "2",
        "canceled": "1",
        "vehicle": "BE.NMBS.IC3033",
    }

    result = format_departure(dep)
    assert "[CANCELED]" in result


def test_format_connection():
    """Test connection formatting with realistic nested iRail API data."""
    from irail_mcp.server import format_connection

    now = int(datetime.now().timestamp())
    conn = {
        "id": "0",
        "departure": {
            "delay": "0",
            "station": "Gent-Sint-Pieters",
            "stationinfo": {"name": "Gent-Sint-Pieters"},
            "time": str(now),
            "vehicle": "BE.NMBS.IC1832",
            "platform": "4",
            "canceled": "0",
        },
        "arrival": {
            "delay": "0",
            "station": "Bruxelles-Central",
            "stationinfo": {"name": "Brussels-Central"},
            "time": str(now + 3600),
            "vehicle": "BE.NMBS.IC1832",
            "platform": "6",
            "canceled": "0",
        },
        "duration": "3600",
    }

    result = format_connection(conn)
    assert "Direct" in result
    assert "60min" in result


if __name__ == "__main__":
    pytest.main([__file__])
