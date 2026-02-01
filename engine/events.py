"""Event matching logic for parcel-event reconciliation."""

import logging
from collections import Counter
from typing import Callable, Dict, Optional

from .datasets import EVENT_DATASETS, PARCEL_FIELDS

logger = logging.getLogger(__name__)
from .recon_utils import fetch_dataset, make_parcel_key

BLOCK_FIELD = PARCEL_FIELDS["block"]
LOT_FIELD = PARCEL_FIELDS["lot"]


def match_events(
    parcels: Dict[str, object],
    datasets: Optional[Dict[str, str]] = None,
    fetch_fn: Optional[Callable[[str, int], list]] = None,
) -> Counter:
    """Count how many events from each dataset hit each parcel.

    Args:
        parcels: Dict of parcels keyed by block-lot.
        datasets: Optional dict of label -> URL. Defaults to EVENT_DATASETS.
        fetch_fn: Optional fetch function (url, limit) -> list. For testing.

    Returns:
        Counter of parcel keys with hit counts.
    """
    datasets = datasets or EVENT_DATASETS
    fetch_fn = fetch_fn or _default_fetch

    all_matches: list = []
    for label, url in datasets.items():
        try:
            data = fetch_fn(url, 50000)
        except Exception as e:
            logger.warning("Skipping dataset %s: %s", label, e)
            continue
        for entry in data:
            block = entry.get(BLOCK_FIELD)
            lot = entry.get(LOT_FIELD)
            key = make_parcel_key(block, lot)
            if key and key in parcels:
                all_matches.append(key)

    return Counter(all_matches)


def _default_fetch(url: str, limit: int) -> list:
    """Default fetch delegate."""
    return fetch_dataset(url, limit=limit)
