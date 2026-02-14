# -SF-Recon-Engine-Data-Driven-
A municipal‑grade intelligence engine that identifies distressed and potentially vacant residential parcels across San Francisco by integrating public datasets, geospatial boundaries, and a tract‑level distress scoring model. Designed for operational clarity, modularity, and real‑world deployment.

## Data sources
- **311 blight cases** – graffiti, abandoned vehicles, encampments, etc.
- **DBI NOVs** – Notices of Violation
- **DBI complaints** – abatement-related inspections (block/lot)
- **HUD USPS vacancy** (optional) – tract-level vacant-address data; set `HUD_API_KEY` to enable
- **Obituaries** – not available in SF open data; would require court probate records or third-party sources
