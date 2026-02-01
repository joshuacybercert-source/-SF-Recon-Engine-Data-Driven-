"""Parcel loading and indexing module."""

import logging
from typing import Dict, Any

from .datasets import PARCEL_DATASET_URL, PARCEL_FIELDS
from .recon_utils import fetch_dataset, make_parcel_key

logger = logging.getLogger(__name__)


def load_parcels(url: str = PARCEL_DATASET_URL, limit: int = 50000) -> Dict[str, Dict[str, Any]]:
    """Load parcels from SF Open Data and index by block-lot key.

    Args:
        url: SODA API URL for the parcel dataset.
        limit: Max records to fetch.

    Returns:
        Dict mapping block-lot keys to parcel records.
    """
    logger.info("Loading parcel dataset...")
    data = fetch_dataset(url, limit=limit)

    parcels: Dict[str, Dict[str, Any]] = {}
    for entry in data:
        block = entry.get(PARCEL_FIELDS["block"])
        lot = entry.get(PARCEL_FIELDS["lot"])
        key = make_parcel_key(block, lot)
        if key:
            parcels[key] = entry

    logger.info("Loaded %d parcels", len(parcels))
    return parcels
