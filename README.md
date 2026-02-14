# SF Recon Engine — Data-Driven Distress Intelligence

A municipal-grade intelligence engine that identifies distressed and potentially vacant residential parcels across San Francisco. Integrates public datasets, geospatial boundaries, and a weighted distress scoring model. Built for operational clarity, modularity, and real-world deployment.

---

## Features

- **Multi-source data fusion** — 311 blight cases, DBI NOVs, DBI complaints (abatement), parcels, land use
- **Weighted distress scoring** — Parcel-level NOVs and complaints, tract-level 311 signals
- **Neighborhood diversification** — Top results span all SF neighborhoods, not just high-complaint areas
- **Zero external dependencies** — Uses Python stdlib only (urllib, json)
- **Optional HUD USPS integration** — Tract-level vacancy data when `HUD_API_KEY` is set

---

## Quick Start

```bash
# Clone and run
git clone https://github.com/joshuacybercert-source/-SF-Recon-Engine-Data-Driven-.git
cd -SF-Recon-Engine-Data-Driven-
python main.py
```

Output: `output/top100.txt` — ranked list of 100 distressed residential parcels.

---

## Sample Output

```
Top 100 distressed parcels (residential only, all SF):
--------------------------------------------------------------------------------
 1. Score 723.90 | 3553-022 | 1941 Mission St | Mission | NOVs: 73 | Complaints: 196 | 311: 1843
 2. Score 696.40 | 3570-002 | 520 South Van Ness Av | Mission | NOVs: 31 | Complaints: 225 | 311: 1843
 3. Score 688.40 | 3568-003 | 528 Valencia St | Mission | NOVs: 29 | Complaints: 213 | 311: 1843
 4. Score 556.80 | 3703-028 | 74 06th St | South of Market | NOVs: 118 | Complaints: 346 | 311: 886
 ...
```

---

## Architecture

```
main.py
  └── engine/
      ├── ingest.py    # Fetch from DataSF SODA API, optional HUD USPS
      ├── normalize.py # Unify schemas → parcel-centric records
      └── score.py     # Weighted scoring + neighborhood diversification
```

| Module      | Responsibility                                      |
|-------------|------------------------------------------------------|
| **ingest**  | Paginated API calls, blight keyword filtering        |
| **normalize** | Parcel aggregation, residential filter, 311/neighborhood mapping |
| **score**   | Distress formula (NOV×1.0 + Complaints×0.5 + 311×0.3), diversification |

---

## Data Sources

| Source | Description |
|--------|--------------|
| **311 blight** | Graffiti, abandoned vehicles, encampments (DataSF) |
| **DBI NOVs** | Notices of Violation (parcel-level) |
| **DBI complaints** | Abatement-related inspections (block/lot) |
| **Parcels** | Active/retired parcel base |
| **Land use** | Residential filter (res units, restype) |
| **HUD USPS** *(optional)* | Tract-level vacancy; set `HUD_API_KEY` |

---

## Requirements

- Python 3.9+
- No pip dependencies (stdlib only)

---

## Optional: HUD USPS Vacancy Data

Register at [HUD User](https://www.huduser.gov/portal/datasets/usps.html), create an API token, then:

```bash
export HUD_API_KEY=your-token-here
python main.py
```

---

## Tech Stack

Python 3 · REST APIs · DataSF (Socrata) · Data normalization · Weighted scoring · Geospatial aggregation

---

## License

MIT
