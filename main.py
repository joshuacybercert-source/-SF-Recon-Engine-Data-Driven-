from engine.ingest import fetch_all
from engine.normalize import normalize_all
from engine.score import score_parcels

def run():
    raw = fetch_all()
    clean = normalize_all(raw)
    scored = score_parcels(clean)
    print("Top 20 parcels:")
    for row in scored[:20]:
        print(row)

if __name__ == "__main__":
    run()
