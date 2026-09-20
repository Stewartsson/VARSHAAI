from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import json

import joblib
import numpy as np
import requests

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# CONFIG
# ============================================================

LAT = 13.0827
LON = 80.2707

START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data" / "nwp_training"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "rainguard_nwp_postprocessor.joblib"
DATA_PATH = DATA_DIR / "chennai_nwp_training.json"


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
# DOWNLOAD HISTORICAL GFS FORECAST DATA
# ============================================================

def download_historical_gfs():

    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": START_DATE,
        "end_date": END_DATE,

        "hourly": ",".join([
            "precipitation",
            "relative_humidity_2m",
            "wind_speed_10m",
            "surface_pressure",
        ]),

        "models": "gfs_global",
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timezone": "UTC",
    }

    print()
    print("Downloading historical GFS data...")
    print("Start:", START_DATE)
    print("End  :", END_DATE)

    response = requests.get(
        url,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    if "hourly" not in data:
        raise RuntimeError(
            "Historical GFS response does not contain hourly data."
        )

    print("Historical GFS download successful.")

    return data


# ============================================================
# DOWNLOAD HISTORICAL OBSERVED RAINFALL
# ============================================================

def download_observed_rainfall():

    """
    Development-stage observation source.

    Uses Open-Meteo historical weather data as the observed
    rainfall reference for pipeline validation.

    This is NOT claimed to be IMD station rainfall.
    """

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": START_DATE,
        "end_date": END_DATE,

        "hourly": "precipitation",

        "precipitation_unit": "mm",
        "timezone": "UTC",
    }

    print()
    print("Downloading historical rainfall reference...")

    response = requests.get(
        url,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    if "hourly" not in data:
        raise RuntimeError(
            "Historical rainfall response does not contain hourly data."
        )

    print("Historical rainfall download successful.")

    return data


# ============================================================
# BUILD OBSERVATION LOOKUP
# ============================================================

def build_observation_lookup(data):

    times = data["hourly"]["time"]
    rain = data["hourly"]["precipitation"]

    lookup = {}

    for timestamp, value in zip(times, rain):

        if value is None:
            continue

        lookup[timestamp] = float(value)

    return lookup


# ============================================================
# ROLLING FEATURES
# ============================================================

def rainfall_features(
    rainfall_history,
    timestamp_index,
):

    recent = rainfall_history[
        max(0, timestamp_index - 1):
        timestamp_index
    ]

    three_day = rainfall_history[
        max(0, timestamp_index - 72):
        timestamp_index
    ]

    seven_day = rainfall_history[
        max(0, timestamp_index - 168):
        timestamp_index
    ]

    return (
        float(np.sum(recent)),
        float(np.sum(three_day)),
        float(np.sum(seven_day)),
    )


# ============================================================
# BUILD TRAINING DATA
# ============================================================

def build_training_dataset(
    gfs_data,
    observation_data,
):

    gfs_hourly = gfs_data["hourly"]

    gfs_times = gfs_hourly["time"]
    gfs_precip = gfs_hourly["precipitation"]
    gfs_humidity = gfs_hourly["relative_humidity_2m"]
    gfs_wind = gfs_hourly["wind_speed_10m"]
    gfs_pressure = gfs_hourly["surface_pressure"]

    observed_lookup = build_observation_lookup(
        observation_data
    )

    rows = []

    observation_series = []

    for timestamp in gfs_times:

        if timestamp not in observed_lookup:
            observation_series.append(np.nan)
        else:
            observation_series.append(
                observed_lookup[timestamp]
            )

    # Forward only genuine observations
    # are used for rolling features.

    for i, timestamp in enumerate(gfs_times):

        target = observed_lookup.get(timestamp)

        if target is None:
            continue

        p = gfs_precip[i]
        h = gfs_humidity[i]
        w = gfs_wind[i]
        pressure = gfs_pressure[i]

        if (
            p is None
            or h is None
            or w is None
            or pressure is None
        ):
            continue

        history = np.asarray(
            observation_series[:i],
            dtype=np.float32,
        )

        history = history[
            np.isfinite(history)
        ]

        if len(history) < 168:
            continue

        recent = float(
            np.sum(history[-1:])
        )

        rolling_3 = float(
            np.sum(history[-72:])
        )

        rolling_7 = float(
            np.sum(history[-168:])
        )

        rows.append({
            "timestamp_utc": timestamp,

            "nwp_precipitation_mm":
                float(p),

            "nwp_humidity":
                float(h),

            "nwp_wind_speed_ms":
                float(w),

            "nwp_pressure_hpa":
                float(pressure),

            "recent_rainfall_mm":
                recent,

            "rolling_3_day_rainfall_mm":
                rolling_3,

            "rolling_7_day_rainfall_mm":
                rolling_7,

            "observed_rainfall_mm":
                float(target),
        })

    return rows


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(rows):

    if len(rows) < 500:

        raise RuntimeError(
            f"Only {len(rows)} valid samples available. "
            "At least 500 samples are required."
        )

    X = np.array([
        [
            row["nwp_precipitation_mm"],
            row["nwp_humidity"],
            row["nwp_wind_speed_ms"],
            row["nwp_pressure_hpa"],
            row["recent_rainfall_mm"],
            row["rolling_3_day_rainfall_mm"],
            row["rolling_7_day_rainfall_mm"],
        ]
        for row in rows
    ], dtype=np.float32)

    y = np.array([
        row["observed_rainfall_mm"]
        for row in rows
    ], dtype=np.float32)

    # --------------------------------------------------------
    # Chronological split
    # --------------------------------------------------------

    split = int(
        len(X) * 0.80
    )

    X_train = X[:split]
    y_train = y[:split]

    X_test = X[split:]
    y_test = y[split:]

    print()
    print("TRAINING")
    print("--------")
    print("Total samples :", len(X))
    print("Training      :", len(X_train))
    print("Testing       :", len(X_test))

    model = HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    predictions = np.maximum(
        predictions,
        0.0,
    )

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions,
        )
    )

    r2 = r2_score(
        y_test,
        predictions,
    )

    print()
    print("VALIDATION")
    print("----------")
    print(f"MAE  : {mae:.4f} mm")
    print(f"RMSE : {rmse:.4f} mm")
    print(f"R²   : {r2:.4f}")

    payload = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "random_state": 42,

        "training_metadata": {
            "training_source":
                "Open-Meteo Historical Forecast GFS",

            "observation_reference":
                "Open-Meteo Historical Weather",

            "start_date":
                START_DATE,

            "end_date":
                END_DATE,

            "sample_count":
                len(X),

            "train_samples":
                len(X_train),

            "test_samples":
                len(X_test),

            "mae_mm":
                float(mae),

            "rmse_mm":
                float(rmse),

            "r2":
                float(r2),
        },
    }

    joblib.dump(
        payload,
        MODEL_PATH,
    )

    print()
    print("MODEL SAVED")
    print("-----------")
    print(MODEL_PATH)

    return payload


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("VARSHAAI - REAL NWP POST-PROCESSING TRAINING")
    print("=" * 60)

    gfs = download_historical_gfs()

    observations = download_observed_rainfall()

    rows = build_training_dataset(
        gfs,
        observations,
    )

    print()
    print("Valid aligned samples:", len(rows))

    if len(rows) == 0:
        raise RuntimeError(
            "No aligned training samples were generated."
        )

    with open(
        DATA_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            rows,
            f,
            indent=2,
        )

    print(
        "Training dataset saved:",
        DATA_PATH,
    )

    train_model(
        rows
    )

    print()
    print("=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()