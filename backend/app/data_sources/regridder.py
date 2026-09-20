import numpy as np

from app.data_sources.spatial_grid import CommonGrid


def bilinear_regrid(
    source_latitudes,
    source_longitudes,
    source_values,
    target_grid: CommonGrid,
):
    """
    Bilinearly interpolate a 2D gridded field onto the
    RainGuard common grid.

    source_values shape:
        (latitude, longitude)

    Missing source values are preserved where interpolation
    cannot be performed reliably.
    """

    source_latitudes = np.asarray(
        source_latitudes,
        dtype=float,
    )

    source_longitudes = np.asarray(
        source_longitudes,
        dtype=float,
    )

    source_values = np.asarray(
        source_values,
        dtype=float,
    )

    if source_values.shape != (
        len(source_latitudes),
        len(source_longitudes),
    ):
        raise ValueError(
            "source_values shape must match "
            "(latitude, longitude)."
        )

    target_latitudes = target_grid.latitudes
    target_longitudes = target_grid.longitudes

    output = np.full(
        target_grid.shape,
        np.nan,
        dtype=float,
    )

    for i, target_lat in enumerate(
        target_latitudes
    ):
        lat_position = np.searchsorted(
            source_latitudes,
            target_lat,
        )

        if (
            lat_position == 0
            or lat_position >= len(source_latitudes)
        ):
            continue

        lat0 = source_latitudes[
            lat_position - 1
        ]

        lat1 = source_latitudes[
            lat_position
        ]

        lat_weight = (
            (target_lat - lat0)
            / (lat1 - lat0)
        )

        for j, target_lon in enumerate(
            target_longitudes
        ):
            lon_position = np.searchsorted(
                source_longitudes,
                target_lon,
            )

            if (
                lon_position == 0
                or lon_position >= len(source_longitudes)
            ):
                continue

            lon0 = source_longitudes[
                lon_position - 1
            ]

            lon1 = source_longitudes[
                lon_position
            ]

            lon_weight = (
                (target_lon - lon0)
                / (lon1 - lon0)
            )

            q11 = source_values[
                lat_position - 1,
                lon_position - 1,
            ]

            q21 = source_values[
                lat_position,
                lon_position - 1,
            ]

            q12 = source_values[
                lat_position - 1,
                lon_position,
            ]

            q22 = source_values[
                lat_position,
                lon_position,
            ]

            corners = np.array(
                [q11, q21, q12, q22],
                dtype=float,
            )

            if not np.all(
                np.isfinite(corners)
            ):
                continue

            value = (
                q11 * (1 - lat_weight)
                * (1 - lon_weight)
                + q21 * lat_weight
                * (1 - lon_weight)
                + q12 * (1 - lat_weight)
                * lon_weight
                + q22 * lat_weight
                * lon_weight
            )

            output[i, j] = value

    return output


if __name__ == "__main__":

    print("RainGuard Bilinear Regridding Test")
    print("----------------------------------")

    # Small synthetic source grid.
    source_latitudes = np.array([
        12.0,
        12.5,
        13.0,
        13.5,
        14.0,
    ])

    source_longitudes = np.array([
        79.0,
        79.5,
        80.0,
        80.5,
        81.0,
    ])

    source_values = np.array([
        [10, 20, 30, 40, 50],
        [20, 30, 40, 50, 60],
        [30, 40, 50, 60, 70],
        [40, 50, 60, 70, 80],
        [50, 60, 70, 80, 90],
    ], dtype=float)

    target_grid = CommonGrid(
        min_lat=12.0,
        max_lat=14.0,
        min_lon=79.0,
        max_lon=81.0,
        resolution_deg=0.25,
    )

    result = bilinear_regrid(
        source_latitudes,
        source_longitudes,
        source_values,
        target_grid,
    )

    print(
        f"\nSource shape : "
        f"{source_values.shape}"
    )

    print(
        f"Target shape : "
        f"{result.shape}"
    )

    print(
        f"Valid target cells : "
        f"{np.isfinite(result).sum()}"
    )

    print(
        f"Target minimum : "
        f"{np.nanmin(result):.2f}"
    )

    print(
        f"Target maximum : "
        f"{np.nanmax(result):.2f}"
    )

    print("\n----------------------------------")
    print("Bilinear regridding test OK.")