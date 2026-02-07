#!/usr/bin/env python3
"""Fetch station data from iRail/stations repository and convert to JSON.

Downloads the authoritative stations.csv from GitHub and produces a curated
stations.json for bundling inside the package.

Usage:
    python scripts/update_stations.py
"""

import csv
import json
import sys
import urllib.request
from pathlib import Path

STATIONS_CSV_URL = (
    "https://raw.githubusercontent.com/iRail/stations/master/stations.csv"
)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "src" / "irail_mcp" / "data" / "stations.json"


def fetch_csv(url: str) -> str:
    """Download the stations CSV."""
    req = urllib.request.Request(url, headers={"User-Agent": "irail-mcp/update-stations"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_stations(csv_text: str) -> list[dict]:
    """Parse CSV into a list of station dicts with only the fields we need."""
    reader = csv.DictReader(csv_text.splitlines())
    stations = []
    for row in reader:
        station = {
            "uri": row.get("URI", ""),
            "name": row.get("name", ""),
            "alternative_fr": row.get("alternative-fr", ""),
            "alternative_nl": row.get("alternative-nl", ""),
            "alternative_de": row.get("alternative-de", ""),
            "alternative_en": row.get("alternative-en", ""),
            "longitude": row.get("longitude", ""),
            "latitude": row.get("latitude", ""),
            "country_code": row.get("country-code", ""),
        }
        # Only include stations with a name
        if station["name"]:
            stations.append(station)
    return stations


def main() -> None:
    print(f"Fetching stations from {STATIONS_CSV_URL} ...")
    csv_text = fetch_csv(STATIONS_CSV_URL)

    stations = parse_stations(csv_text)
    print(f"Parsed {len(stations)} stations")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, indent=2)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
