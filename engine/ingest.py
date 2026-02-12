"""
SODA API ingestion for SF municipal datasets.
"""
import json
import urllib.parse
import urllib.request

BASE = "https://data.sfgov.org/resource"
# App token improves rate limits; optional per Socrata docs
HEADERS = {"Accept": "application/json"}


def _fetch_soda(dataset_id: str, limit: int = 50000, offset: int = 0, **params) -> list:
    """Fetch JSON from a SODA dataset with optional SoQL params."""
    url = f"{BASE}/{dataset_id}.json"
    qs = [f"$limit={limit}", f"$offset={offset}"]
    for k, v in params.items():
        qs.append(f"${k}={urllib.parse.quote(str(v))}")
    url += "?" + "&".join(qs)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def _fetch_all_soda(dataset_id: str, page_size: int = 50000, **params) -> list:
    """Paginate through entire dataset (SODA max 50k/request)."""
    out, offset = [], 0
    while True:
        batch = _fetch_soda(dataset_id, limit=page_size, offset=offset, **params)
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return out


BLIGHT_KEYWORDS = frozenset({
    "abandoned", "vehicle", "graffiti", "encampment", "homeless", "illegal",
    "posting", "postings", "damaged", "property", "vacant", "lot", "blight",
})


def fetch_311_blight(limit: int = 50000, years_back: int = 2) -> list:
    """311 cases: blight-related (graffiti, abandoned vehicles, encampments, etc.)."""
    try:
        # Filter by date to keep dataset manageable
        from datetime import datetime, timedelta
        since = (datetime.now() - timedelta(days=365 * years_back)).strftime("%Y-%m-%dT00:00:00")
        where = f"requested_datetime >= '{since}'"
        # Single batch (50k max); pagination would need multiple requests
        rows = _fetch_soda("vw6y-z8j6", limit=limit, where=where)
        out = []
        for r in rows:
            text = " ".join(
                str(x).lower() for x in (
                    r.get("service_name") or "",
                    r.get("service_subtype") or "",
                    r.get("service_details") or "",
                ) if x
            )
            if any(kw in text for kw in BLIGHT_KEYWORDS):
                out.append(r)
        return out
    except Exception as e:
        print(f"311 fetch warning: {e}")
        return []


def fetch_dbi_novs() -> list:
    """DBI Notice of Violation records (nbtm-fbw5) - all SF (50k batch)."""
    try:
        return _fetch_soda("nbtm-fbw5", limit=50000)
    except Exception as e:
        print(f"DBI NOV fetch warning: {e}")
        return []


def fetch_parcel_base() -> list:
    """Parcels – Active and Retired (acdm-wktn) - single batch for speed."""
    try:
        return _fetch_soda("acdm-wktn", limit=50000)
    except Exception as e:
        print(f"Parcel fetch warning: {e}")
        return []


def fetch_all() -> dict:
    """Fetch all SF datasets; returns raw dict for downstream processing."""
    print("Fetching 311 blight cases...")
    cases_311 = fetch_311_blight()
    print(f"  Got {len(cases_311)} 311 cases")

    print("Fetching DBI NOVs...")
    novs = fetch_dbi_novs()
    print(f"  Got {len(novs)} NOVs")

    print("Fetching parcel base...")
    parcels = fetch_parcel_base()
    print(f"  Got {len(parcels)} parcels")

    return {"311": cases_311, "dbi_novs": novs, "parcels": parcels}
