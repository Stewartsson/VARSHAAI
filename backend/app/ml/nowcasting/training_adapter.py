"""
RainGuard AI - Nowcasting Training Adapter

Converts harmonized weather tensors into training-ready
ConvLSTM sequences.

Expected tensor format:
    (time, latitude, longitude, features)

Output:
    X -> (samples, input_steps, latitude, longitude, features)
    y -> (samples, forecast_steps, latitude, longitude)

Important:
    This adapter does NOT create synthetic 30-minute weather data.
    It expects genuine time-resolved observations such as DWR
    radar / satellite sequences.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class NowcastingTrainingData:
    """Container for ConvLSTM training arrays."""

    X: np.ndarray
    y: np.ndarray
    input_steps: int
    forecast_steps: int
    timestep_minutes: int


class NowcastingTrainingAdapter:
    """
    Prepare time-resolved weather tensors for ConvLSTM training.
    """

    def __init__(
        self,
        input_steps: int = 6,
        forecast_steps: int = 6,
        timestep_minutes: int = 30,
        target_feature: int = 0,
    ):
        self.input_steps = input_steps
        self.forecast_steps = forecast_steps
        self.timestep_minutes = timestep_minutes
        self.target_feature = target_feature

    def validate_tensor(self, tensor: np.ndarray) -> None:
        """Validate the input tensor."""

        if not isinstance(tensor, np.ndarray):
            raise TypeError("tensor must be a NumPy array")

        if tensor.ndim != 4:
            raise ValueError(
                "Expected tensor shape "
                "(time, latitude, longitude, features)"
            )

        if tensor.shape[0] < self.input_steps + self.forecast_steps:
            raise ValueError(
                "Not enough time steps for one training sample. "
                f"Need at least "
                f"{self.input_steps + self.forecast_steps}, "
                f"received {tensor.shape[0]}."
            )

        if not (
            0 <= self.target_feature < tensor.shape[3]
        ):
            raise ValueError(
                f"target_feature={self.target_feature} "
                f"is outside the feature range."
            )

    def build_sequences(
        self,
        tensor: np.ndarray,
    ) -> NowcastingTrainingData:
        """
        Convert a continuous weather tensor into
        supervised ConvLSTM samples.
        """

        self.validate_tensor(tensor)

        total_steps = (
            self.input_steps + self.forecast_steps
        )

        sample_count = tensor.shape[0] - total_steps + 1

        X = np.empty(
            (
                sample_count,
                self.input_steps,
                tensor.shape[1],
                tensor.shape[2],
                tensor.shape[3],
            ),
            dtype=np.float32,
        )

        y = np.empty(
            (
                sample_count,
                self.forecast_steps,
                tensor.shape[1],
                tensor.shape[2],
            ),
            dtype=np.float32,
        )

        for i in range(sample_count):
            input_start = i
            input_end = (
                i + self.input_steps
            )

            target_end = (
                input_end + self.forecast_steps
            )

            X[i] = tensor[
                input_start:input_end
            ]

            y[i] = tensor[
                input_end:target_end,
                :,
                :,
                self.target_feature,
            ]

        return NowcastingTrainingData(
            X=X,
            y=y,
            input_steps=self.input_steps,
            forecast_steps=self.forecast_steps,
            timestep_minutes=self.timestep_minutes,
        )


if __name__ == "__main__":
    # Architecture/data-interface test only.
    #
    # This creates a small structural test tensor.
    # It is NOT real weather data and must NOT be used
    # as model training data.

    time_steps = 18
    height = 8
    width = 8
    features = 10

    dummy_tensor = np.random.default_rng(42).random(
        (
            time_steps,
            height,
            width,
            features,
        ),
        dtype=np.float32,
    )

    adapter = NowcastingTrainingAdapter(
        input_steps=6,
        forecast_steps=6,
        timestep_minutes=30,
        target_feature=0,
    )

    data = adapter.build_sequences(dummy_tensor)

    print("\nRainGuard Nowcasting Training Adapter")
    print("-------------------------------------")
    print("Source tensor:", dummy_tensor.shape)
    print("X shape:      ", data.X.shape)
    print("y shape:      ", data.y.shape)
    print("Input period: ", data.input_steps * data.timestep_minutes, "minutes")
    print("Forecast:     ", data.forecast_steps * data.timestep_minutes, "minutes")
    print("-------------------------------------")

    assert data.X.shape == (
        7,
        6,
        8,
        8,
        10,
    )

    assert data.y.shape == (
        7,
        6,
        8,
        8,
    )

    print("STATUS: Training adapter test PASSED")