import numpy as np


class MLTensorBuilder:
    """
    Builds ML-ready tensors from harmonized RainGuard
    multi-source weather fields.

    Tensor convention:

        (time, latitude, longitude, features)

    This is the interface that the future ConvLSTM/U-Net
    nowcasting model will consume.
    """

    DEFAULT_FEATURES = [
        "radar_rainfall_mm",
        "radar_reflectivity_dbz",
        "satellite_qpe_mm",
        "cloud_top_temperature_k",
        "aws_rainfall_mm",
        "arg_rainfall_mm",
        "nwp_precipitation_mm",
        "nwp_humidity",
        "nwp_wind_speed_ms",
        "nwp_pressure_hpa",
    ]

    def __init__(
        self,
        grid_shape,
        feature_names=None,
    ):
        self.grid_shape = tuple(grid_shape)

        self.feature_names = (
            feature_names
            if feature_names is not None
            else self.DEFAULT_FEATURES.copy()
        )

        if len(self.grid_shape) != 2:
            raise ValueError(
                "grid_shape must contain "
                "(rows, columns)."
            )

    def create_empty(
        self,
        time_steps: int,
    ):
        """
        Create an empty ML tensor.

        Shape:

            (time, latitude, longitude, features)
        """

        if time_steps <= 0:
            raise ValueError(
                "time_steps must be greater than zero."
            )

        return np.full(
            (
                time_steps,
                self.grid_shape[0],
                self.grid_shape[1],
                len(self.feature_names),
            ),
            np.nan,
            dtype=np.float32,
        )

    def set_feature(
        self,
        tensor,
        time_index,
        feature_name,
        field,
    ):
        """
        Insert one spatial field into the tensor.
        """

        if feature_name not in self.feature_names:
            raise ValueError(
                f"Unknown feature: {feature_name}"
            )

        field = np.asarray(
            field,
            dtype=np.float32,
        )

        if field.shape != self.grid_shape:
            raise ValueError(
                "Field shape does not match "
                "the common grid."
            )

        if not (
            0 <= time_index < tensor.shape[0]
        ):
            raise IndexError(
                "time_index is outside tensor range."
            )

        feature_index = (
            self.feature_names.index(
                feature_name
            )
        )

        tensor[
            time_index,
            :,
            :,
            feature_index,
        ] = field

    def validate(
        self,
        tensor,
    ):
        """
        Validate tensor dimensions and report
        missing-value statistics.
        """

        tensor = np.asarray(
            tensor,
            dtype=np.float32,
        )

        expected_shape = (
            tensor.shape[0],
            self.grid_shape[0],
            self.grid_shape[1],
            len(self.feature_names),
        )

        if tensor.shape != expected_shape:
            raise ValueError(
                "Tensor shape does not match "
                "expected dimensions."
            )

        total_values = tensor.size
        missing_values = int(
            np.isnan(tensor).sum()
        )

        return {
            "shape": tensor.shape,
            "time_steps": tensor.shape[0],
            "rows": tensor.shape[1],
            "columns": tensor.shape[2],
            "features": tensor.shape[3],
            "feature_names": self.feature_names,
            "total_values": total_values,
            "missing_values": missing_values,
            "missing_fraction": (
                missing_values / total_values
                if total_values > 0
                else 0.0
            ),
        }

    def describe(self):
        return {
            "tensor_order": (
                "time, latitude, longitude, features"
            ),
            "grid_shape": self.grid_shape,
            "feature_count": len(
                self.feature_names
            ),
            "features": self.feature_names,
        }


if __name__ == "__main__":

    print("RainGuard ML Tensor Builder Test")
    print("--------------------------------")

    # Small demonstration grid.
    grid_shape = (51, 52)

    builder = MLTensorBuilder(
        grid_shape=grid_shape
    )

    print("\nTensor configuration:")

    for key, value in builder.describe().items():
        print(
            f"  {key}: {value}"
        )

    # Six historical time steps.
    tensor = builder.create_empty(
        time_steps=6
    )

    print(
        "\nEmpty tensor shape:"
    )

    print(
        f"  {tensor.shape}"
    )

    # Synthetic radar rainfall field.
    radar_rainfall = np.full(
        grid_shape,
        20.0,
        dtype=np.float32,
    )

    # Synthetic radar reflectivity.
    radar_reflectivity = np.full(
        grid_shape,
        35.0,
        dtype=np.float32,
    )

    # Insert features at the latest time step.
    builder.set_feature(
        tensor,
        time_index=5,
        feature_name="radar_rainfall_mm",
        field=radar_rainfall,
    )

    builder.set_feature(
        tensor,
        time_index=5,
        feature_name="radar_reflectivity_dbz",
        field=radar_reflectivity,
    )

    statistics = builder.validate(
        tensor
    )

    print(
        "\nValidated tensor:"
    )

    for key, value in statistics.items():
        print(
            f"  {key}: {value}"
        )

    print("\nSample values:")

    radar_index = (
        builder.feature_names.index(
            "radar_rainfall_mm"
        )
    )

    reflectivity_index = (
        builder.feature_names.index(
            "radar_reflectivity_dbz"
        )
    )

    print(
        "  radar rainfall: "
        f"{tensor[5, 27, 32, radar_index]} mm"
    )

    print(
        "  radar reflectivity: "
        f"{tensor[5, 27, 32, reflectivity_index]} dBZ"
    )

    print("\n--------------------------------")
    print("ML tensor builder test OK.")