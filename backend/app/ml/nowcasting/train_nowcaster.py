"""
RainGuard AI - ConvLSTM Training Pipeline

Training flow:

    Weather tensor
        ↓
    Dataset validation
        ↓
    Sequence generation
        ↓
    Chronological train/validation split
        ↓
    ConvLSTM training
        ↓
    MAE / RMSE evaluation
        ↓
    Saved model

IMPORTANT:
    Do not use synthetic/random data for claimed model performance.
    This script expects genuine high-frequency weather data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf

from app.ml.nowcasting.convlstm_model import (
    build_convlstm_model,
)
from app.ml.nowcasting.dataset_validator import (
    NowcastingDatasetValidator,
)
from app.ml.nowcasting.training_adapter import (
    NowcastingTrainingAdapter,
)


DEFAULT_INPUT_STEPS = 6
DEFAULT_FORECAST_STEPS = 6
DEFAULT_TIMESTEP_MINUTES = 30
DEFAULT_FEATURES = 10

DEFAULT_VALIDATION_FRACTION = 0.20

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "rainguard_convlstm.keras"


def load_tensor(path: Path) -> np.ndarray:
    """
    Load a NumPy tensor from .npy or .npz.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    if path.suffix.lower() == ".npy":
        tensor = np.load(path)

    elif path.suffix.lower() == ".npz":
        archive = np.load(path)

        if "tensor" in archive:
            tensor = archive["tensor"]

        elif "X" in archive:
            tensor = archive["X"]

        else:
            raise ValueError(
                "NPZ file must contain a 'tensor' or 'X' array."
            )

    else:
        raise ValueError(
            "Dataset must be .npy or .npz"
        )

    return np.asarray(tensor, dtype=np.float32)


