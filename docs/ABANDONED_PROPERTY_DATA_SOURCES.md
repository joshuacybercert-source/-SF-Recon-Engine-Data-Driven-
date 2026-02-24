# Public Data Sources for Abandoned / Vacant Properties

Reference for expanding the SF Recon Engine with additional signals. Includes DataSF SODA API endpoints and non-API sources.

---

## DataSF (SODA API) — Ready to Integrate

Base URL: `https://data.sfgov.org/resource/{dataset_id}.json`

Your engine already uses: `_fetch_soda()` and `_fetch_all_soda()` in `engine/ingest.py`. Parcel linkage uses `block` + `lot` → `parcel_key` (e.g. `1186-006`).

### 1. Assessor Historical Secured Property Tax Rolls
| Field | Value |
|-------|-------|
| **Dataset ID** | `wv5m-vpq2` |
| **API** | `https://data.sfgov.org/resource/wv5m-vpq2.json` |
| **Link** | [Assessor Historical Secured Property Tax Rolls](https://data.sfgov.org/Housing-and-Buildings/Assessor-Historical-Secured-Property-Tax-Rolls/wv5m-vpq2) |
| **Schema** | `parcel_number`, `block`, `lot`, `property_location`, `use_code`, `assessor_neighborhood`, `closed_roll_year` |
| **Use** | Join by block/lot; filter by `closed_roll_year` for latest. No direct delinquency flag—use for value/use context. |

### 2. Eviction Notices
| Field | Value |
|-------|-------|
| **Dataset ID** | `5cei-gny5` |
| **API** | `https://data.sfgov.org/resource/5cei-gny5.json` |
| **Link** | [Eviction Notices](https://data.sfgov.org/Housing-and-Buildings/Eviction-Notices/5cei-gny5) |
| **Schema** | Address, neighborhood, eviction type (e.g. non-payment, owner move-in), filing date |
| **Use** | Evictions → potential vacancy. May need geocoding or address matching to parcel; check for `block`/`lot` columns. |

### 3. Commercial Vacancy Tax Status (Prop D)
| Field | Value |
|-------|-------|
| **Dataset ID** | `iynh-ydf2` |
| **API** | `https://data.sfgov.org/resource/iynh-ydf2.json` |
| **Link** | [Map of Commercial Vacancy Tax Status](https://data.sfgov.org/Economy-and-Community/Map-of-Commercial-Vacancy-Tax-Status/iynh-ydf2) |
| **Use** | Commercial vacancy only; may have parcel/address for cross-reference. |

### 4. All Evictions for Non-Payment
| Field | Value |
|-------|-------|
| **Dataset ID** | `cy9b-iyif` |
| **Link** | [All Evictions for Non-Payment](https://data.sfgov.org/Housing-and-Buildings/all-evictions-for-non-payment/cy9b-iyif) |
| **Use** | Non-payment evictions → stronger vacancy signal. Check schema for parcel linkage. |

---

## SF Treasurer — Not on DataSF API

| Source | URL | Access |
|--------|-----|--------|
| **Delinquent Property Taxes** | [sftreasurer.org/property/delinquent-property-taxes](http://sftreasurer.org/property/delinquent-property-taxes) | Web list of parcels 3+ years delinquent. No public API; may require FOIA or data request. |
| **Commercial Vacancy Reporting** | [sftreasurer.org/report-vacant-commercial-property](https://sftreasurer.org/report-vacant-commercial-property) | Prop D commercial vacancy; self-reported. |

**Recommendation:** Contact SF Treasurer (support@sftreasurer.org) or DataSF (support@datasf.org) to request delinquent parcel list as open data.

---

## Vacant Building Registry (SF)

- **Remove from vacant list:** [sf.gov/remove-your-property-vacant-or-abandoned-building-list](https://www.sf.gov/remove-your-property-vacant-or-abandoned-building-list)
- SF maintains a vacant/abandoned building list via DBI Code Enforcement. **Not found as a public DataSF dataset.** Request via DataSF or DBI.

---

## Community / Third-Party

| Source | URL | Notes |
|--------|-----|-------|
| **VacanSee** | [vacansee.org](https://vacansee.org) | Maps commercial vacancies from Prop D tax data. Open-source; may have data export. |

---

## Integration Checklist for New Data Sources

1. **Parcel linkage:** Does the dataset have `block` and `lot`? If not, `parcel_number` or address → geocode or join via parcels/land use.
2. **Residential filter:** Your engine uses `land_use` (mapblklot) for residential-only. New sources may need the same filter.
3. **Add to `ingest.py`:** New `fetch_*()` function using `_fetch_soda()` or `_fetch_all_soda()`.
4. **Add to `normalize.py`:** Aggregate new counts into `parcel_data` (e.g. `eviction_count`, `tax_delinquent`).
5. **Add to `score.py`:** Include new signals in distress formula (e.g. `eviction_count * 0.4`).

---

## Quick Reference: Current Engine Datasets

| Source | Dataset ID | Parcel Key |
|--------|------------|------------|
| 311 blight | `vw6y-z8j6` | neighborhood (tract-level) |
| DBI NOVs | `nbtm-fbw5` | block, lot |
| DBI complaints | `gm2e-bten` | block, lot |
| Parcels | `acdm-wktn` | block, lot |
| Land use | `fdfd-xptc` | mapblklot |
| HUD USPS | (API) | census tract |
