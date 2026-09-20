"""
VARSHAAI - Historical Rainfall Feature Engineering

Uses the real IMD 0.25-degree daily rainfall dataset.

Historical source:
    IMD RF25_ind2015_rfp25.nc

Selected valid Chennai-area grid:
    Latitude  : 13.25
    Longitude : 80.25

IMPORTANT:
    This historical dataset is from 2015.
    It is used for historical feature engineering
    and model-supporting analysis, NOT as live 2026
    rainfall observations.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .imd_loader import load_imd_rainfall


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

CHENNAI_AREA_LAT = 13.25
CHENNAI_AREA_LON = 80.25

HISTORICAL_YEAR = 2015


# ---------------------------------------------------------
# Load Chennai-area rainfall series
# ---------------------------------------------------------

def load_chennai_area_rainfall() -> pd.DataFrame:
    """
    Load the IMD daily rainfall time series for the
    selected valid Chennai-area grid cell.
    """

    rainfall = load_imd_rainfall()

    series = rainfall.sel(
        LATITUDE=CHENNAI_AREA_LAT,
        LONGITUDE=CHENNAI_AREA_LON,
        method="nearest",
    )

    values = np.asarray(
        series.values,
        dtype=np.float64,
    )

    dates = pd.to_datetime(
        rainfall.TIME.values
    )

    dataframe = pd.DataFrame(
        {
            "date": dates,
            "rainfall_mm": values,
        }
    )

    dataframe["latitude"] = float(
        series.LATITUDE.values
    )

    dataframe["longitude"] = float(
        series.LONGITUDE.values
    )

    return dataframe


# ---------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------

def build_historical_features() -> pd.DataFrame:
    """
    Build rainfall temporal features.

    Features:
        recent_rainfall_mm
        rolling_3_day_rainfall_mm
        rolling_7_day_rainfall_mm
    """

    dataframe = load_chennai_area_rainfall()

    dataframe = dataframe.sort_values(
        "date"
    ).reset_index(drop=True)

    rainfall = dataframe[
        "rainfall_mm"
    ]

    # Recent daily rainfall.
    dataframe[
        "recent_rainfall_mm"
    ] = rainfall

    # Rolling rainfall windows.
    #
    # min_periods is intentionally equal to the
    # window size. This prevents incomplete windows
    # from being silently treated as valid features.

    dataframe[
        "rolling_3_day_rainfall_mm"
    ] = rainfall.rolling(
        window=3,
        min_periods=3,
    ).sum()

    dataframe[
        "rolling_7_day_rainfall_mm"
    ] = rainfall.rolling(
        window=7,
        min_periods=7,
    ).sum()

    return dataframe


# ---------------------------------------------------------
# Latest complete feature row
# ---------------------------------------------------------

def get_latest_complete_features() -> dict:
    """
    Return the latest row for which all three historical
    rainfall features are genuinely available.
    """

    dataframe = build_historical_features()

    required = [
        "recent_rainfall_mm",
        "rolling_3_day_rainfall_mm",
        "rolling_7_day_rainfall_mm",
    ]

    valid = dataframe[
        required
    ].notna().all(axis=1)

    valid_rows = dataframe[
        valid
    ]

    if valid_rows.empty:
        return {
            "status": "unavailable",
            "reason": (
                "No complete historical rainfall "
                "window is available."
            ),
        }

    row = valid_rows.iloc[-1]

    return {
        "status": "available",
        "source": "IMD",
        "dataset": "RF25_ind2015_rfp25.nc",
        "year": HISTORICAL_YEAR,
        "region": (
            "Chennai-area IMD grid cell"
        ),
        "latitude": float(
            row["latitude"]
        ),
        "longitude": float(
            row["longitude"]
        ),
        "date": row[
            "date"
        ].isoformat(),
        "recent_rainfall_mm": float(
            row[
                "recent_rainfall_mm"
            ]
        ),
        "rolling_3_day_rainfall_mm": float(
            row[
                "rolling_3_day_rainfall_mm"
            ]
        ),
        "rolling_7_day_rainfall_mm": float(
            row[
                "rolling_7_day_rainfall_mm"
            ]
        ),
        "historical_feature_status": (
            "complete"
        ),
        "live_data": False,
        "note": (
            "Historical IMD rainfall used for "
            "feature engineering. This is not "
            "current 2026 rainfall."
        ),
    }


# ---------------------------------------------------------
# Full feature table summary
# ---------------------------------------------------------

def get_feature_summary() -> dict:
    """
    Return summary information about the historical
    feature-engineering dataset.
    """

    dataframe = build_historical_features()

    required = [
        "recent_rainfall_mm",
        "rolling_3_day_rainfall_mm",
        "rolling_7_day_rainfall_mm",
    ]

    complete = dataframe[
        required
    ].notna().all(axis=1)

    return {
        "status": "success",
        "source": "IMD",
        "dataset": "RF25_ind2015_rfp25.nc",
        "year": HISTORICAL_YEAR,
        "grid": {
            "latitude": CHENNAI_AREA_LAT,
            "longitude": CHENNAI_AREA_LON,
        },
        "total_days": int(
            len(dataframe)
        ),
        "complete_feature_days": int(
            complete.sum()
        ),
        "incomplete_feature_days": int(
            (~complete).sum()
        ),
        "feature_columns": required,
        "rainfall_unit": "mm/day",
        "live_data": False,
        "note": (
            "No missing historical values are "
            "converted to zero."
        ),
    }


# ---------------------------------------------------------
# Command-line test
# ---------------------------------------------------------

if __name__ == "__main__":

    print()
    print(
        "VARSHAAI Historical Rainfall Features"
    )
    print(
        "======================================"
    )

    print(
        f"Grid latitude : "
        f"{CHENNAI_AREA_LAT}"
    )

    print(
        f"Grid longitude: "
        f"{CHENNAI_AREA_LON}"
    )

    summary = get_feature_summary()

    print(
        "\nTotal days:",
        summary["total_days"],
    )

    print(
        "Complete feature days:",
        summary[
            "complete_feature_days"
        ],
    )

    latest = (
        get_latest_complete_features()
    )

    print(
        "\nLatest complete feature row:"
    )

    for key, value in latest.items():
        print(
            f"{key}: {value}"
        )