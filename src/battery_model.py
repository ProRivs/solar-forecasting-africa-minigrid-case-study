import numpy as np
import pandas as pd
from .config import BatteryConfig, SimConfig

def dispatch_battery(
    times: pd.DatetimeIndex,
    pv_kw: pd.Series,
    load_kw: pd.Series,
    batt: BatteryConfig,
    sim: SimConfig
) -> pd.DataFrame:
    dt = sim.dt_hours
    e_max = batt.energy_kwh
    p_max = batt.power_kw

    e_min = batt.soc_min * e_max
    e_max_soc = batt.soc_max * e_max

    soc = np.zeros(len(times))
    e = batt.soc_init * e_max

    charge_kw = np.zeros(len(times))
    discharge_kw = np.zeros(len(times))
    curtailed_kw = np.zeros(len(times))
    unserved_kw = np.zeros(len(times))

    for i in range(len(times)):
        pv = float(pv_kw.iloc[i])
        ld = float(load_kw.iloc[i])
        net = pv - ld  # + surplus PV

        if net >= 0:
            # Charge
            headroom_kwh = max(e_max_soc - e, 0)
            headroom_kw = headroom_kwh / dt
            p_ch = min(net, p_max, headroom_kw)

            # store energy with charge efficiency
            e = e + p_ch * dt * batt.eta_charge
            charge_kw[i] = p_ch
            curtailed_kw[i] = net - p_ch

        else:
            # Discharge
            deficit = -net
            available_kwh = max(e - e_min, 0)

            # deliverable kW considering discharge efficiency
            available_kw = (available_kwh / dt) * batt.eta_discharge
            p_dis = min(deficit, p_max, available_kw)

            # remove energy accounting for discharge efficiency
            e = e - (p_dis * dt) / batt.eta_discharge
            discharge_kw[i] = p_dis
            unserved_kw[i] = deficit - p_dis

        soc[i] = e / e_max

    out = pd.DataFrame(
        {
            "soc": soc,
            "charge_kw": charge_kw,
            "discharge_kw": discharge_kw,
            "curtailed_pv_kw": curtailed_kw,
            "unserved_load_kw": unserved_kw,
        },
        index=times
    )
    out.index.name = "time"
    out["battery_throughput_kwh"] = (out["charge_kw"] + out["discharge_kw"]) * dt
    return out