# SF Parcel-Event Reconciliation

**San Francisco Parcel-Event Reconciliation Engine** — Matches SF parcels (block-lot) with events from city open datasets (permits, code violations, 311, etc.) and returns event counts per parcel.

Built following the **4 pillars of coding**:
- **Readability** — Type hints, docstrings, clear naming
- **Maintainability** — Modular design, single responsibility, logging
- **Testability** — Dependency injection, pure functions, unit tests
- **Scalability** — Configurable datasets, efficient data structures

## Features

- Loads parcel data from [SF Open Data](https://data.sfgov.org/)
- Matches events from permits, code violations, 311, business, fire, env, nuisance
- Outputs event counts per parcel with top-N summary

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Options:
- `-v, --verbose` — Enable debug logging
- `-n, --top N` — Show top N parcels (default: 20)

## Project Structure

```
sf-recom/
├── engine/
│   ├── __init__.py
│   ├── datasets.py    # Dataset URLs and config
│   ├── parcels.py     # Parcel loading
│   ├── events.py      # Event matching logic
│   ├── recon_utils.py # Fetch and key utilities
│   └── zipmap.py      # ZIP geospatial lookup
├── tests/
│   ├── test_events.py
│   ├── test_parcels.py
│   └── test_recon_utils.py
├── main.py
├── requirements.txt
└── README.md
```

## Data Sources

- **Parcels**: [Address Points](https://data.sfgov.org/Geographic-Locations-and-Boundaries/Address-Points/3mea-di5p)
- **Events**: SF Open Data SODA API (permits, code, 311, business, fire, env, nuisance)

## License

MIT
