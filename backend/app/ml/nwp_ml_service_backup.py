from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json
import joblib
import numpy as np
import requests


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "models" / "rainguard_nwp_postprocessor.joblib"

HEM_TIMESERIES_PATH = (
    BASE_DIR
    / "data"
    / "mosdac"
    / "processed"
    / "chennai_hem_timeseries.json"
)


# ============================================================
# CHENNAI
# ============================================================

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707


# ============================================================
# GFS
# ============================================================

GFS_URL = "https://api.open-meteo.com/v1/gfs"

FORECAST_HOURS = 72


# ============================================================
# TRAINED MODEL FEATURES
# ============================================================

FEATURE_NAMES = [
    "nwp_precipitation_mm",
    "nwp_humidity",
    "nwp_wind_speed_ms",
    "nwp_pressure_hpa",
    "recent_rainfall_mm",
    "rolling_3_day_rainfall_mm",
    "rolling_7_day_rainfall_mm",
]


# ============================================================
# MODEL
# ============================================================

def load_model_payload() -> dict[str, Any]:
    """
    Load the trained NWP post-processing model.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}"
        )

    payload = joblib.load(MODEL_PATH)

    if not isinstance(payload, dict):
        raise ValueError(
            "Unexpected model format. Expected a dictionary."
        )

    return payload


# ============================================================
# GFS FORECAST
# ============================================================

def fetch_gfs_forecast() -> dict[str, Any]:
    """
    Fetch 72-hour GFS forecast for Chennai.

    Source:
        NOAA GFS
        Open-Meteo GFS API

    This is a prototype NWP connection.
    """

    params = {
        "latitude": CHENNAI_LAT,
        "longitude": CHENNAI_LON,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "pressure_msl,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "cloud_cover,"
            "cape"
        ),
        "forecast_hours": FORECAST_HOURS,
        "timezone": "UTC",
    }

    response = requests.get(
        GFS_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# HEM HISTORICAL DATA
# ============================================================

def load_hem_timeseries() -> dict[str, Any]:
    """
    Load the processed INSAT-3DR HEM time series.

    No synthetic observations are generated.
    """

    if not HEM_TIMESERIES_PATH.exists():
        return {
            "status": "unavailable",
            "observations": [],
        }

    with open(
        HEM_TIMESERIES_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# RAINFALL FEATURES
# ============================================================

def calculate_rainfall_features(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate historical rainfall features required by
    the trained NWP model.

    The model requires:

    1. Recent rainfall
    2. Rolling 3-day rainfall
    3. Rolling 7-day rainfall

    Missing historical coverage is NOT fabricated.
    """

    if not observations:
        return {
            "recent_rainfall_mm": None,
            "rolling_3_day_rainfall_mm": None,
            "rolling_7_day_rainfall_mm": None,
            "history_available": False,
            "history_coverage_hours": 0.0,
            "history_reason": "No historical observations available.",
        }

    parsed = []

    for item in observations:

        timestamp = item.get("timestamp_utc")

        rainfall = item.get("rainfall_mm_hr")

        if timestamp is None or rainfall is None:
            continue

        try:
            dt = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )

            value = float(rainfall)

            parsed.append(
                (
                    dt,
                    value,
                )
            )

        except (ValueError, TypeError):
            continue

    if not parsed:
        return {
            "recent_rainfall_mm": None,
            "rolling_3_day_rainfall_mm": None,
            "rolling_7_day_rainfall_mm": None,
            "history_available": False,
            "history_coverage_hours": 0.0,
            "history_reason": "No valid rainfall observations available.",
        }

    parsed.sort(key=lambda x: x[0])

    first_time = parsed[0][0]
    last_time = parsed[-1][0]

    coverage_hours = (
        last_time - first_time
    ).total_seconds() / 3600.0

    recent_rainfall = parsed[-1][1]

    # --------------------------------------------------------
    # 3-day requirement
    # --------------------------------------------------------

    rolling_3_day = None

    if coverage_hours >= 72:

        cutoff_3 = last_time.timestamp() - (
            72 * 3600
        )

        values_3 = [
            value
            for dt, value in parsed
            if dt.timestamp() >= cutoff_3
        ]

        if values_3:
            rolling_3_day = float(
                np.sum(values_3)
            )

    # --------------------------------------------------------
    # 7-day requirement
    # --------------------------------------------------------

    rolling_7_day = None

    if coverage_hours >= 168:

        cutoff_7 = last_time.timestamp() - (
            168 * 3600
        )

        values_7 = [
            value
            for dt, value in parsed
            if dt.timestamp() >= cutoff_7
        ]

        if values_7:
            rolling_7_day = float(
                np.sum(values_7)
            )

    history_available = (
        rolling_3_day is not None
        and rolling_7_day is not None
    )

    if history_available:

        reason = (
            "Required historical rainfall features are available."
        )

    else:

        reason = (
            "Current INSAT-3DR dataset does not contain "
            "the full 3-day and 7-day historical windows "
            "required by the trained model."
        )

    return {
        "recent_rainfall_mm": float(
            recent_rainfall
        ),
        "rolling_3_day_rainfall_mm": rolling_3_day,
        "rolling_7_day_rainfall_mm": rolling_7_day,
        "history_available": history_available,
        "history_coverage_hours": round(
            coverage_hours,
            2,
        ),
        "history_reason": reason,
    }


# ============================================================
# GFS RECORD BUILDING
# ============================================================

