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
    - DNI is estimated from GHI using the DISC decomposition model. This introduces uncertainty, particularly during cloudy periods.
    - DHI is reconstructed from GHI and DNI as: DHI = GHI - DNI * cos(zenith).
    - A fixed wind speed is used for simple cell temperature estimation.
    - Plane-of-array irradiance is computed using a fixed tilt system.
    
    This is a reproducible PV stress-test pipeline, not a plant-grade digital twin.
    """

    # Shared time index
    times = pd.DatetimeIndex(df["time"])

    # NASA POWER hourly ALLSKY_SFC_SW_DWN is Wh/m² over the hour.
    # For hourly modeling, we treat it as average W/m² during that hour.
    ghi = df[ghi_col].astype(float).clip(lower=0)
    

    # Ambient temperature
    ghi = df[ghi_col].astype(float).clip(lower=0)
    temp_air = df[temp_col].astype(float)

    # pvlib site object
    location = pvlib.location.Location(
        latitude=site.latitude,
        longitude=site.longitude,
        tz=site.tz_calc,
        name=site.name
    )

    # Solar position
    solpos = location.get_solarposition(times)
    zenith = solpos["zenith"]
    azimuth = solpos["azimuth"]

    # DNI estimate from GHI using DISC
    disc_out = pvlib.irradiance.disc(
        ghi=ghi,
        solar_zenith=zenith,
        datetime_or_doy=times
    )
    dni = pd.Series(disc_out["dni"], index=times).clip(lower=0)

    # Compute DHI from GHI - DNI*cos(zenith), clipped at zero
    cos_zenith = np.cos(np.radians(zenith)).clip(lower=0)
    dhi = (ghi - dni * cos_zenith).clip(lower=0)

    # POA (Plane-of-array) irradiance
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=pv.tilt_deg,
        surface_azimuth=pv.azimuth_deg,
        solar_zenith=zenith,
        solar_azimuth=azimuth,
        dni=dni,
        ghi=ghi,
        dhi=dhi
    )
    poa_global = pd.Series(poa["poa_global"], index=times).clip(lower=0)

    # Cell temperature approximation using SAPM open-rack glass/glass default style
    temp_cell = pvlib.temperature.sapm_cell(
        poa_global=poa_global,
        temp_air=temp_air,
        wind_speed=1.0  # simple fixed assumption for baseline case
    )

    # DC power using PVWatts
    # pdc0 = DC nameplate in W
    pdc = pvlib.pvsystem.pvwatts_dc(
        g_poa_effective=poa_global,
        temp_cell=temp_cell,
        pdc0=pv.pv_dc_kw * 1000.0,
        gamma_pdc=-0.003
    )

    # Apply aggregate system losses consistently at DC stage
    pdc = pdc * pv.loss_factor

    # Convert DC to AC using PVWatts inverter model
    pac = pvlib.inverter.pvwatts(
        pdc=pdc,
        pdc0=pv.pv_dc_kw * 1000.0
    )

    # Convert W -> kW and clip to inverter AC rating
    pac_kw = pd.Series(pac, index=times) / 1000.0
    pac_kw = pac_kw.clip(lower=0, upper=pv.pv_ac_rated_kw)

    pac_kw.name = "pv_ac_kw"
    return pac_kw