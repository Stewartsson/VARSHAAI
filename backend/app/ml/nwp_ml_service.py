"""
VARSHAAI - NWP ML Service

Purpose:
    Fetch genuine NWP forecast data for Chennai,
    combine it with recent rainfall history,
    and apply the trained NWP post-processing model.

NWP source:
    Open-Meteo GFS

Historical rainfall source:
    Open-Meteo Historical Archive

Optional historical satellite source:
    INSAT-3DR HEM time series

Trained model:
    backend/models/rainguard_nwp_postprocessor.joblib
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import json

import joblib
import numpy as np
import requests


# ============================================================
# PATHS
# ============================================================

# This file is:
#
# VARSHAAI/
# └── backend/
#     └── app/
#         └── ml/
#             └── nwp_ml_service.py
#
# parents[2] = backend/
#
BASE_DIR = Path(__file__).resolve().parents[2]


MODEL_PATH = (
    BASE_DIR
    / "models"
    / "rainguard_nwp_postprocessor.joblib"
)


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
# GFS / NWP
# ============================================================

GFS_URL = "https://api.open-meteo.com/v1/gfs"

FORECAST_HOURS = 72


# ============================================================
# RECENT HISTORICAL RAINFALL
# ============================================================

HISTORICAL_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

HISTORICAL_DAYS = 7


# ============================================================
# MODEL FEATURES
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
# MODEL LOADING
# ============================================================

def load_model_payload() -> dict[str, Any]:
    """
    Load the trained NWP post-processing model.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained NWP model not found:\n{MODEL_PATH}"
        )

    payload = joblib.load(MODEL_PATH)

    if not isinstance(payload, dict):
        raise ValueError(
            "Unexpected model format. "
            "Expected a dictionary."
        )

    return payload


# ============================================================
# MODEL VALIDATION
# ============================================================

def validate_model_payload(
    payload: dict[str, Any],
) -> None:
    """
    Validate that the saved model contains the
    expected components and features.
    """

    if "model" not in payload:
        raise ValueError(
            "Saved NWP model does not contain 'model'."
        )

    if "feature_names" not in payload:
        raise ValueError(
            "Saved NWP model does not contain "
            "'feature_names'."
        )

    saved_features = payload["feature_names"]

    if saved_features != FEATURE_NAMES:
        raise ValueError(
            "NWP model feature mismatch.\n"
            f"Expected: {FEATURE_NAMES}\n"
            f"Found:    {saved_features}"
        )


# ============================================================
# GFS FORECAST
# ============================================================

def fetch_gfs_forecast() -> dict[str, Any]:
    """
    Fetch a 72-hour GFS forecast for Chennai.

    Primary source:
        Open-Meteo GFS endpoint.

    Fallback:
        Open-Meteo standard forecast endpoint.

    The fallback keeps the downstream ML pipeline alive when
    the GFS endpoint is temporarily rate-limited.
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

    urls = [
        (
            GFS_URL,
            "Open-Meteo GFS",
        ),
        (
            "https://api.open-meteo.com/v1/forecast",
            "Open-Meteo Forecast Fallback",
        ),
    ]

    last_error = None

    for url, source_name in urls:

        try:

            print(
                f"Fetching NWP source: {source_name}"
            )

            response = requests.get(
                url,
                params=params,
                timeout=30,
                headers={
                    "User-Agent": "VARSHAAI/1.0",
                    "Accept": "application/json",
                },
            )

            response.raise_for_status()

            payload = response.json()

            hourly = payload.get(
                "hourly",
                {},
            )

            times = hourly.get(
                "time",
                [],
            )

            if not times:
                raise ValueError(
                    "NWP response contains no hourly data."
                )

            print(
                f"NWP source connected: {source_name}"
            )

            payload["_varshaai_source"] = source_name

            return payload

        except Exception as exc:

            last_error = exc

            print(
                f"NWP source failed: "
                f"{source_name} -> {exc}"
            )

    raise RuntimeError(
        "All NWP forecast sources failed. "
        f"Last error: {last_error}"
    )

# ============================================================
# HEM HISTORICAL DATA
# ============================================================

def load_hem_timeseries() -> dict[str, Any]:
    """
    Load processed INSAT-3DR HEM time-series data.

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
# RECENT HISTORICAL RAINFALL
# ============================================================

