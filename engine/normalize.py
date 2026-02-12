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


def _norm_addr(r: dict) -> str:
    """Build normalized address from address components."""
    parts = []
    for k in ("street_number", "street_name", "street_suffix", "unit"):
        v = r.get(k)
        if v:
            parts.append(str(v).strip())
    return " ".join(parts) if parts else ""


def normalize_all(raw: dict) -> List[dict]:
    """
    Unify raw data into parcel-level records.
    Each record: parcel_id, block, lot, address, nov_count, case_311_count, neighborhood, etc.
    """
    novs = raw.get("dbi_novs", [])
    cases_311 = raw.get("311", [])
    parcels = raw.get("parcels", [])

    # Aggregate NOVs by parcel (block, lot)
    parcel_data = defaultdict(lambda: {"nov_count": 0, "address": "", "neighborhood": "", "zipcode": "", "supervisor_district": ""})

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

    # Add parcel records from parcels dataset (if we have block/lot)
    for r in parcels:
        block = r.get("block") or r.get("block_num") or r.get("blklot", "").split("/")[0] if r.get("blklot") else ""
        lot = r.get("lot") or r.get("lot_num") or (r.get("blklot", "").split("/")[-1] if r.get("blklot") else "")
        if block and lot:
            pk = _parcel_key(block, lot)
            if pk not in parcel_data:
                parcel_data[pk]["parcel_id"] = pk
                parcel_data[pk]["block"] = block
                parcel_data[pk]["lot"] = lot
                parcel_data[pk]["nov_count"] = 0
                parcel_data[pk]["address"] = r.get("address") or r.get("addr") or ""
                parcel_data[pk]["neighborhood"] = r.get("neighborhoods_analysis_boundaries") or r.get("neighborhood") or ""
                parcel_data[pk]["zipcode"] = r.get("zipcode") or ""

    # Attach 311 counts by neighborhood (fallback: supervisor district)
    out = []
    for pk, d in parcel_data.items():
        d["case_311_count"] = hood_311.get(d["neighborhood"], 0) or district_311.get(str(d.get("supervisor_district", "")), 0)
        out.append(dict(d))

    return out
