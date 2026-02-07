# iRail MCP Server

> **Disclaimer:** This project was vibe coded and is **not affiliated with or supported by [iRail vzw](https://hello.irail.be)**. Train data may be inaccurate or outdated. Always verify with official sources ([belgiantrain.be](https://www.belgiantrain.be) or the NMBS/SNCB app) before making travel decisions.

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that provides Belgian railway travel information via the [iRail API](https://api.irail.be).

## Features

- **Search Stations** - Find Belgian railway stations by name
- **Live Departures/Arrivals** - Real-time departure and arrival boards
- **Find Connections** - Route planning between stations with transfers
- **Train Information** - Detailed stops, delays, and platforms for a specific train
- **Network Disturbances** - Current disruptions and planned maintenance

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/HansF/irail-mcp.git
cd irail-mcp
uv venv && source .venv/bin/activate
uv pip install -e .
```

## Usage with Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "irail": {
      "command": "uvx",
      "args": ["irail-mcp"]
    }
  }
}
```

Then ask Claude things like:
- "What trains leave Brussels Central in the next hour?"
- "Find a route from Antwerp to Bruges at 2:30 PM tomorrow"
- "Are there any disruptions on the Belgian rail network?"
- "Show me details for train IC2240"

## Tools

### search_stations
Search for stations by name.
- `query` (required) - Station name or partial name
- `lang` (optional) - Language: en, nl, fr, de, it

### get_liveboard
Real-time departures or arrivals from a station.
- `station` (required) - Station name
- `date` (optional) - YYYY-MM-DD, "today", "tomorrow", "+2 days"
- `time` (optional) - HH:MM (24h)
- `arrival` (optional) - Show arrivals instead of departures
- `lang` (optional)

### find_connections
Find routes between two stations.
- `from_station` (required) - Departure station
- `to_station` (required) - Destination station
- `date`, `time`, `lang` (optional)
- `arrival_time` (optional) - If true, time is desired arrival time

### get_train_info
Detailed information about a specific train.
- `train_id` (required) - e.g. "IC1234" or "BE.NMBS.IC1234"
- `date`, `lang` (optional)

### get_disturbances
Current network disruptions and planned works.
- `lang` (optional)

## Running Tests

```bash
uv pip install -e ".[dev]"
python -m pytest tests/ -v
```

## API Compliance

- Rate limited to 3 requests/second per iRail guidelines
- Proper User-Agent header set
- 30-second timeout for slow responses

## License

MIT

## References

- [iRail API](https://api.irail.be) - [Documentation](https://docs.irail.be)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [NMBS/SNCB](https://www.belgiantrain.be)
