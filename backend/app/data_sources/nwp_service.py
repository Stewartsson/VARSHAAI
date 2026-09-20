from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


OPEN_METEO_GFS_URL = "https://api.open-meteo.com/v1/gfs"

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707

FORECAST_HOURS = 72

HOURLY_VARIABLES = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "pressure_msl",
        "wind_speed_10m",
        "wind_direction_10m",
        "cloud_cover",
        "cape",
    ]
)


def _fetch_gfs() -> dict[str, Any]:
    params = {
        "latitude": CHENNAI_LAT,
        "longitude": CHENNAI_LON,
        "hourly": HOURLY_VARIABLES,
        "forecast_hours": FORECAST_HOURS,
        "timezone": "UTC",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    response = requests.get(
        OPEN_METEO_GFS_URL,
        params=params,
        timeout=30,
        headers={
            "User-Agent": "VARSHAAI/1.0",
            "Accept": "application/json",
        },
    )
    response.raise_for_status()
    return response.json()


def _value(values: list[Any], index: int) -> float | None:
    if index >= len(values):
        return None

    raw = values[index]

    if raw is None:
        return None

    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _build_observations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []

    observations: list[dict[str, Any]] = []

    for index, timestamp in enumerate(times):
        observations.append(
            {
                "timestamp_utc": timestamp,
                "lead_hour": index,
                "temperature_c": _value(
                    hourly.get("temperature_2m", []), index
                ),
                "relative_humidity_percent": _value(
                    hourly.get("relative_humidity_2m", []), index
                ),
                "precipitation_mm": _value(
                    hourly.get("precipitation", []), index
                ),
                "rain_mm": _value(
                    hourly.get("rain", []), index
                ),
                "pressure_msl_hpa": _value(
                    hourly.get("pressure_msl", []), index
                ),
                "wind_speed_kmph": _value(
                    hourly.get("wind_speed_10m", []), index
                ),
                "wind_direction_deg": _value(
                    hourly.get("wind_direction_10m", []), index
                ),
                "cloud_cover_percent": _value(
                    hourly.get("cloud_cover", []), index
                ),
                "cape_jkg": _value(
                    hourly.get("cape", []), index
                ),
            }
        )

    return observations


def fetch_chennai_gfs() -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()

    try:
        payload = _fetch_gfs()
        observations = _build_observations(payload)

        return {
            "status": "connected",
            "source": "NOAA GFS",
            "provider": "Open-Meteo GFS API",
            "model": "GFS",
            "region": "Chennai District, Tamil Nadu",
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
            "checked_at_utc": checked_at,
            "forecast_horizon_hours": FORECAST_HOURS,
            "observation_count": len(observations),
            "observations": observations,
            "model_metadata": {
                "spatial_resolution": "approximately 0.11° (~13 km) for GFS global data",
                "native_forecast": "hourly up to 120 hours; longer lead times may be 3-hourly",
                "update_frequency": "approximately every 6 hours",
            },
            "postprocessing": {
                "bias_correction": "ready_for_integration",
                "trained_ml_inference": False,
                "note": (
                    "Raw GFS forecast is connected. "
                    "ML bias correction must only be applied after "
                    "feature schema and trained-model validation."
                ),
            },
        }

    except requests.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        return {
            "status": "unavailable",
            "source": "NOAA GFS",
            "provider": "Open-Meteo GFS API",
            "model": "GFS",
            "region": "Chennai District, Tamil Nadu",
            "checked_at_utc": checked_at,
            "forecast_horizon_hours": FORECAST_HOURS,
            "observation_count": 0,
            "observations": [],
            "http_status": status_code,
            "error": str(exc),
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "source": "NOAA GFS",
            "provider": "Open-Meteo GFS API",
            "model": "GFS",
            "region": "Chennai District, Tamil Nadu",
            "checked_at_utc": checked_at,
            "forecast_horizon_hours": FORECAST_HOURS,
            "observation_count": 0,
            "observations": [],
            "error": str(exc),
        }


def get_gfs_status() -> dict[str, Any]:
    result = fetch_chennai_gfs()

    observations = result.get("observations", [])

    rainfall = [
        item["precipitation_mm"]
        for item in observations
        if item.get("precipitation_mm") is not None
    ]

    max_rain = max(rainfall) if rainfall else None

    return {
        "status": result.get("status"),
        "source": result.get("source"),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "region": result.get("region"),
        "checked_at_utc": result.get("checked_at_utc"),
        "forecast_horizon_hours": result.get("forecast_horizon_hours"),
        "observation_count": result.get("observation_count", 0),
        "max_hourly_precipitation_mm": max_rain,
        "postprocessing": result.get("postprocessing"),
        "http_status": result.get("http_status"),
        "error": result.get("error"),
    }
