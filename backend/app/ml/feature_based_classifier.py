from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix

from app.historical.validation_metrics import categorical_metrics


BASE_DIR = Path(__file__).resolve().parents[3]

FEATURE_DIR = (
    BASE_DIR
    / "data"
    / "historical"
    / "features"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "feature_classifier_results.csv"
)

TRAIN_YEAR = 2015
TEST_YEAR = 2018

RAINFALL_THRESHOLD_MM = 64.5

PROBABILITY_THRESHOLD = 0.50


def load_features(year):
    path = (
        FEATURE_DIR
        / f"rainfall_features_{year}.npz"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Feature file not found: {path}"
        )

    data = np.load(
        path,
        allow_pickle=True,
    )

    X = data["X"].astype(
        np.float32
    )

    y_rainfall = data["y"].astype(
        np.float32
    )

    feature_names = [
        str(x)
        for x in data["feature_names"]
    ]

    return (
        X,
        y_rainfall,
        feature_names,
    )


def main():
    print("RainGuard Feature-Based Heavy-Rain Classifier")
    print("----------------------------------------------")

    X_train, y_train_rainfall, feature_names = (
        load_features(TRAIN_YEAR)
    )

    X_test, y_test_rainfall, _ = (
        load_features(TEST_YEAR)
    )

    print(
        f"Training year : {TRAIN_YEAR}"
    )

    print(
        f"Testing year  : {TEST_YEAR}"
    )

    print(
        f"Features      : {len(feature_names)}"
    )

    print(
        f"Feature names : {feature_names}"
    )

    print("\nPreparing targets...")

    y_train = (
        y_train_rainfall
        >= RAINFALL_THRESHOLD_MM
    ).astype(np.int8)

    y_test = (
        y_test_rainfall
        >= RAINFALL_THRESHOLD_MM
    ).astype(np.int8)

    print(
        f"Training samples : "
        f"{len(y_train):,}"
    )

    print(
        f"Training heavy-rain : "
        f"{int(y_train.sum()):,}"
    )

    print(
        f"Testing samples : "
        f"{len(y_test):,}"
    )

    print(
        f"Testing heavy-rain : "
        f"{int(y_test.sum()):,}"
    )

    print("\nTraining gradient-boosting classifier...")

    model = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    print(
        "  Classifier trained successfully."
    )

    print("\nGenerating probabilities...")

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        probabilities
        >= PROBABILITY_THRESHOLD
    ).astype(np.int8)

    print(
        f"  Probability threshold : "
        f"{PROBABILITY_THRESHOLD:.2f}"
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

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1],
    ).ravel()

    print(f"  TP: {tp}")
    print(f"  FP: {fp}")
    print(f"  FN: {fn}")
    print(f"  TN: {tn}")

    result = {
        "model": "hist_gradient_boosting_features",
        "train_year": TRAIN_YEAR,
        "test_year": TEST_YEAR,
        "rainfall_threshold_mm": (
            RAINFALL_THRESHOLD_MM
        ),
        "probability_threshold": (
            PROBABILITY_THRESHOLD
        ),
        "pod": metrics["pod"],
        "far": metrics["far"],
        "csi": metrics["csi"],
        "true_positive": int(tp),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_negative": int(tn),
    }

    pd.DataFrame(
        [result]
    ).to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n----------------------------------------------")
    print(
        "Feature-based classifier validation complete."
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()