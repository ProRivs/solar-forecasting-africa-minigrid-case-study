import pandas as pd
from .config import SimConfig


def risk_metrics(sim_df: pd.DataFrame, sim: SimConfig) -> pd.Series:
    """
    Compute mini-grid risk metrics for one scenario.

    Parameters
    ----------
    sim_df : pd.DataFrame
        Simulation output dataframe with at least:
        - unserved_load_kw
        - curtailed_pv_kw
        - battery_throughput_kwh
    sim : SimConfig
        Simulation configuration.

    Returns
    -------
    pd.Series
        Summary risk metrics.
    """
    dt = sim.dt_hours

    unserved_energy_kwh = (sim_df["unserved_load_kw"] * dt).sum()
    lolh_hours = (sim_df["unserved_load_kw"] > 0).sum()
    curtailment_kwh = (sim_df["curtailed_pv_kw"] * dt).sum()
    batt_throughput_kwh = sim_df["battery_throughput_kwh"].sum()

    return pd.Series({
        "unserved_energy_kwh": unserved_energy_kwh,
        "lolh_hours": lolh_hours,
        "curtailment_kwh": curtailment_kwh,
        "battery_throughput_kwh": batt_throughput_kwh
    })


def risk_deltas(perfect: pd.Series, forecast: pd.Series) -> pd.DataFrame:
    """
    Build comparison table: Perfect vs Forecast vs Delta.
    """
    table = pd.DataFrame({
        "perfect": perfect,
        "forecast": forecast
    })
    table["delta_B_minus_A"] = table["forecast"] - table["perfect"]
    return table