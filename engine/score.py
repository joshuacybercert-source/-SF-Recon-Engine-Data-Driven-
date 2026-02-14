"""
Tract-level distress scoring: rank parcels by NOV count, 311 complaints, and area signals.
"""
from collections import defaultdict
from typing import List


def diversify_by_neighborhood(scored: List[dict], total: int = 100, per_hood: int = 8) -> List[dict]:
    """Take top parcels from each neighborhood so results span all of SF."""
    by_hood = defaultdict(list)
    for p in scored:
        hood = p.get("neighborhood") or p.get("supervisor_district") or "Unknown"
        if hood:
            by_hood[hood].append(p)
    for hood in by_hood:
        by_hood[hood].sort(key=lambda x: x["distress_score"], reverse=True)
    out = []
    taken = 0
    while taken < total and by_hood:
        for hood in list(by_hood.keys()):
            if by_hood[hood] and taken < total:
                out.append(by_hood[hood].pop(0))
                taken += 1
            if not by_hood[hood]:
                del by_hood[hood]
    out.sort(key=lambda x: x["distress_score"], reverse=True)
    return out[:total]


def score_parcels(clean: List[dict]) -> List[dict]:
    """
    Score each parcel by distress indicators.
    Higher score = more distressed.
    """
    # Weights: NOVs and complaints are parcel-level; 311 is tract-level
    W_NOV = 1.0
    W_COMPLAINT = 0.5   # DBI complaints (abatement-related)
    W_311 = 0.3

    scored = []
    for p in clean:
        nov = p.get("nov_count", 0) or 0
        complaint = p.get("complaint_count", 0) or 0
        c311 = p.get("case_311_count", 0) or 0
        score = (nov * W_NOV) + (complaint * W_COMPLAINT) + (c311 * W_311)
        out = dict(p)
        out["distress_score"] = round(score, 2)
        scored.append(out)

    # Sort by distress_score descending
    scored.sort(key=lambda x: x["distress_score"], reverse=True)
    return scored
