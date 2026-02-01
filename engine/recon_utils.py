"""Utility functions for fetching and keying SF Open Data."""

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


def fetch_dataset(url: str, limit: int = 50000) -> List[Dict[str, Any]]:
    """Fetch JSON dataset from SODA API.

    Args:
        url: SODA API endpoint URL.
        limit: Maximum records to return.

    Returns:
        List of record dicts.

    Raises:
        requests.HTTPError: On non-2xx response.
    """
    dataset_name = url.split("/")[-1].split(".")[0]
    logger.info("Fetching dataset: %s", dataset_name)

    resp = requests.get(url, params={"$limit": limit}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def make_parcel_key(block: Optional[str], lot: Optional[str]) -> Optional[str]:
    """Create a canonical block-lot key for parcel lookup.

    Args:
        block: Block identifier.
        lot: Lot identifier.

    Returns:
        Key string "block-lot" or None if either field is missing.
    """
    block = (block or "").strip()
    lot = (lot or "").strip()
    if not block or not lot:
        return None
    return f"{block}-{lot}"
