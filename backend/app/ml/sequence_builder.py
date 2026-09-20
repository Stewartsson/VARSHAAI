import numpy as np


class NowcastingSequenceBuilder:
    """
    Converts a continuous ML tensor into supervised
    sequence-to-target samples for short-range nowcasting.

    Input tensor:
        (time, latitude, longitude, features)

    Output:
        X = (samples, input_steps, latitude, longitude, features)
        y = (samples, forecast_steps, latitude, longitude)
    """

    def __init__(
        self,
        input_steps: int = 6,
        forecast_steps: int = 6,
        target_feature: int = 0,
    ):
        if input_steps <= 0:
            raise ValueError(
                "input_steps must be greater than zero."
            )

        if forecast_steps <= 0:
            raise ValueError(
                "forecast_steps must be greater than zero."
            )

        if target_feature < 0:
            raise ValueError(
                "target_feature cannot be negative."
            )

        self.input_steps = input_steps
        self.forecast_steps = forecast_steps
        self.target_feature = target_feature

    def build(
        self,
        tensor: np.ndarray,
    ):
        """
        Build sliding-window supervised samples.

        Example with 30-minute data:

            input_steps = 6
                = previous 3 hours

            forecast_steps = 6
                = next 3 hours
        """

        tensor = np.asarray(
            tensor,
            dtype=np.float32,
        )

        if tensor.ndim != 4:
            raise ValueError(
                "tensor must have shape "
                "(time, latitude, longitude, features)."
            )

        time_steps = tensor.shape[0]
        feature_count = tensor.shape[3]

        if self.target_feature >= feature_count:
            raise ValueError(
                "target_feature is outside "
                "the tensor feature range."
            )

        required_steps = (
            self.input_steps
            + self.forecast_steps
        )

        if time_steps < required_steps:
            raise ValueError(
                f"Tensor requires at least "
                f"{required_steps} time steps."
            )

        X_samples = []
        y_samples = []

        for start in range(
            time_steps - required_steps + 1
        ):

            input_end = (
                start + self.input_steps
            )

            target_end = (
                input_end
                + self.forecast_steps
            )

            X_window = tensor[
                start:input_end
            ]

            y_window = tensor[
                input_end:target_end,
                :,
                :,
                self.target_feature,
            ]

            X_samples.append(
                X_window
            )

            y_samples.append(
                y_window
            )

        X = np.stack(
            X_samples
        ).astype(
            np.float32
        )

        y = np.stack(
            y_samples
        ).astype(
            np.float32
        )

        return X, y

    def describe(self):
        return {
            "input_steps": self.input_steps,
            "forecast_steps": self.forecast_steps,
            "target_feature": self.target_feature,
            "input_duration_minutes": (
                self.input_steps * 30
            ),
            "forecast_duration_minutes": (
                self.forecast_steps * 30
            ),
        }


if __name__ == "__main__":

    print("RainGuard Nowcasting Sequence Builder Test")
    print("------------------------------------------")

    # Demonstration:
    #
    # 12 hours of 30-minute observations
    # on a small 10 x 10 grid with 3 features.

    time_steps = 24
    rows = 10
    columns = 10
    features = 3

    tensor = np.zeros(
        (
            time_steps,
            rows,
            columns,
            features,
        ),
        dtype=np.float32,
    )

    # Give rainfall a simple increasing
    # synthetic signal.
    for t in range(time_steps):
        tensor[
            t,
            :,
            :,
            0
        ] = float(t)

    builder = NowcastingSequenceBuilder(
        input_steps=6,
        forecast_steps=6,
        target_feature=0,
    )

    print("\nConfiguration:")

    for key, value in builder.describe().items():
        print(
            f"  {key}: {value}"
        )

    X, y = builder.build(
        tensor
    )

    print("\nOriginal tensor:")
    print(
        f"  shape: {tensor.shape}"
    )

    print("\nSequence dataset:")

    print(
        f"  X shape: {X.shape}"
    )

    print(
        f"  y shape: {y.shape}"
    )

    print("\nFirst sample:")

    print(
        f"  Input rainfall values: "
        f"{X[0, :, 0, 0, 0]}"
    )

    print(
        f"  Target rainfall values: "
        f"{y[0, :, 0, 0]}"
    )

    print("\nLast sample:")

    print(
        f"  Input rainfall values: "
        f"{X[-1, :, 0, 0, 0]}"
    )

    print(
        f"  Target rainfall values: "
        f"{y[-1, :, 0, 0]}"
    )

    print("\n------------------------------------------")
    print("Nowcasting sequence builder test OK.")