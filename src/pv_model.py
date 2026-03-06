import pandas as pd
import pvlib

from .config import SiteConfig, PVConfig

def pv_ac_kw_from_ghi_wh_m2(
        df: pd.DataFrame,
        ghi_col: str,
        site: SiteConfig,
        pv: PVConfig
   ) -> pd.Series:
        """
        Input df msut have:
            - time: timezone-aware datetime (tz_calc, typically UTC)
            - ghi_col: hourly GHI energy per area (Wh/m² per hour)
            - temp_c: optional (not used in this simplified baseline)
        Output:
            - pv_ac_kw: hourly AC power (kW), clipped to 100 kW inverter
        """
    
        times = pd.DatetimeIndex(df["time"])
        ghi = df[ghi_col].astype(float).clip(lower=0)
        
        # pvlib location + solar position
        loc = pvlib.location.location(site.latitude, site.longitude, tz=site.tz_calc, name=site.name)
        solpos = loc.get_solarposition(times)
        
        # Decompose GHI -> DNI/DHI (Erbs: simple, defensible)
        erbs_out = pvlib.irradiance.erbs(
            ghi=ghi, 
            zenith=solpos["zenith"], 
            datetime_or_doy=times
        )
        dni = erbs_out["dni"].clip(lower=0)
        dhi = erbs_out["dhi"].clip(lower=0)

        # POA (plane-of-array) irradiance on tilted plane
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=pv.tilt_deg,
            surface_azimuth=pv.azimuth_deg,
            solar_zenith=solpos["zenith"],
            solar_azimuth=solpos["azimuth"],
            dni=dni, ghi=ghi, dhi=dhi,
        )
        poa_global = poa["poa_global"].clip(lower=0)

       # Simple PV conversion (baseline):
       # DC ~ pv_dc_kw * (POA/1000), then apply aggregate loss factor, then clip at AC rating
   p_dc_kw = pv.pv_dc_kw * (poa_global / 1000.0)
   p_ac_kw = (p_dc_kw * pv.loss_factor).clip(lower=0, upper=pv.pv_ac_rated_kw)

   return p_ac_kw.rename("pv_ac_kw")
        
        