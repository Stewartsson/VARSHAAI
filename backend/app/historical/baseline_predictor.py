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
    / "baseline_validation_results.csv"
)


def persistence_prediction(rainfall):
    """
    Persistence baseline:
    tomorrow's rainfall field = today's rainfall field.

    Prediction for day t is therefore
    the observed rainfall field from day t-1.
    """

    observed = rainfall.values.astype(float)

    predicted = np.full_like(
        observed,
        np.nan,
        dtype=float,
    )

    predicted[1:] = observed[:-1]

    return observed, predicted


def calculate_grid_metrics(
    observed,
    predicted,
    threshold=64.5,
):
    """
    Flatten all valid grid cells and calculate
    rainfall validation metrics.
    """

    observed_flat = observed.reshape(-1)
    predicted_flat = predicted.reshape(-1)

    mask = (
        np.isfinite(observed_flat)
        & np.isfinite(predicted_flat)
    )

    observed_flat = observed_flat[mask]
    predicted_flat = predicted_flat[mask]

    if len(observed_flat) == 0:
        raise ValueError(
            "No valid observed/predicted grid cells."
        )

    return evaluate(
        observed_flat,
        predicted_flat,
        threshold=threshold,
    )


def main():
    files = discover_rainfall_files()

    results = []

    print("RainGuard Persistence Baseline")
    print("--------------------------------")

    for path in files:
        rainfall = load_year(path)

        year = int(
            pd.Timestamp(
                rainfall.TIME.values[0]
            ).year
        )

        print(f"\nProcessing {year}...")

        observed, predicted = (
            persistence_prediction(rainfall)
        )

        metrics = calculate_grid_metrics(
            observed[1:],
            predicted[1:],
            threshold=64.5,
        )

        metrics["year"] = year
        metrics["model"] = "persistence"

        results.append(metrics)

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

        print(
            "  Confusion matrix:"
        )
        print(
            f"    TP: {metrics['true_positive']}"
        )
        print(
            f"    FP: {metrics['false_positive']}"
        )
        print(
            f"    FN: {metrics['false_negative']}"
        )
        print(
            f"    TN: {metrics['true_negative']}"
        )

    result_df = pd.DataFrame(results)

    result_df = result_df[
        [
            "year",
            "model",
            "threshold_mm",
            "mae",
            "rmse",
            "pod",
            "far",
            "csi",
            "true_positive",
            "false_positive",
            "false_negative",
            "true_negative",
        ]
    ]

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n--------------------------------")
    print("Baseline validation complete.")

    print("\nResults:")
    print(
        result_df.to_string(
            index=False
        )
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()