from __future__ import annotations

import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException


# ============================================================
# VARSHAAI - MOSDAC HEM TIME-SERIES API
# ============================================================

router = APIRouter(
    prefix="/api/satellite/hem",
    tags=["MOSDAC HEM Time Series"],
)


# backend/
BACKEND_DIR = Path(__file__).resolve().parents[3]

CSV_FILE = (
    BACKEND_DIR
    / "data"
    / "mosdac"
    / "processed"
    / "chennai_hem_timeseries.csv"
)


# ============================================================
# READ CSV
# ============================================================

def read_timeseries():

    if not CSV_FILE.exists():

        raise FileNotFoundError(
            f"Time-series CSV not found: {CSV_FILE}"
        )

    observations = []

    with CSV_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:

            rainfall = row.get(
                "nearest_rainfall_mm_hr"
            )

            area_mean = row.get(
                "chennai_mean_mm_hr"
            )

            maximum = row.get(
                "chennai_max_mm_hr"
            )

            try:
                rainfall_value = (
                    float(rainfall)
                    if rainfall not in (
                        None,
                        "",
                        "None",
                    )
                    else None
                )

            except ValueError:
                rainfall_value = None

            try:
                area_mean_value = (
                    float(area_mean)
                    if area_mean not in (
                        None,
                        "",
                        "None",
                    )
                    else None
                )

            except ValueError:
                area_mean_value = None

            try:
                maximum_value = (
                    float(maximum)
                    if maximum not in (
                        None,
                        "",
                        "None",
                    )
                    else None
                )

            except ValueError:
                maximum_value = None

            observations.append(
                {
                    "timestamp_utc":
                        row.get(
                            "timestamp_utc"
                        ),

                    "timestamp_ist":
                        row.get(
                            "timestamp_ist"
                        ),

                    "rainfall_mm_hr":
                        rainfall_value,

                    "area_mean_mm_hr":
                        area_mean_value,

                    "area_max_mm_hr":
                        maximum_value,

                    "latitude":
                        _to_float(
                            row.get(
                                "nearest_latitude"
                            )
                        ),

                    "longitude":
                        _to_float(
                            row.get(
                                "nearest_longitude"
                            )
                        ),

                    "source_file":
                        row.get(
                            "source_file"
                        ),

                    "valid_pixels":
                        _to_int(
                            row.get(
                                "valid_pixels"
                            )
                        ),
                }
            )

    observations.sort(
        key=lambda item:
        item["timestamp_utc"] or ""
    )

    return observations


# ============================================================
# CONVERSION HELPERS
# ============================================================

def _to_float(value):

    try:

        if value in (
            None,
            "",
            "None",
        ):
            return None

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return None


def _to_int(value):

    try:

        if value in (
            None,
            "",
            "None",
        ):
            return None

        return int(float(value))

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# STATUS
# ============================================================

@router.get("/timeseries/status")
def timeseries_status():

    if not CSV_FILE.exists():

        return {
            "status": "pending",
            "source": "MOSDAC",
            "satellite": "INSAT-3DR",
            "product": "3RIMG_L2B_HEM",
            "region": "Chennai District",
            "csv_available": False,
            "file": str(CSV_FILE),
            "observations": 0,
        }

    try:

        observations = read_timeseries()

        return {
            "status": "available",
            "source": "MOSDAC",
            "satellite": "INSAT-3DR",
            "product": "3RIMG_L2B_HEM",
            "region": "Chennai District",
            "csv_available": True,
            "file": CSV_FILE.name,
            "observations": len(observations),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# COMPLETE TIME SERIES
# ============================================================

@router.get("/timeseries")
def get_timeseries():

    try:

        observations = read_timeseries()

        if not observations:

            return {
                "status": "empty",
                "source": "MOSDAC",
                "satellite": "INSAT-3DR",
                "product": "3RIMG_L2B_HEM",
                "region": "Chennai District",
                "count": 0,
                "observations": [],
            }

        rainfall_values = [
            item["rainfall_mm_hr"]
            for item in observations
            if item["rainfall_mm_hr"]
            is not None
        ]

        maximum_rainfall = (
            max(rainfall_values)
            if rainfall_values
            else 0.0
        )

        mean_rainfall = (
            sum(rainfall_values)
            / len(rainfall_values)
            if rainfall_values
            else 0.0
        )

        return {
            "status": "success",

            "source": "MOSDAC",

            "satellite": "INSAT-3DR",

            "product":
                "3RIMG_L2B_HEM",

            "region":
                "Chennai District",

            "units":
                "mm/hr",

            "count":
                len(observations),

            "maximum_rainfall_mm_hr":
                maximum_rainfall,

            "mean_rainfall_mm_hr":
                mean_rainfall,

            "observations":
                observations,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# LATEST OBSERVATION
# ============================================================

@router.get("/timeseries/latest")
def get_latest_timeseries_observation():

    try:

        observations = read_timeseries()

        if not observations:

            raise HTTPException(
                status_code=404,
                detail="No observations available.",
            )

        return {
            "status": "success",
            "source": "MOSDAC",
            "satellite": "INSAT-3DR",
            "product": "3RIMG_L2B_HEM",
            "region": "Chennai District",
            "observation":
                observations[-1],
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )