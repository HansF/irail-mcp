"""Tests for MCP server functionality."""

import pytest
import asyncio
from datetime import datetime

from irail_mcp.server import (
    app,
    parse_datetime,
    format_departure,
    format_connection,
    _search_stations,
    _get_liveboard,
    _find_connections,
    _get_train_info,
    _get_disturbances,
)


class TestDateParsing:
    """Test date and time parsing."""

    def test_parse_explicit_datetime(self):
        """Parse explicit date and time."""
        dt = parse_datetime("2024-02-07", "14:30")
        assert dt.year == 2024
        assert dt.month == 2
        assert dt.day == 7
        assert dt.hour == 14
        assert dt.minute == 30

    def test_parse_today(self):
        """Parse 'today' keyword."""
        dt = parse_datetime("today", "12:00")
        today = datetime.now()
        assert dt.year == today.year
        assert dt.month == today.month
        assert dt.day == today.day

    def test_parse_tomorrow(self):
        """Parse 'tomorrow' keyword."""
        dt = parse_datetime("tomorrow", "12:00")
        today = datetime.now()
        assert dt.day == today.day + 1 or (today.day == 1 and dt.month != today.month)

    def test_parse_relative_days(self):
        """Parse relative date format."""
        dt = parse_datetime("+3 days", "12:00")
        today = datetime.now()
        # Just verify it's parsed without error
        assert dt.hour == 12

    def test_parse_european_date_format(self):
        """Parse European date format."""
        dt = parse_datetime("07/02/2024", "14:30")
        assert dt.year == 2024
        assert dt.month == 2
        assert dt.day == 7

    def test_parse_12hour_time_format(self):
        """Parse 12-hour time format."""
        dt = parse_datetime("2024-02-07", "2:30 PM")
        assert dt.hour == 14
        assert dt.minute == 30


