from __future__ import annotations

import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path

import h5py
import numpy as np


# ============================================================
# VARSHAAI
# INSAT-3DR HEM TIME-SERIES PROCESSOR
# ============================================================

SATELLITE = "INSAT-3DR"
PRODUCT = "3RIMG_L2B_HEM"

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707

BACKEND_DIR = Path(__file__).resolve().parent

HEM_DIRECTORY = (
    BACKEND_DIR
    / "data"
    / "mosdac"
    / "hem"
)

OUTPUT_DIRECTORY = (
    BACKEND_DIR
    / "data"
    / "mosdac"
    / "processed"
)

OUTPUT_FILE = (
    OUTPUT_DIRECTORY
    / "chennai_hem_timeseries.csv"
)

DEFAULT_FILL_VALUE = -999.0


# ============================================================
# ATTRIBUTE HELPERS
# ============================================================

def decode_attribute(value):
    """
    Convert HDF5 attributes into normal Python values.

    MOSDAC attributes may appear as:
        scalar
        numpy scalar
        numpy array
        list
        bytes
    """

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="ignore"
        )

    if isinstance(value, np.ndarray):

        if value.size == 1:
            return decode_attribute(
                value.reshape(-1)[0]
            )

        return [
            decode_attribute(item)
            for item in value.tolist()
        ]

    if isinstance(value, list):

        if len(value) == 1:
            return decode_attribute(
                value[0]
            )

        return [
            decode_attribute(item)
            for item in value
        ]

    if isinstance(value, tuple):

        if len(value) == 1:
            return decode_attribute(
                value[0]
            )

        return [
            decode_attribute(item)
            for item in value
        ]

    if isinstance(value, np.generic):
        return value.item()

    return value


def get_numeric_attribute(
    dataset,
    name,
    default=0.0,
):
    """
    Safely read a numeric HDF5 attribute.

    Handles scalar, list and numpy-array attributes.
    """

    value = dataset.attrs.get(
        name,
        default,
    )

    value = decode_attribute(value)

    if isinstance(value, list):

        if len(value) == 0:
            return float(default)

        value = value[0]

    if isinstance(value, tuple):

        if len(value) == 0:
            return float(default)

        value = value[0]

    try:
        return float(value)

    except (TypeError, ValueError):

        return float(default)


# ============================================================
# COORDINATE READER
# ============================================================

def read_coordinate(dataset):
    """
    Read latitude/longitude from MOSDAC HDF5.

    Supports scale_factor and add_offset.
    """

    values = np.asarray(
        dataset[:],
        dtype=float,
    )

    scale_factor = get_numeric_attribute(
        dataset,
        "scale_factor",
        1.0,
    )

    add_offset = get_numeric_attribute(
        dataset,
        "add_offset",
        0.0,
    )

    values = (
        values * scale_factor
        + add_offset
    )

    # Handle common coordinate fill value.
    values[
        values == 32767
    ] = np.nan

    values[
        values == -999
    ] = np.nan

    return values


# ============================================================
# TIME DECODER
# ============================================================

def decode_time(dataset):
    """
    Decode MOSDAC HEM time.

    Expected format:
    minutes since 2000-01-01 00:00:00 UTC
    """

    raw_value = np.asarray(
        dataset[:]
    ).squeeze()

    # If the value is an array, take first element.
    if isinstance(raw_value, np.ndarray):

        if raw_value.size == 0:
            raise ValueError(
                "Empty time dataset."
            )

        raw_value = raw_value.reshape(-1)[0]

    raw_value = float(raw_value)

    epoch = datetime(
        2000,
        1,
        1,
        tzinfo=timezone.utc,
    )

    return epoch + timedelta(
        minutes=raw_value
    )


# ============================================================
# FIND NEAREST PIXEL
# ============================================================

def find_nearest_pixel(
    latitude,
    longitude,
    rainfall,
    target_lat=CHENNAI_LAT,
    target_lon=CHENNAI_LON,
):
    """
    Find the nearest valid HEM pixel to Chennai.
    """

    lat = np.asarray(
        latitude,
        dtype=float,
    )

    lon = np.asarray(
        longitude,
        dtype=float,
    )

    rain = np.asarray(
        rainfall,
        dtype=float,
    )

    valid = (
        np.isfinite(lat)
        & np.isfinite(lon)
        & np.isfinite(rain)
    )

    if not np.any(valid):

        raise ValueError(
            "No valid HEM pixels available."
        )

    distance = (
        (lat - target_lat) ** 2
        +
        (lon - target_lon) ** 2
    )

    distance[
        ~valid
    ] = np.inf

    flat_index = np.argmin(
        distance
    )

    row, column = np.unravel_index(
        flat_index,
        distance.shape,
    )

    return {
        "latitude": float(
            lat[row, column]
        ),

        "longitude": float(
            lon[row, column]
        ),

        "rainfall_mm_hr": float(
            rain[row, column]
        ),

        "row": int(row),

        "column": int(column),
    }