def fetch_recent_historical_rainfall() -> dict[str, Any]:
    """
    Fetch genuine recent rainfall history for Chennai.

    Used for:

        recent rainfall
        rolling 3-day rainfall
        rolling 7-day rainfall
    """

    now_utc = datetime.now(timezone.utc)

    end_date = now_utc.date()

    start_date = (
        end_date
        - timedelta(days=HISTORICAL_DAYS)
    )

    params = {
        "latitude": CHENNAI_LAT,
        "longitude": CHENNAI_LON,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "precipitation",
        "timezone": "UTC",
    }

    try:

        response = requests.get(
            HISTORICAL_URL,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

    except Exception as exc:

        return {
            "source": "Open-Meteo Historical Archive",
            "provider": "Open-Meteo",
            "status": "unavailable",
            "observations": [],
            "history_available": False,
            "error": str(exc),
        }

    hourly = data.get(
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

    observations = []

    for index, timestamp in enumerate(times):

        if index >= len(precipitation):
            continue

        value = precipitation[index]

        if value is None:
            continue

        try:

            rainfall = float(value)

            if not np.isfinite(rainfall):
                continue

            observations.append(
                {
                    "timestamp_utc": timestamp,
                    "rainfall_mm": max(
                        rainfall,
                        0.0,
                    ),
                }
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

    return {
        "source": "Open-Meteo Historical Archive",
        "provider": "Open-Meteo",
        "status": (
            "available"
            if observations
            else "unavailable"
        ),
        "observations": observations,
        "history_available": bool(
            observations
        ),
        "error": None,
    }


# ============================================================
# RAINFALL FEATURES
# ============================================================

def calculate_rainfall_features(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate recent rainfall features.
    """

    if not observations:

        return {
            "recent_rainfall_mm": None,
            "rolling_3_day_rainfall_mm": None,
            "rolling_7_day_rainfall_mm": None,
            "history_available": False,
            "history_coverage_hours": 0.0,
            "history_source": "INSAT-3DR HEM",
            "history_reason": (
                "No historical observations available."
            ),
        }

    parsed = []

    for item in observations:

        timestamp = item.get(
            "timestamp_utc"
        )

        rainfall = item.get(
            "rainfall_mm"
        )

        if timestamp is None:
            continue

        if rainfall is None:
            continue

        try:

            dt = datetime.fromisoformat(
                timestamp.replace(
                    "Z",
                    "+00:00",
                )
            )

            value = float(rainfall)

            if not np.isfinite(value):
                continue

            parsed.append(
                (
                    dt,
                    max(value, 0.0),
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

    if not parsed:

        return {
            "recent_rainfall_mm": None,
            "rolling_3_day_rainfall_mm": None,
            "rolling_7_day_rainfall_mm": None,
            "history_available": False,
            "history_coverage_hours": 0.0,
            "history_source": "INSAT-3DR HEM",
            "history_reason": (
                "Historical observations "
                "could not be parsed."
            ),
        }

    parsed.sort(
        key=lambda item: item[0]
    )

    latest_time = parsed[-1][0]

    recent_start = (
        latest_time
        - timedelta(hours=24)
    )

    three_day_start = (
        latest_time
        - timedelta(days=3)
    )

    seven_day_start = (
        latest_time
        - timedelta(days=7)
    )

    recent_values = [
        rainfall
        for timestamp, rainfall in parsed
        if timestamp > recent_start
    ]

    three_day_values = [
        rainfall
        for timestamp, rainfall in parsed
        if timestamp > three_day_start
    ]

    seven_day_values = [
        rainfall
        for timestamp, rainfall in parsed
        if timestamp > seven_day_start
    ]

    coverage_hours = (
        parsed[-1][0]
        - parsed[0][0]
    ).total_seconds() / 3600.0

    return {
        "recent_rainfall_mm": (
            float(sum(recent_values))
            if recent_values
            else None
        ),
        "rolling_3_day_rainfall_mm": (
            float(sum(three_day_values))
            if three_day_values
            else None
        ),
        "rolling_7_day_rainfall_mm": (
            float(sum(seven_day_values))
            if seven_day_values
            else None
        ),
        "history_available": True,
        "history_coverage_hours": float(
            coverage_hours
        ),
        "history_source": "INSAT-3DR HEM",
        "history_reason": None,
    }


# ============================================================
# OPEN-METEO RAINFALL FEATURES
# ============================================================

def calculate_open_meteo_rainfall_features(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate rainfall features from Open-Meteo
    historical observations.

    Used when INSAT-3DR HEM historical coverage
    is unavailable.
    """

    result = calculate_rainfall_features(
        observations
    )

    result["history_source"] = (
        "Open-Meteo Historical Archive"
    )

    return result


# ============================================================
# NWP FEATURE MATRIX
# ============================================================

def build_nwp_feature_matrix(
    forecast: dict[str, Any],
    rainfall_features: dict[str, Any],
) -> tuple[np.ndarray, list[str]]:
    """
    Convert NWP forecast + rainfall history into
    the exact feature matrix expected by the model.
    """

    hourly = forecast.get(
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

    recent_rainfall = (
        rainfall_features.get(
            "recent_rainfall_mm"
        )
    )

    rolling_3_day = (
        rainfall_features.get(
            "rolling_3_day_rainfall_mm"
        )
    )

    rolling_7_day = (
        rainfall_features.get(
            "rolling_7_day_rainfall_mm"
        )
    )

    if recent_rainfall is None:
        recent_rainfall = 0.0

    if rolling_3_day is None:
        rolling_3_day = 0.0

    if rolling_7_day is None:
        rolling_7_day = 0.0

    sample_count = min(
        len(times),
        len(precipitation),
        len(humidity),
        len(wind_speed),
        len(pressure),
    )

    rows = []

    valid_times = []

    for index in range(sample_count):

        try:

            values = [
                float(precipitation[index]),
                float(humidity[index]),
                float(wind_speed[index]) / 3.6,
                float(pressure[index]),
                float(recent_rainfall),
                float(rolling_3_day),
                float(rolling_7_day),
            ]

        except (
            TypeError,
            ValueError,
        ):

            continue

        if not np.isfinite(
            values
        ).all():

            continue

        rows.append(values)
        valid_times.append(
            times[index]
        )

    if not rows:

        raise ValueError(
            "No valid NWP feature rows "
            "could be created."
        )

    X = np.asarray(
        rows,
        dtype=np.float32,
    )

    return X, valid_times


# ============================================================
# POST-PROCESS NWP
# ============================================================

def postprocess_forecast(
    X: np.ndarray,
) -> np.ndarray:
    """
    Apply the trained NWP post-processing model.
    """

    payload = load_model_payload()

    validate_model_payload(
        payload
    )

    model = payload["model"]

    if X.ndim != 2:
        raise ValueError(
            "NWP feature matrix must be 2-dimensional."
        )

    if X.shape[1] != len(
        FEATURE_NAMES
    ):
        raise ValueError(
            f"Expected {len(FEATURE_NAMES)} features, "
            f"received {X.shape[1]}."
        )

    predictions = model.predict(X)

    predictions = np.asarray(
        predictions,
        dtype=np.float32,
    )

    predictions = np.maximum(
        predictions,
        0.0,
    )

    return predictions


# ============================================================
# COMPLETE 72-HOUR FORECAST
# ============================================================

def generate_nwp_forecast() -> dict[str, Any]:
    """
    Complete NWP rainfall prediction pipeline.
    """

    print(
        "\n========================================"
    )
    print(
        "       VARSHAAI NWP FORECAST"
    )
    print(
        "========================================"
    )

    print(
        "Model path:",
        MODEL_PATH,
    )

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"NWP model not found:\n{MODEL_PATH}"
        )

    print(
        "Model found: YES"
    )

    print(
        "\nFetching GFS forecast..."
    )

    forecast = fetch_gfs_forecast()

    print(
        "GFS forecast received."
    )

    print(
        "\nFetching recent rainfall..."
    )

    historical = (
        fetch_recent_historical_rainfall()
    )

    print(
        "Historical rainfall status:",
        historical.get(
            "status"
        ),
    )

    observations = historical.get(
        "observations",
        [],
    )

    rainfall_features = (
        calculate_open_meteo_rainfall_features(
            observations
        )
    )

    print(
        "\nRainfall features:"
    )

    print(
        "  Recent rainfall:",
        rainfall_features.get(
            "recent_rainfall_mm"
        ),
        "mm",
    )

    print(
        "  Rolling 3-day:",
        rainfall_features.get(
            "rolling_3_day_rainfall_mm"
        ),
        "mm",
    )

    print(
        "  Rolling 7-day:",
        rainfall_features.get(
            "rolling_7_day_rainfall_mm"
        ),
        "mm",
    )

    print(
        "\nBuilding NWP features..."
    )

    X, valid_times = (
        build_nwp_feature_matrix(
            forecast,
            rainfall_features,
        )
    )

    print(
        "Feature matrix:",
        X.shape,
    )

    print(
        "\nApplying NWP post-processing model..."
    )

    predictions = postprocess_forecast(
        X
    )

    print(
        "Predictions generated:",
        len(predictions),
    )

    forecast_rows = []

    for index, timestamp in enumerate(
        valid_times
    ):

        forecast_rows.append(
            {
                "timestamp_utc": timestamp,
                "rainfall_prediction_mm": float(
                    predictions[index]
                ),
            }
        )

    print(
        "\nNWP forecast completed."
    )

    print(
        "========================================"
    )

    return {
        "status": "success",
        "location": {
            "name": "Chennai",
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
        },
        "model": (
            "rainguard_nwp_postprocessor"
        ),
        "nwp_source": (
            "Open-Meteo GFS"
        ),
        "historical_rainfall_source": (
            historical.get(
                "source"
            )
        ),
        "feature_names": FEATURE_NAMES,
        "forecast_hours": len(
            forecast_rows
        ),
        "forecast": forecast_rows,
    }


# ============================================================
# SIMPLE MODEL TEST
# ============================================================

def test_model() -> None:
    """
    Test only the trained model file.
    """

    print(
        "\n===== VARSHAAI NWP MODEL TEST ====="
    )

    print(
        "Model path:",
        MODEL_PATH,
    )

    print(
        "Exists:",
        MODEL_PATH.exists(),
    )

    payload = load_model_payload()

    validate_model_payload(
        payload
    )

    print(
        "Model loaded successfully."
    )

    print(
        "Feature names:"
    )

    for index, name in enumerate(
        FEATURE_NAMES,
        start=1,
    ):

        print(
            f"  {index}. {name}"
        )

    print(
        "===== MODEL TEST PASSED ====="
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        test_model()

        print(
            "\n===== RUNNING FULL NWP TEST ====="
        )

        result = (
            generate_nwp_forecast()
        )

        print(
            "\nSUCCESS!"
        )

        print(
            "Forecast records:",
            result["forecast_hours"],
        )

        print(
            "\nFirst 5 predictions:"
        )

        for item in result[
            "forecast"
        ][:5]:

            print(
                f"  {item['timestamp_utc']} "
                f"-> "
                f"{item['rainfall_prediction_mm']:.3f} mm"
            )

    except Exception as error:

        print(
            "\n========================================"
        )
        print(
            "          NWP TEST FAILED"
        )
        print(
            "========================================"
        )

        print(
            repr(error)
        )

        raise
    # ============================================================
# COMPLETE NWP FEATURE MATRIX
# ============================================================

def _complete_nwp_feature_matrix(
    forecast: dict[str, Any],
    rainfall_features: dict[str, Any],
) -> tuple[np.ndarray, list[str]]:
    """
    Build the seven-feature matrix required by the trained
    NWP post-processing model.
    """

    hourly = forecast.get("hourly", {})

    times = hourly.get("time", [])
    precipitation = hourly.get("precipitation", [])
    humidity = hourly.get("relative_humidity_2m", [])
    wind_speed = hourly.get("wind_speed_10m", [])
    pressure = hourly.get("pressure_msl", [])

    recent = rainfall_features.get(
        "recent_rainfall_mm"
    )
    rolling_3 = rainfall_features.get(
        "rolling_3_day_rainfall_mm"
    )
    rolling_7 = rainfall_features.get(
        "rolling_7_day_rainfall_mm"
    )

    if recent is None:
        recent = 0.0

    if rolling_3 is None:
        rolling_3 = 0.0

    if rolling_7 is None:
        rolling_7 = 0.0

    sample_count = min(
        len(times),
        len(precipitation),
        len(humidity),
        len(wind_speed),
        len(pressure),
    )

    rows = []
    valid_times = []

    for index in range(sample_count):

        try:
            row = [
                float(precipitation[index]),
                float(humidity[index]),
                float(wind_speed[index]) / 3.6,
                float(pressure[index]),
                float(recent),
                float(rolling_3),
                float(rolling_7),
            ]

        except (TypeError, ValueError):
            continue

        if not np.isfinite(row).all():
            continue

        rows.append(row)
        valid_times.append(times[index])

    if not rows:
        raise ValueError(
            "No valid NWP feature rows could be created."
        )

    X = np.asarray(
        rows,
        dtype=np.float32,
    )

    return X, valid_times


# ============================================================
# GENERATE POST-PROCESSED FORECAST
# ============================================================

def generate_postprocessed_forecast() -> dict[str, Any]:
    """
    Generate a 72-hour NWP rainfall forecast and apply the
    trained HistGradientBoosting post-processing model.
    """

    print()
    print("========================================")
    print("       VARSHAAI NWP FORECAST")
    print("========================================")

    print(
        f"Model path: {MODEL_PATH}"
    )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}"
        )

    print("Model found: YES")

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    payload = load_model_payload()

    model = payload.get("model")

    if model is None:
        raise ValueError(
            "Model payload does not contain 'model'."
        )

    feature_names = payload.get(
        "feature_names",
        FEATURE_NAMES,
    )

    if len(feature_names) != 7:
        raise ValueError(
            f"Expected 7 model features, "
            f"received {len(feature_names)}."
        )

    # --------------------------------------------------------
    # FETCH NWP
    # --------------------------------------------------------

    print()
    print("Fetching GFS forecast...")

    forecast = fetch_gfs_forecast()

    print("GFS forecast received.")

    # --------------------------------------------------------
    # FETCH RECENT RAINFALL
    # --------------------------------------------------------

    print()
    print("Fetching recent rainfall...")

    rainfall_history = (
        fetch_recent_historical_rainfall()
    )

    print(
        "Historical rainfall status:",
        rainfall_history.get(
            "status",
            "unknown",
        ),
    )

    observations = rainfall_history.get(
        "observations",
        [],
    )

    rainfall_features = (
        calculate_open_meteo_rainfall_features(
            observations
        )
    )

    print()
    print("Rainfall features:")
    print(
        "  Recent rainfall:",
        rainfall_features.get(
            "recent_rainfall_mm"
        ),
        "mm",
    )
    print(
        "  Rolling 3-day:",
        rainfall_features.get(
            "rolling_3_day_rainfall_mm"
        ),
        "mm",
    )
    print(
        "  Rolling 7-day:",
        rainfall_features.get(
            "rolling_7_day_rainfall_mm"
        ),
        "mm",
    )

    # --------------------------------------------------------
    # BUILD FEATURES
    # --------------------------------------------------------

    print()
    print("Building NWP features...")

    X, valid_times = (
        _complete_nwp_feature_matrix(
            forecast,
            rainfall_features,
        )
    )

    print(
        "Feature matrix:",
        X.shape,
    )

    # --------------------------------------------------------
    # VERIFY FEATURE ORDER
    # --------------------------------------------------------

    expected_features = [
        "nwp_precipitation_mm",
        "nwp_humidity",
        "nwp_wind_speed_ms",
        "nwp_pressure_hpa",
        "recent_rainfall_mm",
        "rolling_3_day_rainfall_mm",
        "rolling_7_day_rainfall_mm",
    ]

    if list(feature_names) != expected_features:
        raise ValueError(
            "Model feature order does not match "
            "the expected NWP feature order."
        )

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    print()
    print(
        "Applying NWP post-processing model..."
    )

    predictions = model.predict(X)

    predictions = np.asarray(
        predictions,
        dtype=np.float32,
    )

    predictions = np.maximum(
        predictions,
        0.0,
    )

    print(
        "Predictions generated:",
        len(predictions),
    )

    # --------------------------------------------------------
    # BUILD RESPONSE
    # --------------------------------------------------------

    records = []

    for timestamp, prediction, row in zip(
        valid_times,
        predictions,
        X,
    ):

        records.append(
            {
                "timestamp_utc": timestamp,
                "nwp_precipitation_mm": float(
                    row[0]
                ),
                "nwp_humidity": float(
                    row[1]
                ),
                "nwp_wind_speed_ms": float(
                    row[2]
                ),
                "nwp_pressure_hpa": float(
                    row[3]
                ),
                "recent_rainfall_mm": float(
                    row[4]
                ),
                "rolling_3_day_rainfall_mm": float(
                    row[5]
                ),
                "rolling_7_day_rainfall_mm": float(
                    row[6]
                ),
                "postprocessed_rainfall_mm": float(
                    prediction
                ),
            }
        )

    print()
    print(
        "NWP forecast completed."
    )
    print(
        "========================================"
    )

    return {
        "status": "success",
        "location": {
            "name": "Chennai",
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
        },
        "forecast_hours": len(records),
        "model": {
            "type": type(model).__name__,
            "file": MODEL_PATH.name,
            "features": list(feature_names),
        },
        "rainfall_history": {
            "source": rainfall_history.get(
                "source"
            ),
            "provider": rainfall_history.get(
                "provider"
            ),
            "status": rainfall_history.get(
                "status"
            ),
            "history_available": rainfall_features.get(
                "history_available",
                False,
            ),
            "recent_rainfall_mm": rainfall_features.get(
                "recent_rainfall_mm"
            ),
            "rolling_3_day_rainfall_mm": rainfall_features.get(
                "rolling_3_day_rainfall_mm"
            ),
            "rolling_7_day_rainfall_mm": rainfall_features.get(
                "rolling_7_day_rainfall_mm"
            ),
        },
        "records": records,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("===== VARSHAAI NWP MODEL TEST =====")

    print(
        "Model path:",
        MODEL_PATH,
    )

    print(
        "Exists:",
        MODEL_PATH.exists(),
    )

    payload = load_model_payload()

    print(
        "Model loaded successfully."
    )

    feature_names = payload.get(
        "feature_names",
        FEATURE_NAMES,
    )

    print(
        "Feature names:"
    )

    for index, name in enumerate(
        feature_names,
        start=1,
    ):
        print(
            f"  {index}. {name}"
        )

    print(
        "===== MODEL TEST PASSED ====="
    )

    print()
    print(
        "===== RUNNING FULL NWP TEST ====="
    )

    result = generate_postprocessed_forecast()

    print()
    print("SUCCESS!")
    print(
        "Forecast records:",
        result["forecast_hours"],
    )

    print()
    print("First 5 predictions:")

    for record in result["records"][:5]:

        print(
            f"  "
            f"{record['timestamp_utc']} "
            f"-> "
            f"{record['postprocessed_rainfall_mm']:.3f} mm"
        )