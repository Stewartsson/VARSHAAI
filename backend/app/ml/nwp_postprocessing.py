"""
RainGuard AI - NWP Post-Processing Model

Purpose:
    Bias-correct / post-process numerical weather prediction
    rainfall forecasts for the 3–72 hour forecast window.

Model:
    HistGradientBoostingRegressor

Input features:
    - NWP precipitation
    - NWP humidity
    - NWP wind speed
    - NWP pressure
    - recent observed rainfall
    - temporal rainfall features

Target:
    Observed rainfall

IMPORTANT:
    This module is the second distinct ML model in the
    RainGuard architecture.

    Initial historical experiments can use IMD rainfall data
    as a benchmark. That does NOT constitute live NWP
    validation until genuine NWP forecasts are connected.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


@dataclass
class NWPPostProcessingResult:
    """Evaluation result for the NWP post-processing model."""

    mae: float
    rmse: float
    sample_count: int


class NWPPostProcessor:
    """
    Machine-learning post-processor for NWP rainfall.

    The model learns the relationship between NWP-derived
    predictors and observed rainfall.
    """

    def __init__(
        self,
        random_state: int = 42,
    ):
        self.random_state = random_state

        self.model = HistGradientBoostingRegressor(
            max_iter=200,
            learning_rate=0.08,
            max_leaf_nodes=31,
            l2_regularization=1.0,
            random_state=random_state,
        )

        self.feature_names = [
            "nwp_precipitation_mm",
            "nwp_humidity",
            "nwp_wind_speed_ms",
            "nwp_pressure_hpa",
            "recent_rainfall_mm",
            "rolling_3_day_rainfall_mm",
            "rolling_7_day_rainfall_mm",
        ]

        self.is_fitted = False

    def validate_features(
        self,
        X: np.ndarray,
    ) -> None:
        """Validate the feature matrix."""

        if not isinstance(X, np.ndarray):
            raise TypeError(
                "X must be a NumPy array."
            )

        if X.ndim != 2:
            raise ValueError(
                "X must have shape "
                "(samples, features)."
            )

        expected = len(
            self.feature_names
        )

        if X.shape[1] != expected:
            raise ValueError(
                f"Expected {expected} features, "
                f"received {X.shape[1]}."
            )

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> None:
        """
        Train the NWP post-processing model.
        """

        self.validate_features(X)

        y = np.asarray(
            y,
            dtype=np.float32,
        )

        if y.ndim != 1:
            raise ValueError(
                "y must be a one-dimensional target array."
            )

        if len(X) != len(y):
            raise ValueError(
                "X and y must contain the same "
                "number of samples."
            )

        valid = (
            np.isfinite(X).all(axis=1)
            & np.isfinite(y)
        )

        X_valid = X[valid]
        y_valid = y[valid]

        if len(X_valid) < 2:
            raise ValueError(
                "Not enough valid samples for training."
            )

        self.model.fit(
            X_valid,
            y_valid,
        )

        self.is_fitted = True

    def predict(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """Generate post-processed rainfall predictions."""

        if not self.is_fitted:
            raise RuntimeError(
                "Model must be fitted before prediction."
            )

        self.validate_features(X)

        predictions = self.model.predict(X)

        # Rainfall cannot be negative.
        predictions = np.maximum(
            predictions,
            0.0,
        )

        return predictions.astype(
            np.float32
        )

    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> NWPPostProcessingResult:
        """Evaluate model using MAE and RMSE."""

        y = np.asarray(
            y,
            dtype=np.float32,
        )

        predictions = self.predict(X)

        valid = (
            np.isfinite(y)
            & np.isfinite(predictions)
        )

        if not np.any(valid):
            raise ValueError(
                "No valid samples available for evaluation."
            )

        y_valid = y[valid]
        prediction_valid = predictions[valid]

        mae = mean_absolute_error(
            y_valid,
            prediction_valid,
        )

        rmse = np.sqrt(
            mean_squared_error(
                y_valid,
                prediction_valid,
            )
        )

        return NWPPostProcessingResult(
            mae=float(mae),
            rmse=float(rmse),
            sample_count=int(
                np.sum(valid)
            ),
        )

    def save(
        self,
        path: str | Path,
    ) -> None:
        """Save the trained model."""

        if not self.is_fitted:
            raise RuntimeError(
                "Cannot save an unfitted model."
            )

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "model": self.model,
            "feature_names": self.feature_names,
            "random_state": self.random_state,
        }

        joblib.dump(
            payload,
            path,
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "NWPPostProcessor":
        """Load a previously trained model."""

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Model not found: {path}"
            )

        payload = joblib.load(path)

        processor = cls(
            random_state=payload[
                "random_state"
            ],
        )

        processor.model = payload[
            "model"
        ]

        processor.feature_names = payload[
            "feature_names"
        ]

        processor.is_fitted = True

        return processor


def build_demo_dataset(
    samples: int = 2000,
):
    """
    Create a deterministic synthetic dataset for an
    architecture smoke test.

    This data is NOT used to claim weather-model performance.
    """

    rng = np.random.default_rng(42)

    X = rng.random(
        (
            samples,
            7,
        ),
        dtype=np.float32,
    )

    # Create a deterministic relationship between
    # predictors and target so the smoke test can
    # verify that the estimator learns.
    y = (
        0.55 * X[:, 0]
        + 0.15 * X[:, 1]
        + 0.10 * X[:, 2]
        + 0.05 * X[:, 3]
        + 0.10 * X[:, 4]
        + 0.03 * X[:, 5]
        + 0.02 * X[:, 6]
    )

    y = (
        y * 100.0
    ).astype(
        np.float32
    )

    return X, y


if __name__ == "__main__":

    print("\nRainGuard NWP Post-Processing Model")
    print("===================================")

    # --------------------------------------------------
    # Architecture smoke test
    # --------------------------------------------------

    X, y = build_demo_dataset(
        samples=2000
    )

    split = 1600

    X_train = X[:split]
    y_train = y[:split]

    X_test = X[split:]
    y_test = y[split:]

    processor = NWPPostProcessor()

    print(
        "\nFeatures:",
        len(processor.feature_names),
    )

    print(
        "Training samples:",
        len(X_train),
    )

    print(
        "Test samples:",
        len(X_test),
    )

    processor.fit(
        X_train,
        y_train,
    )

    predictions = processor.predict(
        X_test
    )

    result = processor.evaluate(
        X_test,
        y_test,
    )

    print(
        "\nPrediction shape:",
        predictions.shape,
    )

    print(
        f"Smoke-test MAE:  {result.mae:.4f}"
    )

    print(
        f"Smoke-test RMSE: {result.rmse:.4f}"
    )

    # --------------------------------------------------
    # Persistence test
    # --------------------------------------------------

    model_path = (
        Path("models")
        / "rainguard_nwp_postprocessor.joblib"
    )

    processor.save(
        model_path
    )

    loaded = NWPPostProcessor.load(
        model_path
    )

    loaded_predictions = loaded.predict(
        X_test[:5]
    )

    assert predictions.shape == (
        len(X_test),
    )

    assert loaded_predictions.shape == (
        5,
    )

    assert loaded.is_fitted

    print(
        "\nModel persistence test PASSED"
    )

    print(
        "Model saved:",
        model_path,
    )

    print(
        "\nSTATUS: NWP post-processing model test PASSED"
    )