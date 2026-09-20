from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WeatherObservation:
    """
    Common observation format used by RainGuard's
    multi-source data ingestion layer.
    """

    source: str
    timestamp: datetime

    latitude: float
    longitude: float

    rainfall_mm: Optional[float] = None

    temperature_c: Optional[float] = None
    relative_humidity: Optional[float] = None

    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None

    pressure_hpa: Optional[float] = None

    reflectivity_dbz: Optional[float] = None
    cloud_top_temperature_k: Optional[float] = None

    quality_flag: str = "unknown"