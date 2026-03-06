import pandas as pd
from .config import SimConfig

def risk_metrics(sim_df: pd.DataFrame, sim: SimConfig) -> pd.Series:
    dt = sim.dt_hours

    unserved_kwh = (sim_df["unserved_load_kw"] * dt).sum()
    lolh = (sim_df["unserved_load_kw"] > 0).sum()
    curtailed_kwh = (sim_df["curtailed_pv_kw"] * dt).sum()
    batt_throughput_kwh = sim_df["battery_throughput_kwh"].sum()

    return pd.Series({
        "unserved_energy_kwh": unserved_kwh,
        "lolh_hours": lolh,
        "curtailment_kwh": curtailed_kwh,
        "battery_throughput_kwh": batt_throughput_kwh
    })

def risk_deltas(perfect: pd.Series, forecast: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({"perfect": perfect, "forecast": forecast})
    df["delta_B_minus_A"] = df["forecast"] - df["perfect"]
    return df