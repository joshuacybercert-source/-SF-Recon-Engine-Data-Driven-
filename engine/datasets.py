"""Dataset configuration for SF Open Data SODA API."""

from typing import Dict

# Base parcel dataset: Address Points (public, includes ZIP)
PARCEL_DATASET_URL: str = "https://data.sfgov.org/resource/3mea-di5p.json"

# Event datasets used for scoring parcels
EVENT_DATASETS: Dict[str, str] = {
    "permits": "https://data.sfgov.org/resource/i98e-djp9.json",
    "code": "https://data.sfgov.org/resource/wg3w-h783.json",
    "blight311": "https://data.sfgov.org/resource/vw6y-z8j6.json",
    "business": "https://data.sfgov.org/resource/g8m3-pdis.json",
    "fire": "https://data.sfgov.org/resource/4zuq-2cbe.json",
    "env": "https://data.sfgov.org/resource/gm2e-bten.json",
    "nuisance": "https://data.sfgov.org/resource/nbtm-fbw5.json",
}

# Field mappings for parcel records
PARCEL_FIELDS: Dict[str, str] = {
    "block": "block",
    "lot": "lot",
    "address": "address",
    "zipcode": "zipcode",
}
