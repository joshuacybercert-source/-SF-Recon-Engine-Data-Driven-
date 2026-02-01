"""Tests for events module."""

from collections import Counter

import pytest

from engine.events import match_events


class TestMatchEvents:
    """Tests for match_events with injected fetch function."""

    def test_counts_events_for_matching_parcels(self) -> None:
        parcels = {"1234-56": {}, "9999-99": {}}
        datasets = {"test": "https://example.com/data.json"}

        def mock_fetch(url: str, limit: int) -> list:
            return [
                {"block": "1234", "lot": "56"},
                {"block": "1234", "lot": "56"},
                {"block": "9999", "lot": "99"},
            ]

        counts = match_events(parcels, datasets=datasets, fetch_fn=mock_fetch)
        assert counts == Counter({"1234-56": 2, "9999-99": 1})

    def test_ignores_events_for_unknown_parcels(self) -> None:
        parcels = {"1234-56": {}}
        datasets = {"test": "https://example.com/data.json"}

        def mock_fetch(url: str, limit: int) -> list:
            return [
                {"block": "1234", "lot": "56"},
                {"block": "9999", "lot": "99"},
            ]

        counts = match_events(parcels, datasets=datasets, fetch_fn=mock_fetch)
        assert counts == Counter({"1234-56": 1})

    def test_skips_dataset_on_fetch_error(self) -> None:
        parcels = {"1234-56": {}}
        datasets = {
            "fail": "https://example.com/fail.json",
            "ok": "https://example.com/ok.json",
        }

        def mock_fetch(url: str, limit: int) -> list:
            if "fail" in url:
                raise RuntimeError("Network error")
            return [{"block": "1234", "lot": "56"}]

        counts = match_events(parcels, datasets=datasets, fetch_fn=mock_fetch)
        assert counts == Counter({"1234-56": 1})
