from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import h5py
import numpy as np


# ============================================================
# VARSHAAI
# MOSDAC INSAT-3DR HEM DATA READER
# ============================================================

SATELLITE = "INSAT-3DR"
PRODUCT = "3RIMG_L2B_HEM"

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707

DEFAULT_HEM_FILL = -999.0
DEFAULT_COORD_FILL = 32767


def decode_attribute(value):
    """Convert HDF5 attributes into normal Python values."""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")

    if isinstance(value, np.bytes_):
        return value.tobytes().decode(
            "utf-8",
            errors="ignore",
        )

    if isinstance(value, np.ndarray):
        if value.size == 1:
            return decode_attribute(value.reshape(-1)[0])

    return value


def read_coordinate(dataset):
    """
    Read latitude/longitude and apply the HDF5
    scale factor and offset.
    """

    raw = dataset[:].astype(np.float32)

    fill_value = dataset.attrs.get(
        "_FillValue",
        DEFAULT_COORD_FILL,
    )

    scale_factor = dataset.attrs.get(
        "scale_factor",
        1.0,
    )

    add_offset = dataset.attrs.get(
        "add_offset",
        0.0,
    )

    fill_value = float(
        np.asarray(fill_value).reshape(-1)[0]
    )

    scale_factor = float(
        np.asarray(scale_factor).reshape(-1)[0]
    )

    add_offset = float(
        np.asarray(add_offset).reshape(-1)[0]
    )

    valid = raw != fill_value

    result = (
        raw * scale_factor
        + add_offset
    )

    result[~valid] = np.nan

    return result


def decode_time(minutes, units):
    """
    Decode MOSDAC time information.

    Example:

    minutes since 2000-01-01 00:00:00
    """

    if "since" not in units.lower():

        raise ValueError(
            f"Unsupported time units: {units}"
        )

    base_text = units.split(
        "since",
        1,
    )[1].strip()

    base_text = base_text.replace(
        "Z",
        "",
    )

    try:

        base_datetime = datetime.fromisoformat(
            base_text
        )

    except ValueError:

        base_datetime = datetime(
            2000,
            1,
            1,
            0,
            0,
        )

    base_datetime = base_datetime.replace(
        tzinfo=timezone.utc
    )

    return (
        base_datetime
        + timedelta(minutes=float(minutes))
    )


def read_hem_file(file_path):
    """
    Read one INSAT-3DR HEM file.

    Returns:
        rainfall
        latitude
        longitude
        timestamp
        metadata
    """

    file_path = Path(file_path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"HEM file not found: {file_path}"
        )

    with h5py.File(
        file_path,
        "r",
    ) as hdf:

        # ----------------------------------------------------
        # HEM rainfall
        # ----------------------------------------------------

        hem_dataset = hdf["HEM"]

        rainfall = hem_dataset[:]

        # HEM normally contains:
        #
        # (1, 2816, 2805)
        #
        # Convert to:
        #
        # (2816, 2805)

        if (
            rainfall.ndim == 3
            and rainfall.shape[0] == 1
        ):

            rainfall = rainfall[0]

        rainfall = rainfall.astype(
            np.float32
        )

        fill_value = hem_dataset.attrs.get(
            "_FillValue",
            DEFAULT_HEM_FILL,
        )

        fill_value = float(
            np.asarray(
                fill_value
            ).reshape(-1)[0]
        )

        rainfall[
            rainfall == fill_value
        ] = np.nan

        rainfall[
            ~np.isfinite(rainfall)
        ] = np.nan

        # ----------------------------------------------------
        # Latitude
        # ----------------------------------------------------

        latitude = read_coordinate(
            hdf["Latitude"]
        )

        # ----------------------------------------------------
        # Longitude
        # ----------------------------------------------------

        longitude = read_coordinate(
            hdf["Longitude"]
        )

        # ----------------------------------------------------
        # Time
        # ----------------------------------------------------

        time_dataset = hdf["time"]

        time_value = float(
            time_dataset[0]
        )

        time_units = decode_attribute(
            time_dataset.attrs.get(
                "units",
                "minutes since 2000-01-01 00:00:00",
            )
        )

        timestamp_utc = decode_time(
            time_value,
            time_units,
        )

        timestamp_ist = (
            timestamp_utc
            + timedelta(
                hours=5,
                minutes=30,
            )
        )

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        units = decode_attribute(
            hem_dataset.attrs.get(
                "units",
                "mm/hr",
            )
        )

        long_name = decode_attribute(
            hem_dataset.attrs.get(
                "long_name",
                "Hydro Estimator Precipitation",
            )
        )

        metadata = {
            "filename": file_path.name,
            "satellite": SATELLITE,
            "product": PRODUCT,
            "units": units,
            "long_name": long_name,
            "fill_value": fill_value,
            "shape": list(
                rainfall.shape
            ),
        }

    return {
        "satellite": SATELLITE,
        "product": PRODUCT,
        "timestamp_utc": timestamp_utc,
        "timestamp_ist": timestamp_ist,
        "rainfall": rainfall,
        "latitude": latitude,
        "longitude": longitude,
        "metadata": metadata,
    }


