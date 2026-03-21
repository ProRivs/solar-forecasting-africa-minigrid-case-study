import numpy as np
import pandas as pd
import pvlib

from .config import SiteConfig, PVConfig


def pv_ac_power_series(
    df: pd.DataFrame,
    ghi_col: str,
    temp_col: str,
    site: SiteConfig,
    pv: PVConfig
) -> pd.Series:    
    """
    Convert hourly GHI and ambient temperature into hourly AC PV power.

    Internal time basis
    -------------------
    The input dataframe is expected to use NASA POWER LST as the master hourly index.
    These timestamps are kept timezone-naive in the wider Phase 2 pipeline.

    For pvlib solar-position calculations only, the LST timestamps are temporarily
    localized to Africa/Douala so that pvlib has a timezone-aware DatetimeIndex.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
        - time: timezone-aware datetime
        - ghi_col: hourly GHI (Wh/m² over 1 hour, treated as average W/m²)
        - temp_col: ambient temperature in °C
    ghi_col : str
        Name of GHI column.
    temp_col : str
        Name of ambient temperature column.
    site : SiteConfig
        Site configuration (location, timezone).
    pv : PVConfig
        PV system configuration.

    Returns
    -------
    pd.Series
        Hourly AC PV power in kW, clipped to inverter limit.

    Notes
    -----
    - NASA POWER hourly ALLSKY_SFC_SW_DWN is treated as average W/m² during the hour.
    - DNI is estimated from GHI using the DISC decomposition model. This introduces uncertainty, particularly       during cloudy periods.
    - DHI is reconstructed from GHI and DNI as: DHI = GHI - DNI * cos(zenith).
    - A fixed wind speed is used for simple cell temperature estimation.
    - Plane-of-array irradiance is computed using a fixed tilt system.
    - Aggregate system losses (~14%) are applied.
    
    This is a reproducible PV stress-test pipeline, not a plant-grade digital twin.
    """

    # --- SAFETY CHECK: enforce expected time basis ---
    if site.time_basis != "NASA_LST":
        raise ValueError("pv_model currently assumes NASA LST time basis")
        
    # Read time column
    times_raw = pd.DatetimeIndex(df["time"])

    # Normalize two parallel versions:
    # 1) internal naive index for outputs
    # 2) timezone-aware version for pvlib calculations
    if times_raw.tz is None:
        times_lst = times_raw
        times_pv = times_raw.tz_localize(site.tz_pvlib)
    else:
        times_pv = times_raw.tz_convert(site.tz_pvlib)
        times_lst = pd.DatetimeIndex(times_pv.tz_localize(None))

    # Use numpy arrays for core calculations
    ghi = df[ghi_col].astype(float).to_numpy()
    ghi = np.clip(ghi, 0, None)

    temp_air = df[temp_col].astype(float).to_numpy()

    location = pvlib.location.Location(
        latitude=site.latitude,
        longitude=site.longitude,
        tz=site.tz_pvlib,
        name=site.name
    )

    # Solar position
    solpos = location.get_solarposition(times_pv)
    zenith = solpos["zenith"].to_numpy()
    azimuth = solpos["azimuth"].to_numpy()

    # DISC decomposition
    disc_out = pvlib.irradiance.disc(
        ghi=ghi,
        solar_zenith=zenith,
        datetime_or_doy=times_pv
    )
    dni = np.clip(np.asarray(disc_out["dni"]), 0, None)

    # Reconstruct DHI
    cos_zenith = np.clip(np.cos(np.radians(zenith)), 0, None)
    dhi = np.clip(ghi - dni * cos_zenith, 0, None)

    # Plane-of-array irradiance
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=pv.tilt_deg,
        surface_azimuth=pv.azimuth_deg,
        solar_zenith=zenith,
        solar_azimuth=azimuth,
        dni=dni,
        ghi=ghi,
        dhi=dhi
    )
    poa_global = np.clip(np.asarray(poa["poa_global"]), 0, None)

    # Cell temperature
    temp_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]

    temp_cell = pvlib.temperature.sapm_cell(
        poa_global=poa_global,
        temp_air=temp_air,
        wind_speed=1.0,
        a=temp_params["a"],
        b=temp_params["b"],
        deltaT=temp_params["deltaT"]
    )

    # PVWatts DC
    pdc = pvlib.pvsystem.pvwatts_dc(
        effective_irradiance=poa_global,
        temp_cell=temp_cell,
        pdc0=pv.pv_dc_kw * 1000.0,
        gamma_pdc=-0.003
    )

    # Aggregate losses
    pdc = pdc * pv.loss_factor

    # PVWatts inverter
    pac = pvlib.inverter.pvwatts(
        pdc=pdc,
        pdc0=pv.pv_dc_kw * 1000.0
    )

    # W -> kW
    pac_kw = np.clip(np.asarray(pac) / 1000.0, 0, pv.pv_ac_rated_kw)

    # Force zero below horizon
    pac_kw = np.where(zenith < 90, pac_kw, 0.0)

    return pd.Series(pac_kw, index=times_lst, name="pv_ac_kw")