# ============================================================
# PROCESS ONE HEM FILE
# ============================================================

def process_hem_file(
    file_path: Path
):

    print()
    print(
        f"Processing: {file_path.name}"
    )

    with h5py.File(
        file_path,
        "r"
    ) as hdf:

        # ----------------------------------------------------
        # Required datasets
        # ----------------------------------------------------

        if "HEM" not in hdf:
            raise ValueError(
                "HEM dataset not found."
            )

        if "Latitude" not in hdf:
            raise ValueError(
                "Latitude dataset not found."
            )

        if "Longitude" not in hdf:
            raise ValueError(
                "Longitude dataset not found."
            )

        if "time" not in hdf:
            raise ValueError(
                "time dataset not found."
            )

        hem_dataset = hdf[
            "HEM"
        ]

        latitude_dataset = hdf[
            "Latitude"
        ]

        longitude_dataset = hdf[
            "Longitude"
        ]

        time_dataset = hdf[
            "time"
        ]

        # ----------------------------------------------------
        # Read rainfall
        # ----------------------------------------------------

        rainfall = np.asarray(
            hem_dataset[:],
            dtype=float,
        )

        # MOSDAC HEM can contain:
        #
        # (1, 2816, 2805)
        #
        # Remove singleton dimension.

        rainfall = np.squeeze(
            rainfall
        )

        if rainfall.ndim != 2:

            raise ValueError(
                f"Unexpected HEM shape: "
                f"{rainfall.shape}"
            )

        # ----------------------------------------------------
        # Fill value
        # ----------------------------------------------------

        fill_value = get_numeric_attribute(
            hem_dataset,
            "_FillValue",
            DEFAULT_FILL_VALUE,
        )

        rainfall[
            rainfall == fill_value
        ] = np.nan

        rainfall[
            rainfall == DEFAULT_FILL_VALUE
        ] = np.nan

        # ----------------------------------------------------
        # Read coordinates
        # ----------------------------------------------------

        latitude = read_coordinate(
            latitude_dataset
        )

        longitude = read_coordinate(
            longitude_dataset
        )

        # ----------------------------------------------------
        # Decode timestamp
        # ----------------------------------------------------

        timestamp = decode_time(
            time_dataset
        )

        # ----------------------------------------------------
        # Find nearest Chennai pixel
        # ----------------------------------------------------

        pixel = find_nearest_pixel(
            latitude=latitude,
            longitude=longitude,
            rainfall=rainfall,
        )

        # ----------------------------------------------------
        # Chennai area
        #
        # Approximate bounding box:
        #
        # Latitude:
        # 12.8 - 13.4
        #
        # Longitude:
        # 79.9 - 80.6
        # ----------------------------------------------------

        area_mask = (
            (latitude >= 12.8)
            &
            (latitude <= 13.4)
            &
            (longitude >= 79.9)
            &
            (longitude <= 80.6)
            &
            np.isfinite(rainfall)
        )

        area_values = rainfall[
            area_mask
        ]

        if area_values.size > 0:

            minimum = float(
                np.min(
                    area_values
                )
            )

            maximum = float(
                np.max(
                    area_values
                )
            )

            mean = float(
                np.mean(
                    area_values
                )
            )

            median = float(
                np.median(
                    area_values
                )
            )

            valid_pixels = int(
                area_values.size
            )

        else:

            minimum = None
            maximum = None
            mean = None
            median = None
            valid_pixels = 0

        # ----------------------------------------------------
        # Units
        # ----------------------------------------------------

        units = decode_attribute(
            hem_dataset.attrs.get(
                "units",
                "mm/hr",
            )
        )

        if isinstance(units, list):

            if len(units) > 0:
                units = str(
                    units[0]
                )

            else:
                units = "mm/hr"

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        result = {

            "timestamp_utc":
                timestamp.isoformat(),

            "timestamp_ist":
                timestamp.astimezone(
                    timezone(
                        timedelta(
                            hours=5,
                            minutes=30
                        )
                    )
                ).isoformat(),

            "satellite":
                SATELLITE,

            "product":
                PRODUCT,

            "source_file":
                file_path.name,

            "nearest_latitude":
                pixel[
                    "latitude"
                ],

            "nearest_longitude":
                pixel[
                    "longitude"
                ],

            "nearest_rainfall_mm_hr":
                pixel[
                    "rainfall_mm_hr"
                ],

            "pixel_row":
                pixel[
                    "row"
                ],

            "pixel_column":
                pixel[
                    "column"
                ],

            "chennai_min_mm_hr":
                minimum,

            "chennai_max_mm_hr":
                maximum,

            "chennai_mean_mm_hr":
                mean,

            "chennai_median_mm_hr":
                median,

            "valid_pixels":
                valid_pixels,

            "hem_shape":
                str(
                    rainfall.shape
                ),

            "units":
                str(units),
        }

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        print(
            f"  UTC timestamp : "
            f"{timestamp.isoformat()}"
        )

        print(
            f"  Rainfall      : "
            f"{pixel['rainfall_mm_hr']:.2f} mm/hr"
        )

        print(
            f"  Pixel         : "
            f"{pixel['latitude']:.3f}, "
            f"{pixel['longitude']:.3f}"
        )

        if mean is not None:

            print(
                f"  Area mean     : "
                f"{mean:.2f} mm/hr"
            )

        else:

            print(
                "  Area mean     : "
                "No valid pixels"
            )

        print(
            f"  Valid pixels  : "
            f"{valid_pixels}"
        )

        return result


