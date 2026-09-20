"""
VARSHAAI
INSAT-3DR HEM Time-Series Processor

Purpose
-------
Process all downloaded INSAT-3DR HEM precipitation products and create
a Chennai-focused rainfall time series.

Source:
    INSAT-3DR
Product:
    3RIMG_L2B_HEM

Output:
    backend/data/mosdac/processed/chennai_hem_timeseries.csv
    backend/data/mosdac/processed/chennai_hem_timeseries.json

Important:
    - Uses the existing hem_reader.py for Chennai coordinate extraction.
    - Does NOT fabricate missing observations.
    - Preserves actual satellite timestamps.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

from app.data_sources.mosdac.hem_reader import (
    get_chennai_rainfall,
    get_chennai_statistics,
)


# ============================================================
# CONFIGURATION
# ============================================================

SATELLITE = "INSAT-3DR"
PRODUCT = "3RIMG_L2B_HEM"

# This file is:
# backend/app/data_sources/mosdac/hem_timeseries.py
#
# parents[0] -> mosdac
# parents[1] -> data_sources
# parents[2] -> app
# parents[3] -> backend
BACKEND_DIR = Path(__file__).resolve().parents[3]

HEM_DIRECTORY = BACKEND_DIR / "data" / "mosdac" / "hem"

PROCESSED_DIRECTORY = (
    BACKEND_DIR / "data" / "mosdac" / "processed"
)

CSV_OUTPUT = (
    PROCESSED_DIRECTORY / "chennai_hem_timeseries.csv"
)

JSON_OUTPUT = (
    PROCESSED_DIRECTORY / "chennai_hem_timeseries.json"
)

HEM_PATTERN = "*_L2B_HEM_*.h5"


# ============================================================
# HELPERS
# ============================================================

def safe_float(value: Any) -> float | None:
    """
    Convert a value to float safely.

    Returns None for invalid / missing values.
    """

    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    # Reject NaN / infinity.
    if result != result:
        return None

    if result == float("inf") or result == float("-inf"):
        return None

    return result


def get_hem_files() -> list[Path]:
    """
    Return HEM files sorted chronologically by filename.
    """

    if not HEM_DIRECTORY.exists():
        return []

    files = list(HEM_DIRECTORY.glob(HEM_PATTERN))

    return sorted(files, key=lambda p: p.name)


def extract_record(file_path: Path) -> dict[str, Any]:
    """
    Extract one Chennai observation from one HEM file.

    Uses the already-tested get_chennai_rainfall() function.
    """

    rainfall_result = get_chennai_rainfall(file_path)

    statistics_result = get_chennai_statistics(file_path)

    rainfall = safe_float(
        rainfall_result.get("rainfall_mm_hr")
    )

    latitude = safe_float(
        rainfall_result.get("latitude")
    )

    longitude = safe_float(
        rainfall_result.get("longitude")
    )

    distance_degrees = safe_float(
        rainfall_result.get("distance_degrees")
    )

    pixel_row = rainfall_result.get("pixel_row")
    pixel_column = rainfall_result.get("pixel_column")

    # Statistics
    minimum = safe_float(
        statistics_result.get("minimum_mm_hr")
    )

    maximum = safe_float(
        statistics_result.get("maximum_mm_hr")
    )

    area_mean = safe_float(
        statistics_result.get("mean_mm_hr")
    )

    area_median = safe_float(
        statistics_result.get("median_mm_hr")
    )

    valid_pixel_count = statistics_result.get(
        "valid_pixel_count"
    )

    return {
        "timestamp_utc": rainfall_result.get(
            "timestamp_utc"
        ),
        "timestamp_ist": rainfall_result.get(
            "timestamp_ist"
        ),

        "satellite": rainfall_result.get(
            "satellite",
            SATELLITE,
        ),

        "product": rainfall_result.get(
            "product",
            PRODUCT,
        ),

        "rainfall_mm_hr": rainfall,

        "chennai_pixel_latitude": latitude,

        "chennai_pixel_longitude": longitude,

        "pixel_row": pixel_row,

        "pixel_column": pixel_column,

        "distance_degrees": distance_degrees,

        "area_min_mm_hr": minimum,

        "area_max_mm_hr": maximum,

        "area_mean_mm_hr": area_mean,

        "area_median_mm_hr": area_median,

        "valid_pixel_count": valid_pixel_count,

        "source_file": rainfall_result.get(
            "source_file",
            file_path.name,
        ),

        "status": (
            "valid"
            if rainfall is not None
            else "no_valid_chennai_value"
        ),
    }


def process_files() -> list[dict[str, Any]]:
    """
    Process every HEM file.
    """

    files = get_hem_files()

    print()
    print("=" * 72)
    print("VARSHAAI - INSAT-3DR HEM TIME-SERIES PROCESSOR")
    print("=" * 72)

    print()
    print(f"HEM directory : {HEM_DIRECTORY}")
    print(f"Files found   : {len(files)}")

    if not files:
        print()
        print("ERROR: No HEM files found.")
        print(f"Expected directory: {HEM_DIRECTORY}")
        return []

    records: list[dict[str, Any]] = []

    for index, file_path in enumerate(files, start=1):

        print()
        print(
            f"[{index:02d}/{len(files):02d}] "
            f"{file_path.name}"
        )

        try:
            record = extract_record(file_path)

            timestamp_utc = record.get(
                "timestamp_utc"
            )

            timestamp_ist = record.get(
                "timestamp_ist"
            )

            rainfall = record.get(
                "rainfall_mm_hr"
            )

            print(
                f"  UTC       : {timestamp_utc}"
            )

            print(
                f"  IST       : {timestamp_ist}"
            )

            if rainfall is None:
                print(
                    "  Rainfall  : No valid value"
                )
            else:
                print(
                    f"  Rainfall  : "
                    f"{rainfall:.3f} mm/hr"
                )

            print(
                f"  Pixel     : "
                f"{record.get('chennai_pixel_latitude')}, "
                f"{record.get('chennai_pixel_longitude')}"
            )

            print(
                f"  Area mean : "
                f"{record.get('area_mean_mm_hr')} mm/hr"
            )

            print(
                f"  Valid px  : "
                f"{record.get('valid_pixel_count')}"
            )

            records.append(record)

        except Exception as exc:

            print(
                f"  ERROR     : {exc}"
            )

            # Keep the file in the time series as an error
            # record rather than silently dropping it.
            records.append(
                {
                    "timestamp_utc": None,
                    "timestamp_ist": None,
                    "satellite": SATELLITE,
                    "product": PRODUCT,
                    "rainfall_mm_hr": None,
                    "chennai_pixel_latitude": None,
                    "chennai_pixel_longitude": None,
                    "pixel_row": None,
                    "pixel_column": None,
                    "distance_degrees": None,
                    "area_min_mm_hr": None,
                    "area_max_mm_hr": None,
                    "area_mean_mm_hr": None,
                    "area_median_mm_hr": None,
                    "valid_pixel_count": None,
                    "source_file": file_path.name,
                    "status": "processing_error",
                    "error": str(exc),
                }
            )

    return records


# ============================================================
# TIME-SERIES SUMMARY
# ============================================================

def build_summary(
    records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Build summary statistics from valid observations.
    """

    valid_values = []

    for record in records:

        value = safe_float(
            record.get("rainfall_mm_hr")
        )

        if value is not None:
            valid_values.append(value)

    total_records = len(records)

    valid_records = len(valid_values)

    missing_records = (
        total_records - valid_records
    )

    summary: dict[str, Any] = {
        "total_files": total_records,
        "valid_chennai_observations": valid_records,
        "missing_chennai_observations": missing_records,
        "valid_fraction": (
            round(valid_records / total_records, 4)
            if total_records
            else 0.0
        ),
        "minimum_rainfall_mm_hr": None,
        "maximum_rainfall_mm_hr": None,
        "mean_rainfall_mm_hr": None,
        "median_rainfall_mm_hr": None,
    }

    if valid_values:

        summary[
            "minimum_rainfall_mm_hr"
        ] = round(min(valid_values), 3)

        summary[
            "maximum_rainfall_mm_hr"
        ] = round(max(valid_values), 3)

        summary[
            "mean_rainfall_mm_hr"
        ] = round(mean(valid_values), 3)

        summary[
            "median_rainfall_mm_hr"
        ] = round(median(valid_values), 3)

    return summary


