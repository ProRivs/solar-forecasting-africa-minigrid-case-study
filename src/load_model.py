import numpy as np
import pandas as pd

def periurban_load_kw(times: pd.DatetimeIndex, base_kw=25.0, peak_kw=120.0, seed=42) -> pd.Series:
    """
    Peri-urban synthetic load:
      - morning ramp
      - daytime moderate
      - strong evening peak (18-23)
    Deterministic with seed.
    """
    rng = np.random.default_rng(seed)
    h = times.hour

    # Morning bump around 8
    morning = np.exp(-0.5 * ((h - 8) / 2.0) ** 2)

    # Evening peak around 20
    evening = np.exp(-0.5 * ((h - 20) / 2.5) ** 2)

    # Daytime moderate uplift (11–16)
    daytime = ((h >= 11) & (h <= 16)).astype(float) * 0.4

    shape = 0.35 * morning + 0.75 * evening + 0.25 * daytime
    shape = (shape - shape.min()) / (shape.max() - shape.min() + 1e-9)

    load = base_kw + shape * (peak_kw - base_kw)

    # Small noise
    load = load * (1 + rng.normal(0, 0.03, size=len(times)))
    load = np.clip(load, 0, None)

    return pd.Series(load, index=times, name="load_kw")