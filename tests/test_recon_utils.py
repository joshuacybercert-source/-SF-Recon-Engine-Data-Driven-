"""Tests for recon_utils module."""

import pytest

from engine.recon_utils import make_parcel_key


class TestMakeParcelKey:
    """Tests for make_parcel_key."""

    def test_normal_input(self) -> None:
        assert make_parcel_key("1234", "56") == "1234-56"

    def test_strips_whitespace(self) -> None:
        assert make_parcel_key("  1234  ", "  56  ") == "1234-56"

    def test_missing_block_returns_none(self) -> None:
        assert make_parcel_key(None, "56") is None
        assert make_parcel_key("", "56") is None

    def test_missing_lot_returns_none(self) -> None:
        assert make_parcel_key("1234", None) is None
        assert make_parcel_key("1234", "") is None

    def test_both_empty_returns_none(self) -> None:
        assert make_parcel_key("", "") is None
        assert make_parcel_key(None, None) is None
