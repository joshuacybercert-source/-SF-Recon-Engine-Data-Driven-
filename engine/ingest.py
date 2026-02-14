"""
SODA API ingestion for SF municipal datasets.
Also supports optional HUD USPS vacant-address data (requires HUD_API_KEY).
Obituaries/death records: not available in SF open data; would require
court probate records or third-party sources.
"""
import json
import os
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


def fetch_land_use() -> list:
    """SF Land Use (fdfd-xptc) - existing_use, restype, res units for residential filter."""
    try:
        return _fetch_all_soda("fdfd-xptc", page_size=50000)
    except Exception as e:
        print(f"Land use fetch warning: {e}")
        return []


def fetch_dbi_complaints() -> list:
    """DBI complaints (gm2e-bten) – abatement-related; has block/lot, date_abated."""
    try:
        return _fetch_all_soda("gm2e-bten", page_size=50000)
    except Exception as e:
        print(f"DBI complaints fetch warning: {e}")
        return []


def fetch_hud_usps_vacancy() -> list:
    """
    HUD USPS vacant-address data by census tract (requires HUD_API_KEY).
    Returns tract-level vacancy rates; join via tract GEOID.
    Register at https://www.huduser.gov/portal/datasets/usps.html
    """
    token = os.environ.get("HUD_API_KEY")
    if not token:
        return []
    try:
        # SF county FIPS: state 06, county 075
        url = "https://www.huduser.gov/hudapi/public/uspsncwm?type=1&stateid=06"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results") or []
        # Filter to SF county (FIPS 075); STCNTY = state+county e.g. 06075
        sf = [r for r in results if str(r.get("COUNTY_GEOID", "")) == "075" or str(r.get("STCNTY", "")) == "6075"]
        return sf if sf else results
    except Exception as e:
        print(f"HUD USPS fetch warning: {e}")
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

    print("Fetching land use (residential filter)...")
    land_use = fetch_land_use()
    print(f"  Got {len(land_use)} land use records")

    print("Fetching DBI complaints (abatement-related)...")
    dbi_complaints = fetch_dbi_complaints()
    print(f"  Got {len(dbi_complaints)} DBI complaints")

    hud_usps = []
    if os.environ.get("HUD_API_KEY"):
        print("Fetching HUD USPS vacancy (tract-level)...")
        hud_usps = fetch_hud_usps_vacancy()
        print(f"  Got {len(hud_usps)} SF tracts")
    else:
        print("  (HUD USPS skipped; set HUD_API_KEY to enable)")

    return {
        "311": cases_311,
        "dbi_novs": novs,
        "dbi_complaints": dbi_complaints,
        "parcels": parcels,
        "land_use": land_use,
        "hud_usps_tracts": hud_usps,
    }
