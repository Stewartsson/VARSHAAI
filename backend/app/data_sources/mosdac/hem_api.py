from pathlib import Path
import json

from fastapi import APIRouter, HTTPException

from app.data_sources.mosdac.hem_reader import (
    get_chennai_rainfall,
    get_chennai_statistics,
)


# ============================================================
# VARSHAAI
# MOSDAC INSAT-3DR HEM API
# ============================================================

router = APIRouter(
    prefix="/api/satellite/hem",
    tags=["MOSDAC Satellite HEM"],
)


# ============================================================
# DIRECTORIES
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[3]

HEM_DIRECTORY = (
    BACKEND_DIR
    / "data"
    / "mosdac"
    / "hem"
)

PROCESSED_DIRECTORY = (
    BACKEND_DIR
    / "data"
    / "mosdac"
    / "processed"
)

TIMESERIES_JSON = (
    PROCESSED_DIRECTORY
    / "chennai_hem_timeseries.json"
)


# ============================================================
# FIND LATEST HEM FILE
# ============================================================

def find_latest_hem_file():
    """
    Find the latest INSAT-3DR HEM HDF5 file
    available in the local MOSDAC data directory.
    """

    files = sorted(
        HEM_DIRECTORY.glob(
            "3RIMG_*_L2B_HEM_*.h5"
        )
    )

    if not files:
        return None

    return files[-1]


# ============================================================
# LATEST HEM OBSERVATION
# ============================================================

@router.get("/latest")
def get_latest_hem():

    file_path = find_latest_hem_file()

    if file_path is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "No INSAT-3DR HEM files found "
                "in the MOSDAC data directory."
            ),
        )

    try:

        result = get_chennai_rainfall(
            file_path
        )

        return {
            "status": "success",
            "source": "MOSDAC",
            "satellite": result["satellite"],
            "product": result["product"],
            "timestamp_utc": result[
                "timestamp_utc"
            ],
            "timestamp_ist": result[
                "timestamp_ist"
            ],
            "rainfall_mm_hr": result[
                "rainfall_mm_hr"
            ],
            "latitude": result[
                "latitude"
            ],
            "longitude": result[
                "longitude"
            ],
            "pixel_row": result[
                "pixel_row"
            ],
            "pixel_column": result[
                "pixel_column"
            ],
            "source_file": result[
                "source_file"
            ],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"HEM processing failed: {exc}",
        )


# ============================================================
# CHENNAI HEM STATISTICS
# ============================================================

@router.get("/chennai")
def get_chennai_hem_statistics():

    file_path = find_latest_hem_file()

    if file_path is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "No INSAT-3DR HEM files found "
                "in the MOSDAC data directory."
            ),
        )

    try:

        result = get_chennai_statistics(
            file_path
        )

        return {
            "status": result["status"],
            "source": "MOSDAC",
            "satellite": result.get(
                "satellite",
                "INSAT-3DR",
            ),
            "product": result.get(
                "product",
                "3RIMG_L2B_HEM",
            ),
            "timestamp_utc": result.get(
                "timestamp_utc"
            ),
            "timestamp_ist": result.get(
                "timestamp_ist"
            ),
            "rainfall_unit": result.get(
                "rainfall_unit",
                "mm/hr",
            ),
            "minimum_mm_hr": result.get(
                "minimum_mm_hr"
            ),
            "maximum_mm_hr": result.get(
                "maximum_mm_hr"
            ),
            "mean_mm_hr": result.get(
                "mean_mm_hr"
            ),
            "median_mm_hr": result.get(
                "median_mm_hr"
            ),
            "valid_pixel_count": result.get(
                "valid_pixel_count",
                0,
            ),
            "bounding_box": result.get(
                "bounding_box"
            ),
            "source_file": file_path.name,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"HEM statistics failed: {exc}",
        )


# ============================================================
# TIME-SERIES API
# ============================================================

@router.get("/timeseries")
def get_hem_timeseries():

    """
    Return the processed Chennai INSAT-3DR HEM
    rainfall time series.

    Data is generated by:
        hem_timeseries.py

    Source:
        MOSDAC INSAT-3DR HEM

    Unit:
        mm/hr
    """

    if not TIMESERIES_JSON.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "HEM time-series file not found. "
                "Run: "
                "python -m "
                "app.data_sources.mosdac.hem_timeseries"
            ),
        )

    try:

        with TIMESERIES_JSON.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return {
            "status": "success",
            "source": "MOSDAC",
            "satellite": data.get(
                "satellite",
                "INSAT-3DR",
            ),
            "product": data.get(
                "product",
                "3RIMG_L2B_HEM",
            ),
            "region": data.get(
                "region",
                "Chennai District, Tamil Nadu",
            ),
            "unit": data.get(
                "unit",
                "mm/hr",
            ),
            "processing": data.get(
                "processing",
                {},
            ),
            "summary": data.get(
                "summary",
                {},
            ),
            "time_gaps": data.get(
                "time_gaps",
                [],
            ),
            "observations": data.get(
                "observations",
                [],
            ),
        }

    except json.JSONDecodeError as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "HEM time-series JSON is invalid: "
                f"{exc}"
            ),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to read HEM time-series: "
                f"{exc}"
            ),
        )


# ============================================================
# HEM STATUS
# ============================================================

@router.get("/status")
def get_hem_status():

    files = sorted(
        HEM_DIRECTORY.glob(
            "3RIMG_*_L2B_HEM_*.h5"
        )
    )

    latest_file = (
        files[-1].name
        if files
        else None
    )

    timeseries_available = (
        TIMESERIES_JSON.exists()
    )

    return {
        "status": "available"
        if files
        else "pending",

        "source": "MOSDAC",

        "satellite": "INSAT-3DR",

        "product": "3RIMG_L2B_HEM",

        "files_available": len(files),

        "latest_file": latest_file,

        "timeseries_available": (
            timeseries_available
        ),

        "timeseries_file": (
            TIMESERIES_JSON.name
            if timeseries_available
            else None
        ),

        "data_directory": str(
            HEM_DIRECTORY
        ),
    }