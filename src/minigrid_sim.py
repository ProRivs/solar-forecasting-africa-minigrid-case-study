import pandas as pd

from .config import SiteConfig, PVConfig, BatteryConfig, SimConfig
from .pv_model import pv_ac_power_series
from .battery_model import dispatch_battery


def simulate_minigrid(
    df: pd.DataFrame,
    ghi_col: str,
    temp_col: str,
    site: SiteConfig,
    pv: PVConfig,
    batt: BatteryConfig,
    sim: SimConfig,
    load_kw: pd.Series
) -> pd.DataFrame:
    """
    Run mini-grid simulation for one irradiance scenario.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - time
        - ghi_col
        - temp_col
    ghi_col : str
        Name of irradiance column to use for this scenario.
    temp_col : str
        Name of temperature column.
    site, pv, batt, sim : config objects
    load_kw : pd.Series
        Hourly load profile aligned to df["time"].

    Returns
    -------
    pd.DataFrame
        Simulation outputs:
        - pv_ac_kw
        - load_kw
        - served_load_kw
        - unserved_load_kw
        - curtailed_pv_kw
        - soc
        - battery_throughput_kwh
    """
    times = pd.DatetimeIndex(df["time"])

    pv_kw = pv_ac_power_series(
        df=df,
        ghi_col=ghi_col,
        temp_col=temp_col,
        site=site,
        pv=pv
    )

    batt_df = dispatch_battery(
        times=times,
        pv_kw=pv_kw,
        load_kw=load_kw,
        batt=batt,
        sim=sim
    )

    served_kw = load_kw - batt_df["unserved_load_kw"]

    out = pd.DataFrame(index=times)
    out["pv_ac_kw"] = pv_kw
    out["load_kw"] = load_kw
    out["served_load_kw"] = served_kw
    out["unserved_load_kw"] = batt_df["unserved_load_kw"]
    out["curtailed_pv_kw"] = batt_df["curtailed_pv_kw"]
    out["soc"] = batt_df["soc"]
    out["battery_throughput_kwh"] = batt_df["battery_throughput_kwh"]

    out.index.name = "time"
    return out