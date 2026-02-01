"""Tests for parcels module."""

from engine.recon_utils import make_parcel_key


class TestLoadParcels:
    """Tests for parcel key format used in parcels module."""

    def test_parcel_key_format(self) -> None:
        """Verify parcel keys follow block-lot format."""
        assert make_parcel_key("1234", "56") == "1234-56"
