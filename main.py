from engine.ingest import fetch_all
from engine.normalize import normalize_all
from engine.score import score_parcels, diversify_by_neighborhood

def run():
    raw = fetch_all()
    clean = normalize_all(raw)
    scored = score_parcels(clean)
    # Diversify so we get parcels from all SF neighborhoods, not just Mission
    scored = diversify_by_neighborhood(scored, total=100, per_hood=8)
    lines = ["Top 100 distressed parcels (residential only, all SF):", "-" * 80]
    for i, row in enumerate(scored[:100], 1):
        addr = row.get("address") or f"{row.get('block','')}-{row.get('lot','')}"
        line = f"{i:2}. Score {row.get('distress_score',0):.2f} | {row.get('parcel_id','')} | {addr} | {row.get('neighborhood','')} | NOVs: {row.get('nov_count',0)} | Complaints: {row.get('complaint_count',0)} | 311: {row.get('case_311_count',0)}"
        lines.append(line)
    out_path = "output/top100.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n" + "\n".join(lines))
    print(f"\nSaved to {out_path}")

if __name__ == "__main__":
    run()