def build_gfs_records(
    gfs_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convert raw GFS response into model-friendly records.
    """

    hourly = gfs_data.get(
        "hourly",
        {},
    )

    times = hourly.get(
        "time",
        [],
    )

    precipitation = hourly.get(
        "precipitation",
        [],
    )

    humidity = hourly.get(
        "relative_humidity_2m",
        [],
    )

    wind_speed = hourly.get(
        "wind_speed_10m",
        [],
    )

    pressure = hourly.get(
        "pressure_msl",
        [],
    )

    records = []

    for index, timestamp in enumerate(times):

        precip = (
            precipitation[index]
            if index < len(precipitation)
            else None
        )

        rh = (
            humidity[index]
            if index < len(humidity)
            else None
        )

        wind_kmh = (
            wind_speed[index]
            if index < len(wind_speed)
            else None
        )

        pressure_value = (
            pressure[index]
            if index < len(pressure)
            else None
        )

        wind_ms = None

        if wind_kmh is not None:
            wind_ms = float(wind_kmh) / 3.6

        records.append(
            {
                "timestamp_utc": timestamp,
                "nwp_precipitation_mm": (
                    float(precip)
                    if precip is not None
                    else None
                ),
                "nwp_humidity": (
                    float(rh)
                    if rh is not None
                    else None
                ),
                "nwp_wind_speed_ms": wind_ms,
                "nwp_pressure_hpa": (
                    float(pressure_value)
                    if pressure_value is not None
                    else None
                ),
            }
        )

    return records


# ============================================================
# LIVE POST-PROCESSED FORECAST
# ============================================================

def generate_postprocessed_forecast() -> dict[str, Any]:
    """
    Generate the NWP + ML post-processing result.

    ML prediction is intentionally gated.

    Prediction occurs ONLY when all seven required
    model features are genuinely available.
    """

    model_payload = load_model_payload()

    model = model_payload.get("model")

    model_features = model_payload.get(
        "feature_names",
        FEATURE_NAMES,
    )

    gfs_data = fetch_gfs_forecast()

    hem_data = load_hem_timeseries()

    observations = hem_data.get(
        "observations",
        [],
    )

    historical = calculate_rainfall_features(
        observations
    )

    gfs_records = build_gfs_records(
        gfs_data
    )

    feature_status = {
        "nwp_precipitation_mm": "available",
        "nwp_humidity": "available",
        "nwp_wind_speed_ms": "available",
        "nwp_pressure_hpa": "available",
        "recent_rainfall_mm": (
            "available"
            if historical["recent_rainfall_mm"] is not None
            else "unavailable"
        ),
        "rolling_3_day_rainfall_mm": (
            "available"
            if historical["rolling_3_day_rainfall_mm"] is not None
            else "unavailable"
        ),
        "rolling_7_day_rainfall_mm": (
            "available"
            if historical["rolling_7_day_rainfall_mm"] is not None
            else "unavailable"
        ),
    }

    required_available = all(
        value == "available"
        for value in feature_status.values()
    )

    predictions = []

    # ========================================================
    # ML INFERENCE
    # ========================================================

    if required_available:

        for record in gfs_records:

            values = [
                record["nwp_precipitation_mm"],
                record["nwp_humidity"],
                record["nwp_wind_speed_ms"],
                record["nwp_pressure_hpa"],
                historical["recent_rainfall_mm"],
                historical["rolling_3_day_rainfall_mm"],
                historical["rolling_7_day_rainfall_mm"],
            ]

            if not all(
                value is not None
                and np.isfinite(float(value))
                for value in values
            ):
                continue

            X = np.asarray(
                [values],
                dtype=np.float32,
            )

            prediction = model.predict(X)

            prediction_value = max(
                float(prediction[0]),
                0.0,
            )

            predictions.append(
                {
                    "timestamp_utc": record[
                        "timestamp_utc"
                    ],
                    "lead_hour": len(predictions),
                    "raw_nwp_precipitation_mm": (
                        record[
                            "nwp_precipitation_mm"
                        ]
                    ),
                    "ml_postprocessed_precipitation_mm": (
                        prediction_value
                    ),
                }
            )

    status = (
        "prediction_available"
        if predictions
        else "historical_data_required"
    )

    return {
        "status": status,
        "source": "NOAA GFS",
        "provider": "Open-Meteo GFS API",
        "model": "HistGradientBoostingRegressor",
        "model_file": MODEL_PATH.name,
        "region": "Chennai District, Tamil Nadu",
        "latitude": CHENNAI_LAT,
        "longitude": CHENNAI_LON,
        "forecast_horizon_hours": FORECAST_HOURS,
        "feature_names": model_features,
        "feature_count": len(model_features),
        "feature_status": feature_status,
        "historical_rainfall": historical,
        "prediction_available": bool(
            predictions
        ),
        "predictions": predictions,
        "prediction_count": len(
            predictions
        ),
        "scientific_note": (
            "ML inference is performed only when "
            "all seven trained-model features are "
            "available from genuine data. "
            "Missing historical rainfall is not synthesized."
        ),
    }


# ============================================================
# END
# ============================================================


if __name__ == "__main__":

    print(
        "VARSHAAI NWP ML SERVICE"
    )

    print(
        "Model:",
        MODEL_PATH,
    )

    print(
        "HEM:",
        HEM_TIMESERIES_PATH,
    )

    payload = load_model_payload()

    print(
        "Model loaded:",
        type(payload.get("model")).__name__,
    )

    print(
        "Features:",
        payload.get(
            "feature_names",
            FEATURE_NAMES,
        ),
    )