def calculate_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """
    Calculate rainfall regression metrics.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    valid = (
        np.isfinite(y_true)
        & np.isfinite(y_pred)
    )

    if not np.any(valid):
        raise ValueError(
            "No valid values available for evaluation."
        )

    true_values = y_true[valid]
    predicted_values = y_pred[valid]

    errors = (
        predicted_values - true_values
    )

    mae = float(
        np.mean(np.abs(errors))
    )

    rmse = float(
        np.sqrt(np.mean(errors ** 2))
    )

    return {
        "MAE": mae,
        "RMSE": rmse,
    }


def chronological_split(
    X: np.ndarray,
    y: np.ndarray,
    validation_fraction: float,
):
    """
    Split sequences chronologically.

    Earlier samples → training
    Later samples   → validation

    This avoids randomly mixing future information
    into the training set.
    """

    if not 0 < validation_fraction < 1:
        raise ValueError(
            "validation_fraction must be between 0 and 1."
        )

    split_index = int(
        len(X) * (1.0 - validation_fraction)
    )

    if split_index <= 0 or split_index >= len(X):
        raise ValueError(
            "Dataset is too small for the requested split."
        )

    X_train = X[:split_index]
    y_train = y[:split_index]

    X_val = X[split_index:]
    y_val = y[split_index:]

    return (
        X_train,
        y_train,
        X_val,
        y_val,
    )


def train_nowcaster(
    tensor: np.ndarray,
    timestep_minutes: int,
    source_type: str,
    epochs: int = 10,
    batch_size: int = 2,
    validation_fraction: float = DEFAULT_VALIDATION_FRACTION,
):
    """
    Validate, prepare and train the ConvLSTM model.
    """

    print("\nRainGuard AI - ConvLSTM Training")
    print("================================")

    # --------------------------------------------------
    # 1. Validate dataset
    # --------------------------------------------------

    validator = NowcastingDatasetValidator(
        expected_timestep_minutes=DEFAULT_TIMESTEP_MINUTES,
        expected_features=DEFAULT_FEATURES,
        minimum_time_steps=(
            DEFAULT_INPUT_STEPS
            + DEFAULT_FORECAST_STEPS
        ),
    )

    validation_result = validator.validate(
        tensor,
        timestep_minutes=timestep_minutes,
        source_type=source_type,
    )

    print("\nDataset validation")
    print("------------------")

    for message in validation_result.messages:
        print(message)

    if not validation_result.eligible_for_nowcasting:
        raise ValueError(
            "\nDataset is not eligible for ConvLSTM "
            "nowcasting training."
        )

    # --------------------------------------------------
    # 2. Build supervised sequences
    # --------------------------------------------------

    adapter = NowcastingTrainingAdapter(
        input_steps=DEFAULT_INPUT_STEPS,
        forecast_steps=DEFAULT_FORECAST_STEPS,
        timestep_minutes=DEFAULT_TIMESTEP_MINUTES,
        target_feature=0,
    )

    training_data = adapter.build_sequences(
        tensor
    )

    X = training_data.X
    y = training_data.y

    print("\nSequence preparation")
    print("--------------------")
    print("X:", X.shape)
    print("y:", y.shape)

    # --------------------------------------------------
    # 3. Remove samples containing invalid values
    # --------------------------------------------------

    sample_validity = (
        np.isfinite(X).all(
            axis=(1, 2, 3, 4)
        )
        &
        np.isfinite(y).all(
            axis=(1, 2, 3)
        )
    )

    X = X[sample_validity]
    y = y[sample_validity]

    print(
        "Valid training sequences:",
        len(X),
    )

    if len(X) < 2:
        raise ValueError(
            "Not enough valid sequences for training."
        )

    # --------------------------------------------------
    # 4. Chronological split
    # --------------------------------------------------

    (
        X_train,
        y_train,
        X_val,
        y_val,
    ) = chronological_split(
        X,
        y,
        validation_fraction,
    )

    print("\nDataset split")
    print("-------------")
    print("Training:", X_train.shape)
    print("Validation:", X_val.shape)

    # --------------------------------------------------
    # 5. Build model
    # --------------------------------------------------

    height = X.shape[2]
    width = X.shape[3]
    channels = X.shape[4]

    model = build_convlstm_model(
        height=height,
        width=width,
        channels=channels,
        input_steps=DEFAULT_INPUT_STEPS,
        forecast_steps=DEFAULT_FORECAST_STEPS,
    )

    print("\nModel")
    print("-----")
    print(
        f"Grid: {height} × {width}"
    )
    print(
        f"Features: {channels}"
    )
    print(
        f"Input: {DEFAULT_INPUT_STEPS} × "
        f"{DEFAULT_TIMESTEP_MINUTES} min"
    )
    print(
        f"Forecast: {DEFAULT_FORECAST_STEPS} × "
        f"{DEFAULT_TIMESTEP_MINUTES} min"
    )

    # --------------------------------------------------
    # 6. Training callbacks
    # --------------------------------------------------

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
        ),
    ]

    # --------------------------------------------------
    # 7. Train
    # --------------------------------------------------

    print("\nTraining")
    print("--------")

    history = model.fit(
        X_train,
        y_train,
        validation_data=(
            X_val,
            y_val,
        ),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    # --------------------------------------------------
    # 8. Predict validation sequences
    # --------------------------------------------------

    print("\nValidation prediction")
    print("---------------------")

    y_pred = model.predict(
        X_val,
        batch_size=batch_size,
        verbose=1,
    )

    # --------------------------------------------------
    # 9. Metrics
    # --------------------------------------------------

    metrics = calculate_regression_metrics(
        y_val,
        y_pred,
    )

    print("\nValidation metrics")
    print("-------------------")
    print(
        f"MAE:  {metrics['MAE']:.4f}"
    )
    print(
        f"RMSE: {metrics['RMSE']:.4f}"
    )

    # --------------------------------------------------
    # 10. Save model
    # --------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model.save(MODEL_PATH)

    print("\nModel saved")
    print("-----------")
    print(MODEL_PATH)

    return model, history, metrics


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Train the RainGuard ConvLSTM nowcasting model."
        )
    )

    parser.add_argument(
        "--data",
        required=True,
        help=(
            "Path to a genuine high-frequency "
            "weather tensor (.npy/.npz)."
        ),
    )

    parser.add_argument(
        "--timestep",
        type=int,
        default=30,
        help="Dataset timestep in minutes.",
    )

    parser.add_argument(
        "--source",
        default="DWR radar",
        help="Dataset source type.",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Maximum training epochs.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Training batch size.",
    )

    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.20,
        help="Chronological validation fraction.",
    )

    args = parser.parse_args()

    data_path = Path(args.data)

    tensor = load_tensor(
        data_path
    )

    train_nowcaster(
        tensor=tensor,
        timestep_minutes=args.timestep,
        source_type=args.source,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_fraction=(
            args.validation_fraction
        ),
    )


if __name__ == "__main__":
    main()