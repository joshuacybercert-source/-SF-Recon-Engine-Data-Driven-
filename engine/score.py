"""
Tract-level distress scoring: rank parcels by NOV count, 311 complaints, and area signals.
"""
from typing import List


def score_parcels(clean: List[dict]) -> List[dict]:
    """
    Score each parcel by dystress indicators.
    Higher score = more distressed.
    """
    # Weight: NOVs are direct parcel-level (1.0), 311 is tract-level (0.3)
    W_NOV = 1.0
    W_311 = 0.3

    scored = []
    for p in clean:
        nov = p.get("nov_count", 0) or 0
        c311 = p.get("case_311_count", 0) or 0
        score = (nov * W_NOV) + (c311 * W_311)
        out = dict(p)
        out["distress_score"] = round(score, 2)
        scored.append(out)

    # Sort by distress_score descending
    scored.sort(key=lambda x: x["distress_score"], reverse=True)
    return scored
