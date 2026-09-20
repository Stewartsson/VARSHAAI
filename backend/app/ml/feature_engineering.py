from pathlib import Path

import numpy as np
import pandas as pd

from app.historical.multi_year_loader import (
    discover_rainfall_files,
    load_year,
)


BASE_DIR = Path(__file__).resolve().parents[3]

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "historical"
    / "features"
)


LAG_DAYS = [1, 2, 3, 7]

ROLLING_WINDOWS = [3, 7]


def build_rainfall_features(rainfall):
    """
    Build rainfall-derived spatial-temporal features.

    Features are calculated independently for every
    grid cell and day.

    Current features:
        lag_1
        lag_2
        lag_3
        lag_7
        rolling_3_day
        rolling_7_day
        recent_trend

    The design is intentionally modular so that future
    radar, satellite, AWS/ARG and NWP features can be
    added without changing the downstream ML interface.
    """

    values = rainfall.values.astype(
        np.float32
    )

    feature_arrays = {}

    for lag in LAG_DAYS:
        lag_array = np.full_like(
            values,
            np.nan,
            dtype=np.float32,
        )

        lag_array[lag:] = values[:-lag]

        feature_arrays[
            f"lag_{lag}"
        ] = lag_array

    for window in ROLLING_WINDOWS:
        rolling_array = np.full_like(
            values,
            np.nan,
            dtype=np.float32,
        )

        for day in range(
            window - 1,
            values.shape[0],
        ):
            window_values = values[
                day - window + 1:
                day + 1
            ]

            rolling_array[day] = np.nansum(
                window_values,
                axis=0,
            )

            all_missing = np.all(
                ~np.isfinite(
                    window_values
                ),
                axis=0,
            )

            rolling_array[day][
                all_missing
            ] = np.nan

        feature_arrays[
            f"rolling_{window}_day"
        ] = rolling_array

    trend = np.full_like(
        values,
        np.nan,
        dtype=np.float32,
    )

    trend[1:] = (
        values[1:]
        - values[:-1]
    )

    feature_arrays[
        "recent_trend"
    ] = trend

    return feature_arrays


def flatten_features(
    rainfall,
    feature_arrays,
):
    """
    Convert spatial-temporal feature arrays
    into a tabular ML dataset.

    Each row represents:

        one day × one grid cell

    Returns:
        X : feature matrix
        y : next/current rainfall target
    """

    target = rainfall.values.astype(
        np.float32
    )

    feature_names = list(
        feature_arrays.keys()
    )

    X_parts = []
    y_parts = []

    for day in range(
        target.shape[0]
    ):
        feature_stack = np.stack(
            [
                feature_arrays[name][day]
                for name in feature_names
            ],
            axis=-1,
        )

        target_flat = target[
            day
        ].reshape(-1)

        feature_flat = feature_stack.reshape(
            -1,
            len(feature_names),
        )

        valid = (
            np.isfinite(target_flat)
            & np.all(
                np.isfinite(feature_flat),
                axis=1,
            )
        )

        if not valid.any():
            continue

        X_parts.append(
            feature_flat[valid]
        )

        y_parts.append(
            target_flat[valid]
        )

    if not X_parts:
        raise ValueError(
            "No valid feature samples found."
        )

    X = np.concatenate(
        X_parts,
        axis=0,
    )

    y = np.concatenate(
        y_parts,
        axis=0,
    )

    return (
        X,
        y,
        feature_names,
    )


def process_year(rainfall, year):
    """
    Build and save features for one year.
    """

    print(
        f"\nBuilding features for {year}..."
    )

    features = build_rainfall_features(
        rainfall
    )

    X, y, feature_names = (
        flatten_features(
            rainfall,
            features,
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        OUTPUT_DIR
        / f"rainfall_features_{year}.npz"
    )

    np.savez_compressed(
        output_file,
        X=X,
        y=y,
        feature_names=np.array(
            feature_names
        ),
    )

    print(
        f"  Samples  : {len(y):,}"
    )

    print(
        f"  Features : {len(feature_names)}"
    )

    print(
        f"  Output   : {output_file}"
    )


def main():
    files = discover_rainfall_files()

    print("RainGuard Feature Engineering")
    print("------------------------------")

    for path in files:
        rainfall = load_year(path)

        year = int(
            pd.Timestamp(
                rainfall.TIME.values[0]
            ).year
        )

        process_year(
            rainfall,
            year,
        )

    print("\n------------------------------")
    print("Feature engineering complete.")


if __name__ == "__main__":
    main()