def find_nearest_pixel(
    latitude,
    longitude,
    target_lat=CHENNAI_LAT,
    target_lon=CHENNAI_LON,
):
    """
    Find the satellite pixel nearest to Chennai.
    """

    valid = (
        np.isfinite(latitude)
        & np.isfinite(longitude)
    )

    if not np.any(valid):

        raise ValueError(
            "No valid latitude/longitude pixels found."
        )

    distance = (
        (latitude - target_lat) ** 2
        +
        (longitude - target_lon) ** 2
    )

    distance[
        ~valid
    ] = np.inf

    row, column = np.unravel_index(
        np.argmin(distance),
        distance.shape,
    )

    return {
        "row": int(row),
        "column": int(column),
        "latitude": float(
            latitude[row, column]
        ),
        "longitude": float(
            longitude[row, column]
        ),
        "distance_degrees": float(
            np.sqrt(
                distance[row, column]
            )
        ),
    }


def get_chennai_rainfall(file_path):
    """
    Get HEM rainfall at the satellite
    pixel nearest to Chennai.
    """

    data = read_hem_file(
        file_path
    )

    pixel = find_nearest_pixel(
        data["latitude"],
        data["longitude"],
    )

    rainfall_value = float(
        data["rainfall"][
            pixel["row"],
            pixel["column"],
        ]
    )

    if not np.isfinite(
        rainfall_value
    ):

        rainfall_value = None

    return {
        "satellite": data["satellite"],
        "product": data["product"],
        "timestamp_utc": (
            data["timestamp_utc"].isoformat()
        ),
        "timestamp_ist": (
            data["timestamp_ist"].isoformat()
        ),
        "rainfall_mm_hr": rainfall_value,
        "latitude": pixel["latitude"],
        "longitude": pixel["longitude"],
        "pixel_row": pixel["row"],
        "pixel_column": pixel["column"],
        "distance_degrees": pixel[
            "distance_degrees"
        ],
        "source_file": data[
            "metadata"
        ]["filename"],
    }


def get_chennai_statistics(
    file_path,
    lat_min=12.8,
    lat_max=13.4,
    lon_min=79.9,
    lon_max=80.6,
):
    """
    Calculate HEM rainfall statistics
    over the Chennai region.
    """

    data = read_hem_file(
        file_path
    )

    latitude = data["latitude"]
    longitude = data["longitude"]
    rainfall = data["rainfall"]

    mask = (
        (latitude >= lat_min)
        &
        (latitude <= lat_max)
        &
        (longitude >= lon_min)
        &
        (longitude <= lon_max)
        &
        np.isfinite(rainfall)
    )

    values = rainfall[mask]

    if values.size == 0:

        return {
            "status": "no_valid_data",
            "valid_pixel_count": 0,
        }

    return {
        "status": "success",
        "satellite": data["satellite"],
        "product": data["product"],
        "timestamp_utc": (
            data["timestamp_utc"].isoformat()
        ),
        "timestamp_ist": (
            data["timestamp_ist"].isoformat()
        ),
        "rainfall_unit": "mm/hr",
        "minimum_mm_hr": float(
            np.min(values)
        ),
        "maximum_mm_hr": float(
            np.max(values)
        ),
        "mean_mm_hr": float(
            np.mean(values)
        ),
        "median_mm_hr": float(
            np.median(values)
        ),
        "valid_pixel_count": int(
            values.size
        ),
        "bounding_box": {
            "lat_min": lat_min,
            "lat_max": lat_max,
            "lon_min": lon_min,
            "lon_max": lon_max,
        },
    }