# ============================================================
# GAP DETECTION
# ============================================================

def detect_time_gaps(
    records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Detect gaps between consecutive satellite observations.

    HEM is expected to provide approximately 30-minute
    observations, but the processor does not fabricate missing
    observations.
    """

    from datetime import datetime

    timestamps: list[tuple[datetime, str]] = []

    for record in records:

        timestamp = record.get(
            "timestamp_utc"
        )

        if not timestamp:
            continue

        try:
            parsed = datetime.fromisoformat(
                str(timestamp).replace(
                    "Z",
                    "+00:00",
                )
            )

            timestamps.append(
                (
                    parsed,
                    str(
                        record.get(
                            "source_file",
                            "",
                        )
                    ),
                )
            )

        except (TypeError, ValueError):
            continue

    timestamps.sort(key=lambda x: x[0])

    gaps: list[dict[str, Any]] = []

    for index in range(
        1,
        len(timestamps),
    ):

        previous_time = timestamps[
            index - 1
        ][0]

        current_time = timestamps[
            index
        ][0]

        difference_minutes = (
            current_time - previous_time
        ).total_seconds() / 60.0

        # A normal interval is 30 minutes.
        if difference_minutes > 30:

            gaps.append(
                {
                    "from_utc": previous_time.isoformat(),
                    "to_utc": current_time.isoformat(),
                    "gap_minutes": difference_minutes,
                }
            )

    return gaps


# ============================================================
# CSV
# ============================================================

def save_csv(
    records: list[dict[str, Any]]
) -> None:

    PROCESSED_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "timestamp_utc",
        "timestamp_ist",
        "satellite",
        "product",
        "rainfall_mm_hr",
        "chennai_pixel_latitude",
        "chennai_pixel_longitude",
        "pixel_row",
        "pixel_column",
        "distance_degrees",
        "area_min_mm_hr",
        "area_max_mm_hr",
        "area_mean_mm_hr",
        "area_median_mm_hr",
        "valid_pixel_count",
        "source_file",
        "status",
    ]

    with CSV_OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in records:

            row = {
                key: record.get(key)
                for key in fieldnames
            }

            writer.writerow(row)

    print()
    print(
        f"CSV saved: {CSV_OUTPUT}"
    )


# ============================================================
# JSON
# ============================================================

def save_json(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    gaps: list[dict[str, Any]],
) -> None:

    PROCESSED_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "project": "VARSHAAI",
        "satellite": SATELLITE,
        "product": PRODUCT,
        "region": "Chennai District, Tamil Nadu",
        "unit": "mm/hr",

        "processing": {
            "source": "MOSDAC",
            "description": (
                "INSAT-3DR Hydro Estimator "
                "precipitation time series"
            ),
            "expected_interval_minutes": 30,
            "missing_observations_preserved": True,
            "synthetic_values_added": False,
        },

        "summary": summary,

        "time_gaps": gaps,

        "observations": records,
    }

    with JSON_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"JSON saved: {JSON_OUTPUT}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    records = process_files()

    if not records:
        print()
        print("=" * 72)
        print("NO DATA PROCESSED")
        print("=" * 72)
        return

    summary = build_summary(
        records
    )

    gaps = detect_time_gaps(
        records
    )

    save_csv(
        records
    )

    save_json(
        records,
        summary,
        gaps,
    )

    print()
    print("=" * 72)
    print("TIME-SERIES SUMMARY")
    print("=" * 72)

    print(
        f"Total files              : "
        f"{summary['total_files']}"
    )

    print(
        f"Valid Chennai values     : "
        f"{summary['valid_chennai_observations']}"
    )

    print(
        f"Missing/invalid values   : "
        f"{summary['missing_chennai_observations']}"
    )

    print(
        f"Valid fraction           : "
        f"{summary['valid_fraction']}"
    )

    print(
        f"Minimum rainfall         : "
        f"{summary['minimum_rainfall_mm_hr']} mm/hr"
    )

    print(
        f"Maximum rainfall         : "
        f"{summary['maximum_rainfall_mm_hr']} mm/hr"
    )

    print(
        f"Mean rainfall            : "
        f"{summary['mean_rainfall_mm_hr']} mm/hr"
    )

    print(
        f"Median rainfall          : "
        f"{summary['median_rainfall_mm_hr']} mm/hr"
    )

    print()
    print(
        f"Detected time gaps       : "
        f"{len(gaps)}"
    )

    for gap in gaps:

        print(
            f"  {gap['from_utc']} → "
            f"{gap['to_utc']} "
            f"({gap['gap_minutes']} min)"
        )

    print()
    print("=" * 72)
    print("MOSDAC HEM TIME-SERIES PROCESSING COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()