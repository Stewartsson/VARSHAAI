from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from app.historical.multi_year_loader import (
    discover_rainfall_files,
    load_year,
)
from app.historical.validation_metrics import (
    categorical_metrics,
)


BASE_DIR = Path(__file__).resolve().parents[3]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "heavy_rain_classifier_results.csv"
)


TRAIN_YEAR = 2015
TEST_YEAR = 2018

THRESHOLD_MM = 64.5

LAG_DAYS = [1, 2, 3, 7]


def build_samples(rainfall):
    """
    Build daily grid-cell classification samples.

    Features:
        Rainfall from 1, 2, 3 and 7 days earlier.

    Target:
        1 if current-day rainfall >= threshold,
        otherwise 0.
    """

    values = rainfall.values.astype(
        np.float64
    )

    X_parts = []
    y_parts = []

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

        X_parts.append(
            feature_flat[valid]
        )

        y_parts.append(
            (
                target_flat[valid]
                >= THRESHOLD_MM
            ).astype(np.int8)
        )

    if not X_parts:
        raise ValueError(
            "No valid classifier samples found."
        )

    X = np.concatenate(
        X_parts,
        axis=0,
    )

    y = np.concatenate(
        y_parts,
        axis=0,
    )

    return X, y


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

    print("RainGuard Heavy-Rain Classifier")
    print("--------------------------------")
    print(
        f"Training year : {TRAIN_YEAR}"
    )
    print(
        f"Testing year  : {TEST_YEAR}"
    )
    print(
        f"Threshold     : {THRESHOLD_MM} mm"
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
        f"  Heavy-rain samples : "
        f"{int(y_train.sum()):,}"
    )

    print(
        f"  Non-heavy samples  : "
        f"{int((y_train == 0).sum()):,}"
    )

    print("\nTraining logistic classifier...")

    model = LogisticRegression(
        max_iter=500,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    print(
        "  Classifier trained successfully."
    )

    print("\nBuilding test samples...")

    X_test, y_test = build_samples(
        rainfall_by_year[TEST_YEAR]
    )

    print(
        f"  Samples : {len(y_test):,}"
    )

    print(
        f"  Heavy-rain samples : "
        f"{int(y_test.sum()):,}"
    )

    print("\nGenerating event probabilities...")

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        probabilities >= 0.50
    ).astype(np.int8)

    print(
        "  Predictions generated."
    )

    print("\nCalculating validation metrics...")

    metrics = categorical_metrics(
        y_test,
        predictions,
        threshold=0.5,
    )

    print(
        f"  POD : {metrics['pod']:.4f}"
    )

    print(
        f"  FAR : {metrics['far']:.4f}"
    )

    print(
        f"  CSI : {metrics['csi']:.4f}"
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
        "model": "heavy_rain_logistic_classifier",
        "train_year": TRAIN_YEAR,
        "test_year": TEST_YEAR,
        "rainfall_threshold_mm": THRESHOLD_MM,
        "classification_probability_threshold": 0.50,
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

    print("\n--------------------------------")
    print(
        "Heavy-rain classification complete."
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()