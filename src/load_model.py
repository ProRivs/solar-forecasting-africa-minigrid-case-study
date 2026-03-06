import numpy as np
import pandas as pd

def periurban_load_profile(
    times: pd.DatetimeIndex,
    base_kw: float = 20.0,
    peak_kw: float = 80.0,
    seed: int = 42
) -> pd.Series:
    """
    Synthetic peri-urban hourly load profile used for Phase 2 case study.

    Characteristics or Design intent:
    - morning ramp
    - moderate daytime commercial/service demand
    - strong evening peak (18:00-23:00)
    - slight day-of-week variation
    - small random noise for realism

    This load is intentionally synthetic but defensible. It is designed to approximate typical peri-urban demand patterns while remaining reproducible across 
    simulations.

    The purpose is not to reproduce a measured feeder exactly, but to provide a consistent stress-test load profile for mini-grid analysis.

    Parameters
    ----------
    times : pd.DatetimeIndex
        Shared hourly simulation index.
    base_kw : float
        Minimum background demand.
    peak_kw : float
        Peak evening demand.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.Series
        Hourly load in kW.
    """
    rng = np.random.default_rng(seed)
    h = times.hour
    dow = times.dayofweek

    # Morning ramp centered around 08:00
    morning = np.exp(-0.5 * ((h - 8) / 2.0) ** 2)

    # Daytime moderate demand uplift between 11:00 and 16:00
    daytime = ((h >= 11) & (h <= 16)).astype(float) * 0.35

    # Strong evening peak centered around 20:00
    evening = np.exp(-0.5 * ((h - 20) / 2.5) ** 2)

    # Combined normalized shape
    shape = 0.35 * morning + 0.25 * daytime + 0.75 * evening
    shape = (shape - shape.min()) / (shape.max() - shape.min() + 1e-9)

    load_kw = base_kw + shape * (peak_kw - base_kw)

    # Slight weekend evening uplift (peri-urban social/commercial activity)
    weekend_evening = ((dow >= 5) & (h >= 18) & (h <= 23)).astype(float)
    load_kw = load_kw * (1 + 0.05 * weekend_evening)

    # Small random noise (±3%)
    noise = rng.normal(0, 0.03, size=len(times))
    load_kw = load_kw * (1 + noise)

    # Keep physically valid
    load_kw = np.clip(load_kw, 0, None)

    return pd.Series(load_kw, index=times, name="load_kw")



    # This is synthetic, defensible, and designed to reflect: morning activity pickup, daytime moderate commercial/service demand, strong evening peak
    # The purpose is not to reproduce a measured feeder exactly, but to provide a reproducible peri-urban stress-test load for mini-grid analysis.