# ============================================================
# PROCESS ALL HEM FILES
# ============================================================

def process_all_files():

    print()
    print(
        "=" * 70
    )

    print(
        "VARSHAAI - INSAT-3DR HEM "
        "TIME-SERIES PROCESSOR"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "Input directory:"
    )

    print(
        HEM_DIRECTORY
    )

    # --------------------------------------------------------
    # Check directory
    # --------------------------------------------------------

    if not HEM_DIRECTORY.exists():

        raise FileNotFoundError(
            "HEM directory does not exist:\n"
            f"{HEM_DIRECTORY}"
        )

    # --------------------------------------------------------
    # Find HEM files
    # --------------------------------------------------------

    files = sorted(
        HEM_DIRECTORY.glob(
            "3RIMG_*_L2B_HEM_*.h5"
        )
    )

    print()

    print(
        f"HDF5 files found: "
        f"{len(files)}"
    )

    if not files:

        raise FileNotFoundError(
            "No INSAT-3DR HEM files found."
        )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    failed_files = []

    # --------------------------------------------------------
    # Process files
    # --------------------------------------------------------

    for index, file_path in enumerate(
        files,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(files)}]"
        )

        try:

            result = process_hem_file(
                file_path
            )

            results.append(
                result
            )

        except Exception as error:

            print(
                f"  ERROR: {error}"
            )

            failed_files.append(
                {
                    "file":
                        file_path.name,

                    "error":
                        str(error),
                }
            )

    # --------------------------------------------------------
    # Sort by time
    # --------------------------------------------------------

    results.sort(
        key=lambda item:
        item[
            "timestamp_utc"
        ]
    )

    # --------------------------------------------------------
    # CSV columns
    # --------------------------------------------------------

    fieldnames = [

        "timestamp_utc",

        "timestamp_ist",

        "satellite",

        "product",

        "source_file",

        "nearest_latitude",

        "nearest_longitude",

        "nearest_rainfall_mm_hr",

        "pixel_row",

        "pixel_column",

        "chennai_min_mm_hr",

        "chennai_max_mm_hr",

        "chennai_mean_mm_hr",

        "chennai_median_mm_hr",

        "valid_pixels",

        "hem_shape",

        "units",
    ]

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "PROCESSING COMPLETE"
    )

    print(
        "=" * 70
    )

    print()

    print(
        f"Files found      : "
        f"{len(files)}"
    )

    print(
        f"Files processed  : "
        f"{len(results)}"
    )

    print(
        f"Files failed     : "
        f"{len(failed_files)}"
    )

    print()

    print(
        "Output CSV:"
    )

    print(
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # Rainfall summary
    # --------------------------------------------------------

    rainfall_values = [

        item[
            "nearest_rainfall_mm_hr"
        ]

        for item in results

        if item[
            "nearest_rainfall_mm_hr"
        ] is not None

    ]

    if rainfall_values:

        print()

        print(
            "CHENNAI SATELLITE "
            "RAINFALL SUMMARY"
        )

        print(
            f"Minimum : "
            f"{min(rainfall_values):.2f} mm/hr"
        )

        print(
            f"Maximum : "
            f"{max(rainfall_values):.2f} mm/hr"
        )

        print(
            f"Mean    : "
            f"{np.mean(rainfall_values):.2f} mm/hr"
        )

    # --------------------------------------------------------
    # Failed files
    # --------------------------------------------------------

    if failed_files:

        print()

        print(
            "FAILED FILES"
        )

        for item in failed_files:

            print(
                f"- {item['file']}"
            )

            print(
                f"  {item['error']}"
            )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    print()

    if len(results) == len(files):

        print(
            "SUCCESS: ALL HEM FILES PROCESSED"
        )

    elif len(results) > 0:

        print(
            "PARTIAL SUCCESS: "
            "SOME HEM FILES FAILED"
        )

    else:

        print(
            "ERROR: NO HEM FILES WERE PROCESSED"
        )

    print()

    print(
        "MOSDAC HEM TIME SERIES READY"
    )

    print(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_all_files()