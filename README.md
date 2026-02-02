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

## High-Value Signals To Add

- Utility shutoff or low-usage signals (water, electric, gas delinquency)
- Code enforcement and nuisance history (repeat violations, abatement, debris)
- Tax delinquency and liens (unpaid taxes, mechanics liens, probate)

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

## Security Posture + Wi-Fi Health Tool

This repo also includes a small local-only GUI that checks basic security posture
and Wi-Fi health on Windows/macOS/Linux. It does not scan networks or perform
offensive actions.

```bash
python security_posture_app.py
```

Checks include:
- Wi-Fi encryption and signal strength (Windows; limited info on macOS/Linux)
- Firewall status
- OS update recency (Windows)
- Password policy and admin group review (Windows/Linux)
- Disk encryption status (BitLocker/FileVault)
- Defender real-time protection (Windows)

Exports:
- JSON (always available)
- HTML (always available)
- PDF (requires `reportlab`)

### Packaging (optional)

Build a standalone executable with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed security_posture_app.py
```

### Windows install + desktop icon

This script builds the EXE (if missing), installs it under `%LOCALAPPDATA%`,
and creates a desktop shortcut:

```powershell
.\scripts\install_windows.ps1
```

### Custom app icon

Provide a PNG (recommended 256x256) and generate `assets/app.ico`:

```bash
python scripts/generate_icon.py --source "path\to\logo.png"
```

After that, rerun `.\scripts\install_windows.ps1` or `.\scripts\build_msi.ps1`.

### MSI installer (Windows)

1) Install WiX Toolset (v4 preferred)
2) Build the MSI:

```powershell
.\scripts\build_msi.ps1
```

Outputs `dist\SecurityPosture.msi`.

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
