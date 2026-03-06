# Solar Forecasting Africa Mini-Grid Case Study

This repository implements a reproducible mini-grid stress-test to evaluate how solar forecast uncertainty affects design-relevant and operational outcomes.

## System Definition
- **PV system:** 100 kW AC, 120 kWp DC (DC/AC ratio = 1.2)
- **Battery:** 200 kWh / 50 kW, rule-based dispatch
- **Load:** synthetic peri-urban hourly demand profile

## Scenario Design
Two scenarios are evaluated using the same load and battery assumptions:

- **Scenario A — Perfect:** PV generation is computed from actual irradiance
- **Scenario B — Forecast:** PV generation is computed from forecasted irradiance produced by the Phase 1 baseline forecasting workflow

The difference between these scenarios isolates the operational penalty introduced by forecast uncertainty.

## Outputs
The main outputs are mini-grid-relevant risk metrics for both scenarios and their deltas:

- Unserved Energy (kWh)
- Loss of Load Hours (LOLH)
- Energy Curtailed (kWh)
- Battery Throughput (kWh)

The core Phase 2 result is the forecast penalty:

- ΔUnservedEnergy
- ΔLOLH
- ΔCurtailment
- ΔBatteryThroughput

## Objective
This is a stress-test of design and operations under forecast uncertainty.

The goal is not to build a full optimization framework, but to establish a transparent and defensible pipeline linking:
1. irradiance inputs,
2. PV power conversion,
3. peri-urban demand,
4. battery dispatch,
5. reliability-oriented risk metrics.

## Repository Structure
```text
solar-forecasting-minigrid-case-study/
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── src/
│   ├── config.py
│   ├── pv_model.py
│   ├── load_model.py
│   ├── battery_model.py
│   ├── minigrid_sim.py
│   └── metrics.py
├── notebooks/
│   ├── 01_build_inputs.ipynb
│   ├── 02_pv_simulation.ipynb
│   ├── 03_minigrid_dispatch.ipynb
│   └── 04_risk_metrics.ipynb
├── reports/
│   ├── phase2_summary.md
│   └── tables/
├── requirements.txt
└── README.md
```

## Note:
### Modeling scope:

The load profile is synthetic but designed to represent a plausible
peri-urban demand pattern with morning activity, moderate daytime
commercial demand, and a strong evening peak.

PV production is derived from NASA POWER irradiance using a simplified
pvlib pipeline intended for reproducible stress-testing rather than
plant-grade PV performance modeling.

