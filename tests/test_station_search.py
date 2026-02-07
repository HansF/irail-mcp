"""Tests for offline station search."""

import pytest

from irail_mcp.station_search import search_stations, _normalize, _strip_accents


class TestNormalization:
    """Test text normalization functions."""

    def test_strip_accents_basic(self):
        assert _strip_accents("Liège") == "Liege"

    def test_strip_accents_multiple(self):
        assert _strip_accents("Bruxelles-Schérbéek") == "Bruxelles-Scherbeek"

    def test_strip_accents_no_change(self):
        assert _strip_accents("Brussels") == "Brussels"

    def test_normalize_casefold_and_accents(self):
        assert _normalize("Liège") == "liege"

    def test_normalize_preserves_hyphens(self):
        assert _normalize("Gent-Sint-Pieters") == "gent-sint-pieters"


class TestStationSearch:
    """Test station search functionality."""

    def test_search_by_exact_name(self):
        results = search_stations("Aalst")
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert "Aalst" in names

    def test_search_case_insensitive(self):
        results = search_stations("aalst")
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert "Aalst" in names

    def test_search_accent_insensitive(self):
        """Searching 'Liege' should match 'Liège'."""
        results = search_stations("Liege")
        assert len(results) >= 1
        # At least one result should have Liège in the name
        found = any("Liège" in r["name"] or "Liege" in r["name"] for r in results)
        assert found, f"Expected Liège station, got: {[r['name'] for r in results]}"

    def test_search_french_alternative(self):
        """Searching 'Bruxelles' should find Brussels stations via alternative_fr."""
        results = search_stations("Bruxelles")
        assert len(results) >= 1

    def test_search_dutch_alternative(self):
        """Searching 'Alost' should find Aalst via alternative_fr."""
        results = search_stations("Alost")
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert "Aalst" in names

    def test_search_partial_name(self):
        """Substring matching should work."""
        results = search_stations("Gent")
        assert len(results) >= 1

    def test_search_empty_query(self):
        results = search_stations("")
        assert results == []

    def test_search_whitespace_only(self):
        results = search_stations("   ")
        assert results == []

    def test_search_no_results(self):
        results = search_stations("xyznonexistent12345")
        assert results == []

    def test_result_has_expected_keys(self):
        results = search_stations("Brussels")
        assert len(results) >= 1
        station = results[0]
        assert "uri" in station
        assert "name" in station
        assert "longitude" in station
        assert "latitude" in station
        assert "country_code" in station
        # Internal field should not be exposed
        assert "_search_text" not in station

    def test_search_loads_many_stations(self):
        """Sanity check: searching a very common letter returns many results."""
        results = search_stations("a")
        assert len(results) > 50