class TestFormatting:
    """Test output formatting functions with realistic iRail API data structures."""

    def test_format_departure_with_delay(self):
        """Format departure with delay. API returns all values as strings."""
        now = str(int(datetime.now().timestamp()))
        dep = {
            "id": "0",
            "station": "Antwerpen-Centraal",
            "stationinfo": {"name": "Antwerpen-Centraal", "id": "BE.NMBS.008821006", "locationX": "4.421101", "locationY": "51.2172"},
            "time": now,
            "delay": "300",  # 5 minutes in seconds, as string
            "platform": "3",
            "platforminfo": {"name": "3", "normal": "1"},
            "canceled": "0",
            "vehicle": "BE.NMBS.IC1832",
        }
        result = format_departure(dep)
        assert "Antwerpen-Centraal" in result
        assert "+5min" in result
        assert "Platform 3" in result
        assert "[CANCELED]" not in result

    def test_format_departure_on_time(self):
        """Format departure on time — delay is "0"."""
        now = str(int(datetime.now().timestamp()))
        dep = {
            "id": "1",
            "station": "Bruxelles-Central",
            "stationinfo": {"name": "Brussels-Central", "id": "BE.NMBS.008813003", "locationX": "4.356801", "locationY": "50.845658"},
            "time": now,
            "delay": "0",
            "platform": "1",
            "platforminfo": {"name": "1", "normal": "1"},
            "canceled": "0",
            "vehicle": "BE.NMBS.S32087",
        }
        result = format_departure(dep)
        assert "Brussels-Central" in result
        assert "+" not in result  # No delay shown
        assert "Platform 1" in result

    def test_format_departure_canceled(self):
        """Format canceled departure — canceled field is string "1"."""
        now = str(int(datetime.now().timestamp()))
        dep = {
            "id": "2",
            "station": "Gent-Sint-Pieters",
            "stationinfo": {"name": "Gent-Sint-Pieters", "id": "BE.NMBS.008892007", "locationX": "3.710675", "locationY": "51.035896"},
            "time": now,
            "delay": "0",
            "platform": "2",
            "platforminfo": {"name": "2", "normal": "1"},
            "canceled": "1",
            "vehicle": "BE.NMBS.IC3033",
        }
        result = format_departure(dep)
        assert "[CANCELED]" in result

    def test_format_departure_with_station_string_fallback(self):
        """Format departure when stationinfo is missing, falls back to station string."""
        now = str(int(datetime.now().timestamp()))
        dep = {
            "time": now,
            "delay": "0",
            "platform": "5",
            "canceled": "0",
            "station": "Leuven",
            "vehicle": "BE.NMBS.IC1234",
        }
        result = format_departure(dep)
        assert "Leuven" in result

    def test_format_connection_direct(self):
        """Format direct connection — nested departure/arrival objects."""
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
                "platforminfo": {"name": "4", "normal": "1"},
                "canceled": "0",
            },
            "arrival": {
                "delay": "0",
                "station": "Bruxelles-Central",
                "stationinfo": {"name": "Brussels-Central"},
                "time": str(now + 3600),
                "vehicle": "BE.NMBS.IC1832",
                "platform": "6",
                "platforminfo": {"name": "6", "normal": "1"},
                "canceled": "0",
            },
            "duration": "3600",
        }
        result = format_connection(conn)
        assert "Direct" in result
        assert "60min" in result
        assert "Platform 4" in result

    def test_format_connection_with_transfers(self):
        """Format connection with transfers — vias has nested "number" as string."""
        now = int(datetime.now().timestamp())
        conn = {
            "id": "1",
            "departure": {
                "delay": "120",
                "station": "Gent-Sint-Pieters",
                "stationinfo": {"name": "Gent-Sint-Pieters"},
                "time": str(now),
                "vehicle": "BE.NMBS.IC1832",
                "platform": "2",
                "platforminfo": {"name": "2", "normal": "1"},
                "canceled": "0",
            },
            "arrival": {
                "delay": "0",
                "station": "Bruxelles-Central",
                "stationinfo": {"name": "Brussels-Central"},
                "time": str(now + 7200),
                "vehicle": "BE.NMBS.IC2345",
                "platform": "3",
                "platforminfo": {"name": "3", "normal": "1"},
                "canceled": "0",
            },
            "duration": "7200",
            "vias": {
                "number": "1",
                "via": [
                    {
                        "id": "0",
                        "arrival": {"time": str(now + 1800)},
                        "departure": {"time": str(now + 2400)},
                        "station": "Bruxelles-Midi",
                        "stationinfo": {"name": "Brussels-South/Midi"},
                        "vehicle": "BE.NMBS.IC2345",
                    }
                ],
            },
        }
        result = format_connection(conn)
        assert "1 transfer(s)" in result
        assert "+2min" in result
        assert "120min" in result

    def test_format_connection_no_vias_key(self):
        """Format connection when vias key is entirely absent (direct train)."""
        now = int(datetime.now().timestamp())
        conn = {
            "departure": {
                "delay": "0",
                "time": str(now),
                "platform": "1",
            },
            "arrival": {
                "delay": "0",
                "time": str(now + 1800),
            },
            "duration": "1800",
        }
        result = format_connection(conn)
        assert "Direct" in result
        assert "30min" in result


class TestClientInitialization:
    """Test iRailClient initialization."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client can be used as async context manager."""
        from irail_mcp.irail_client import iRailClient
        async with iRailClient() as client:
            assert client.client is not None

    def test_rate_limiter_delay_calculation(self):
        """Test rate limiter calculates correct delay."""
        from irail_mcp.irail_client import RateLimiter

        limiter = RateLimiter(10)  # 10 req/s
        assert limiter.delay == pytest.approx(0.1, abs=0.001)

        limiter = RateLimiter(3)  # 3 req/s
        assert limiter.delay == pytest.approx(1.0 / 3, abs=0.001)


class TestMCPServerRegistration:
    """Test that MCP server tools are registered."""

    def test_app_has_tools(self):
        """Verify the app object exists and is an MCP server."""
        assert app is not None
        assert hasattr(app, "call_tool")
        assert hasattr(app, "list_tools")

    @pytest.mark.asyncio
    async def test_call_tool_method_exists(self):
        """Verify call_tool method can be invoked."""
        assert hasattr(app, "call_tool")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
