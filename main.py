from engine.ingest import fetch_all
from engine.normalize import normalize_all
from engine.score import score_parcels, diversify_by_neighborhood

# Neighborhoods containing "Sunset" or "Richmond" (e.g. Sunset/Parkside, Inner Sunset, Outer Richmond, Inner Richmond)
SUNSET_RICHMOND_KEYWORDS = ("sunset", "richmond")


def _filter_neighborhoods(parcels, keywords):
    """Filter parcels to neighborhoods whose names contain any of the keywords (case-insensitive)."""
    if not keywords:
        return parcels
    kw = tuple(k.lower() for k in keywords)
    return [p for p in parcels if any(k in (p.get("neighborhood") or "").lower() for k in kw)]


def run(neighborhood_filter=None):
    """
    Run the engine. If neighborhood_filter is a tuple of keywords (e.g. ("sunset", "richmond")),
    only parcels in matching neighborhoods are included.
    """
    raw = fetch_all()
    clean = normalize_all(raw)
    scored = score_parcels(clean)

    if neighborhood_filter:
        scored = _filter_neighborhoods(scored, neighborhood_filter)
        title = f"Top 100 distressed parcels (residential only, Sunset & Richmond):"
        out_path = "output/top100_sunset_richmond.txt"
    else:
        scored = diversify_by_neighborhood(scored, total=100, per_hood=8)
        title = "Top 100 distressed parcels (residential only, all SF):"
        out_path = "output/top100.txt"

    lines = [title, "-" * 80]
    for i, row in enumerate(scored[:100], 1):
        addr = row.get("address") or f"{row.get('block','')}-{row.get('lot','')}"
        line = f"{i:2}. Score {row.get('distress_score',0):.2f} | {row.get('parcel_id','')} | {addr} | {row.get('neighborhood','')} | NOVs: {row.get('nov_count',0)} | Complaints: {row.get('complaint_count',0)} | 311: {row.get('case_311_count',0)}"
        lines.append(line)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n" + "\n".join(lines))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--sunset-richmond":
        run(neighborhood_filter=SUNSET_RICHMOND_KEYWORDS)
    else:
        run()
