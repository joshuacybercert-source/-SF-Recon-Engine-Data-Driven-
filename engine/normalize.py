"""
Unify schemas from 311, DBI NOVs, Parcels into a single parcel-centric view.
"""
from collections import defaultdict
from typing import List




def _parcel_key(block: str, lot: str) -> str:
    """Normalize block-lot into a parcel identifier."""
    b = (block or "").strip().zfill(4)
    l = (lot or "").strip().upper()
    return f"{b}-{l}"


def _mapblklot_to_parcel_key(mapblklot: str) -> str | None:
    """Convert Land Use mapblklot to parcel_key. Supports '1186006'->'1186-006' and '1186/006'."""
    if not mapblklot:
        return None
    s = str(mapblklot).strip().upper()
    if "/" in s:
        parts = s.split("/", 1)
        if len(parts) == 2:
            return _parcel_key(parts[0], parts[1])
    # Concatenated: block (4 digits) + lot (rest)
    if len(s) >= 7:
        return f"{s[:4]}-{s[4:]}"
    return None


def _is_residential(land_use_record: dict) -> bool:
    """True if parcel has residential use (res units > 0 or residential land use)."""
    res = float(land_use_record.get("res") or 0)
    landuse = (land_use_record.get("landuse") or "").upper()
    restype = (land_use_record.get("restype") or "").upper()
    if res > 0:
        return True
    if landuse in ("RESIDENT", "MIXRES"):
        return True
    if restype in ("SINGLE", "FLATS", "APTS", "CONDO", "SRO"):
        return True
    return False


def _norm_addr(r: dict) -> str:
    """Build normalized address from address components."""
    parts = []
    for k in ("street_number", "street_name", "street_suffix", "unit"):
        v = r.get(k)
        if v:
            parts.append(str(v).strip())
    return " ".join(parts) if parts else ""


def normalize_all(raw: dict, residential_only: bool = True) -> List[dict]:
    """
    Unify raw data into parcel-level records.
    Each record: parcel_id, block, lot, address, nov_count, case_311_count, neighborhood, etc.
    If residential_only=True, filter to parcels with residential use (Land Use data).
    """
    novs = raw.get("dbi_novs", [])
    cases_311 = raw.get("311", [])
    dbi_complaints = raw.get("dbi_complaints", [])
    parcels = raw.get("parcels", [])
    land_use = raw.get("land_use", [])
    hud_tracts = raw.get("hud_usps_tracts", [])

    # Build set of residential parcel_ids from Land Use
    residential_parcels = set()
    if residential_only and land_use:
        for r in land_use:
            if _is_residential(r):
                pk = _mapblklot_to_parcel_key(r.get("mapblklot"))
                if pk:
                    residential_parcels.add(pk)

    # Aggregate NOVs by parcel (block, lot)
    parcel_data = defaultdict(lambda: {"nov_count": 0, "complaint_count": 0, "address": "", "neighborhood": "", "zipcode": "", "supervisor_district": ""})

    for r in novs:
        block = r.get("block") or r.get("block_id")
        lot = r.get("lot") or r.get("lot_id")
        if not block or not lot:
            continue
        pk = _parcel_key(block, lot)
        parcel_data[pk]["parcel_id"] = pk
        parcel_data[pk]["block"] = block
        parcel_data[pk]["lot"] = lot
        parcel_data[pk]["nov_count"] += 1
        if not parcel_data[pk]["address"]:
            parcel_data[pk]["address"] = _norm_addr(r) or f"{r.get('street_number', '')} {r.get('street_name', '')}".strip()
        if not parcel_data[pk]["neighborhood"]:
            parcel_data[pk]["neighborhood"] = r.get("neighborhoods_analysis_boundaries") or r.get("neighborhood") or ""
        if not parcel_data[pk]["zipcode"]:
            parcel_data[pk]["zipcode"] = r.get("zipcode") or ""
        if not parcel_data[pk]["supervisor_district"]:
            parcel_data[pk]["supervisor_district"] = r.get("supervisor_district") or ""

    # Aggregate DBI complaints (abatement-related) by parcel
    for r in dbi_complaints:
        block = r.get("block")
        lot = r.get("lot")
        if not block or not lot:
            continue
        pk = _parcel_key(block, lot)
        if pk not in parcel_data:
            addr = _norm_addr(r) or f"{r.get('street_number', '')} {r.get('street_name', '')}".strip()
            parcel_data[pk] = {"parcel_id": pk, "block": block, "lot": lot, "nov_count": 0, "complaint_count": 0, "address": addr, "neighborhood": "", "zipcode": r.get("zip_code", ""), "supervisor_district": ""}
        parcel_data[pk]["complaint_count"] += 1
        if not parcel_data[pk].get("address"):
            parcel_data[pk]["address"] = _norm_addr(r) or f"{r.get('street_number', '')} {r.get('street_name', '')}".strip()

    # Aggregate 311 by neighborhood and supervisor district
    hood_311 = defaultdict(int)
    district_311 = defaultdict(int)
    for r in cases_311:
        hood = (
            r.get("analysis_neighborhood")
            or r.get("neighborhoods_analysis_boundaries")
            or r.get("neighborhoods_sffind_boundaries")
            or r.get("neighborhood")
            or ""
        )
        district = r.get("supervisor_district") or ""
        if hood:
            hood_311[str(hood)] += 1
        if district:
            district_311[str(district)] += 1

    # Add/update parcel records from parcels dataset (if we have block/lot)
    for r in parcels:
        block = r.get("block") or r.get("block_num") or r.get("blklot", "").split("/")[0] if r.get("blklot") else ""
        lot = r.get("lot") or r.get("lot_num") or (r.get("blklot", "").split("/")[-1] if r.get("blklot") else "")
        if block and lot:
            pk = _parcel_key(block, lot)
            if pk not in parcel_data:
                parcel_data[pk] = {"parcel_id": pk, "block": block, "lot": lot, "nov_count": 0, "complaint_count": 0, "address": "", "neighborhood": "", "zipcode": "", "supervisor_district": ""}
            parcel_data[pk]["parcel_id"] = pk
            parcel_data[pk]["block"] = block
            parcel_data[pk]["lot"] = lot
            if not parcel_data[pk]["address"]:
                parcel_data[pk]["address"] = r.get("address") or r.get("addr") or ""
            if not parcel_data[pk]["neighborhood"]:
                parcel_data[pk]["neighborhood"] = r.get("neighborhoods_analysis_boundaries") or r.get("neighborhood") or ""
            if not parcel_data[pk]["zipcode"]:
                parcel_data[pk]["zipcode"] = r.get("zipcode") or ""

    # Attach 311 counts and filter to residential if requested
    out = []
    for pk, d in parcel_data.items():
        if residential_only and residential_parcels and pk not in residential_parcels:
            continue
        d["case_311_count"] = hood_311.get(d["neighborhood"], 0) or district_311.get(str(d.get("supervisor_district", "")), 0)
        out.append(dict(d))

    return out
