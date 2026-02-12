from engine.ingest import fetch_all
from engine.normalize import normalize_all
from engine.score import score_parcels

def run():
    raw = fetch_all()
    clean = normalize_all(raw)
    scored = score_parcels(clean)
    print("\nTop 100 distressed parcels (all SF):")
    print("-" * 80)
    for i, row in enumerate(scored[:100], 1):
        addr = row.get("address") or f"{row.get('block','')}-{row.get('lot','')}"
        print(f"{i:2}. Score {row.get('distress_score',0):.2f} | {row.get('parcel_id','')} | {addr} | {row.get('neighborhood','')} | NOVs: {row.get('nov_count',0)} | 311: {row.get('case_311_count',0)}")

if __name__ == "__main__":
    run()
