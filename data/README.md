# Data Documentation

## Data Sources

This repository uses two input data streams:

1. **Actual irradiance and temperature**
   - Source: NASA POWER
   - Variables:
     - `ALLSKY_SFC_SW_DWN` → hourly Global Horizontal Irradiance (GHI), Wh/m²
     - `T2M` → temperature at 2 meters, °C

2. **Forecast irradiance**
   - Source: processed output exported from the Phase 1 baseline forecasting workflow
   - Variable:
   - `ghi_forecast_wh_m2` → forecasted hourly GHI, Wh/m²

The Phase 2 workflow combines both inputs on a shared hourly timestamp index tto have:
- timestamp
- ghi_actual_wh_m2
- ghi_forecast_wh_m2
- temperature (temp_c)

---

## Location

- **City:** Maroua, Cameroon
- **Latitude:** 10.6032
- **Longitude:** 14.3226

This location is used as a Sahelian stress-test case for solar variability and operational uncertainty.

---

## Time Handling/Convention
### Computational timezone
The internal master time basis in this repository is the original NASA POWER hourly **`LST`** convention.

Timestamps are kept timezone-naive inside the Phase 2 workflow to preserve consistency with the source irradiance series and the Phase 1 forecast artifact.

### Local interpretation timezone
For pvlib solar-position calculations only, timestamps are temporarily localized to **`Africa/Douala`** so that timezone-aware solar geometry can be computed.

### Indexing rule
All time-dependent series must share the same hourly datetime index:

- actual irradiance
- forecast irradiance
- PV AC power
- load
- battery state of charge
- curtailed energy
- unserved energy

This is a strict requirement for the simulation pipeline.

---

## Temporal Resolution

- **Resolution:** Hourly

The mini-grid case study is implemented at hourly resolution to remain consistent with both NASA POWER inputs and the Phase 1 forecasting workflow.

---

## Data Retrieval Strategy

### Actual irradiance
Actual irradiance is retrieved directly from NASA POWER or loaded from a processed NASA-derived file committed to this repository.

### Forecast irradiance
Forecast irradiance is imported as a processed artifact from the Phase 1 repository rather than re-training the forecasting model inside this repo. The artifact contains aligned hourly timestamps together with actual and forecasted GHI values.

Expected columns:
- time
- ghi_actual_wh_m2
- ghi_forecast_wh_m2
- temp_c

This design keeps Phase 2 independent from the Phase 1 training pipeline while preserving traceable linkage between project stages.

---

## Processed Data Files

Typical processed files used in this repository include:

- `phase2_inputs.csv`
- `pv_actual_kw.csv`
- `pv_forecast_kw.csv`
- `load_kw.csv`
- `sim_perfect.csv`
- `sim_forecast.csv`

These files are generated during notebook execution and stored in `data/processed/`.

---

## Known Limitations

- NASA POWER irradiance is satellite/reanalysis-derived and may smooth local cloud dynamics.
- Fast irradiance ramps may be understated relative to ground measurements.
- GHI-to-DNI/DHI decomposition introduces additional modeling uncertainty.
- Plane-of-array transposition introduces approximation error.
- Forecast irradiance inherits errors from the Phase 1 baseline model.
- The purpose of this repository is not to reproduce plant-grade PV physics, but to build a consistent stress-test pipeline for forecast uncertainty in mini-grid operations.

---

## Reproducibility Notes

- Public source data should be retrieved from the original source (NASA POWER), not from another repository.
- Derived forecast outputs may be imported from earlier project stages as processed artifacts.
- This design keeps the repository independently reproducible while preserving cross-phase linkage where appropriate.