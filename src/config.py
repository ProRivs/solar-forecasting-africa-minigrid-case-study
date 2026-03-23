from dataclasses import dataclass

@dataclass(frozen=True)
class SiteConfig:
    name: str = "Maroua, Cameroon"
    latitude: float = 10.6032
    longitude: float = 14.3226
    
    # Internal data basis
    time_basis: str = "NASA_LST"

    # Used only where pvlib requires timezone-aware timestamps
    tz_pvlib: str = "Africa/Douala"

    # we can repace the africa/Douala timezone with the one below for more precision
    '''
        @property
        def tz_pvlib(self):
            solar_offset_hours = self.longitude / 15.0
            solar_offset_seconds = int(round(solar_offset_hours * 3600))
            return timezone(timedelta(seconds=solar_offset_seconds))
    '''
     
    # Optional user-facing display timezone
    tz_display: str = "Africa/Douala"
    
@dataclass(frozen=True)
class PVConfig:
    pv_ac_rated_kw: float = 100.0       # inverter AC rating    
    dc_ac_ratio: float = 1.2            # aka inverter loading ratio or ILR
    pv_dc_kw: float = 120.0             # # DC array (DC/AC=1.2 typical)

    tilt_deg: float = 12.0              # simple Sahel-like fixed tilt (10-15°) assumption
    azimuth_deg: float = 180.0          # south-facing

    # Aggregate losses = 14% => keep 0.86 net factor
    loss_factor: float = 0.86
    
@dataclass(frozen=True)
class BatteryConfig:
    energy_kwh: float = 200.0
    power_kw: float = 50.0
    eta_charge: float = 0.95
    eta_discharge: float = 0.95
    soc_min: float = 0.10
    soc_max: float = 0.90
    soc_init: float = 0.50
    
@dataclass(frozen=True)
class SimConfig:
    dt_hours: float = 1.0