import pandas as pd
from .config import SiteConfig, PVConfig, BatteryConfig, SimConfig
from .pv_model import pv_ac_kw_from_ghi_wh_m2
from .battery_model import dispatch_battery

def simulate_minigrid(df: pd.DataFrame, ghi_col: str,
                      site: SiteConfig, pv: PVConfig, batt: BatteryConfig, sim: SimConfig,
                      load_kw: pd.Series) -> pd.DataFrame:
    times = pd.DatetimeIndex(df["time"])
    pv_kw = pv_ac_kw_from_ghi_wh_m2(df, ghi_col=ghi_col, site=site, pv=pv)

    batt_df = dispatch_battery(times, pv_kw, load_kw, batt, sim)

    supply_kw = pv_kw + batt_df["discharge_kw"]  # battery discharge adds supply
    # charging consumes surplus PV; curtailment already computed in batt_df
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