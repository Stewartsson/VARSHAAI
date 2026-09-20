from pathlib import Path

import numpy as np
import pandas as pd

from app.historical.multi_year_loader import (
    discover_rainfall_files,
    load_year,
)
from app.historical.validation_metrics import evaluate


BASE_DIR = Path(__file__).resolve().parents[3]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "historical_ml_validation_results.csv"
)


TRAIN_YEAR = 2015
TEST_YEAR = 2018

THRESHOLD_MM = 64.5

LAG_DAYS = [1, 2, 3, 7]


def build_samples(rainfall):
    """
    Build daily grid-cell training samples.

    Features:
        rainfall from 1, 2, 3 and 7 days earlier.

    Target:
        rainfall on the current day.
    """

    values = rainfall.values.astype(np.float64)

    samples_x = []
    samples_y = []

    max_lag = max(LAG_DAYS)

    for day_index in range(
        max_lag,
        values.shape[0],
    ):
        target = values[day_index]

        features = [
            values[
                day_index - lag
            ]
            for lag in LAG_DAYS
        ]

        feature_stack = np.stack(
            features,
            axis=-1,
        )

        target_flat = target.reshape(-1)
        feature_flat = feature_stack.reshape(
            -1,
            len(LAG_DAYS),
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

        samples_x.append(
            feature_flat[valid]
        )

        samples_y.append(
            target_flat[valid]
        )

    if not samples_x:
        raise ValueError(
            "No valid ML samples could be created."
        )

    X = np.concatenate(
        samples_x,
        axis=0,
    )

    y = np.concatenate(
        samples_y,
        axis=0,
    )

    return X, y


def train_linear_model(X, y):
    """
    Train a linear rainfall prediction model.

    The model learns:

        rainfall(t) =
            intercept
            + w1 * rainfall(t-1)
            + w2 * rainfall(t-2)
            + w3 * rainfall(t-3)
            + w4 * rainfall(t-7)
    """

    X_design = np.column_stack(
        [
            np.ones(len(X)),
            X,
        ]
    )

    coefficients, _, _, _ = np.linalg.lstsq(
        X_design,
        y,
        rcond=None,
    )

    return coefficients


def predict(X, coefficients):
    """
    Generate rainfall predictions.
    """

    X_design = np.column_stack(
        [
            np.ones(len(X)),
            X,
        ]
    )

    predictions = X_design @ coefficients

    # Rainfall cannot be negative.
    predictions = np.maximum(
        predictions,
        0.0,
    )

    return predictions


def main():
    files = discover_rainfall_files()

    rainfall_by_year = {}

    for path in files:
        rainfall = load_year(path)

        year = int(
            pd.Timestamp(
                rainfall.TIME.values[0]
            ).year
        )

        rainfall_by_year[year] = rainfall

    if TRAIN_YEAR not in rainfall_by_year:
        raise FileNotFoundError(
            f"Training year {TRAIN_YEAR} not found."
        )

    if TEST_YEAR not in rainfall_by_year:
        raise FileNotFoundError(
            f"Testing year {TEST_YEAR} not found."
        )

    print("RainGuard Historical ML Model")
    print("-----------------------------")
    print(
        f"Training year : {TRAIN_YEAR}"
    )
    print(
        f"Testing year  : {TEST_YEAR}"
    )
    print(
        f"Lag features  : {LAG_DAYS}"
    )

    print("\nBuilding training samples...")

    X_train, y_train = build_samples(
        rainfall_by_year[TRAIN_YEAR]
    )

    print(
        f"  Samples : {len(y_train):,}"
    )
    print(
        f"  Features: {X_train.shape[1]}"
    )

    print("\nTraining model...")

    coefficients = train_linear_model(
        X_train,
        y_train,
    )

    print("  Model trained successfully.")

    print("\nModel coefficients:")

    print(
        f"  Intercept : "
        f"{coefficients[0]:.6f}"
    )

    for index, lag in enumerate(
        LAG_DAYS,
        start=1,
    ):
        print(
            f"  Lag {lag:>2} day : "
            f"{coefficients[index]:.6f}"
        )

    print("\nBuilding test samples...")

    X_test, y_test = build_samples(
        rainfall_by_year[TEST_YEAR]
    )

    print(
        f"  Samples : {len(y_test):,}"
    )

    print("\nGenerating predictions...")

    predictions = predict(
        X_test,
        coefficients,
    )

    print(
        f"  Predictions generated : "
        f"{len(predictions):,}"
    )

    print("\nCalculating validation metrics...")

    metrics = evaluate(
        y_test,
        predictions,
        threshold=THRESHOLD_MM,
    )

    print(
        f"  MAE  : {metrics['mae']:.4f} mm"
    )
    print(
        f"  RMSE : {metrics['rmse']:.4f} mm"
    )
    print(
        f"  POD  : {metrics['pod']:.4f}"
    )
    print(
        f"  FAR  : {metrics['far']:.4f}"
    )
    print(
        f"  CSI  : {metrics['csi']:.4f}"
    )

    print("\nConfusion matrix:")
    print(
        f"  TP: {metrics['true_positive']}"
    )
    print(
        f"  FP: {metrics['false_positive']}"
    )
    print(
        f"  FN: {metrics['false_negative']}"
    )
    print(
        f"  TN: {metrics['true_negative']}"
    )

    result = {
        "model": "historical_lag_linear",
        "train_year": TRAIN_YEAR,
        "test_year": TEST_YEAR,
        "threshold_mm": metrics[
            "threshold_mm"
        ],
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "pod": metrics["pod"],
        "far": metrics["far"],
        "csi": metrics["csi"],
        "true_positive": metrics[
            "true_positive"
        ],
        "false_positive": metrics[
            "false_positive"
        ],
        "false_negative": metrics[
            "false_negative"
        ],
        "true_negative": metrics[
            "true_negative"
        ],
    }

    pd.DataFrame(
        [result]
    ).to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n-----------------------------")
    print(
        "Historical ML validation complete."
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()