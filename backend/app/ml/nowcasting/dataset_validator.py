"""
RainGuard AI - Nowcasting Dataset Validator

Validates whether a weather dataset is suitable for
0–3 hour high-frequency nowcasting.

This validator intentionally rejects daily datasets for
ConvLSTM nowcasting training.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class DatasetValidationResult:
    """Result of validating a nowcasting dataset."""

    valid: bool
    eligible_for_nowcasting: bool
    messages: list[str]


class NowcastingDatasetValidator:
    """
    Validate a harmonized weather tensor before ConvLSTM training.

    Expected tensor:
        (time, latitude, longitude, features)
    """

    def __init__(
        self,
        expected_timestep_minutes: int = 30,
        expected_features: int = 10,
        minimum_time_steps: int = 12,
        max_missing_fraction: float = 0.50,
    ):
        self.expected_timestep_minutes = (
            expected_timestep_minutes
        )
        self.expected_features = expected_features
        self.minimum_time_steps = minimum_time_steps
        self.max_missing_fraction = max_missing_fraction

    def validate(
        self,
        tensor: np.ndarray,
        timestep_minutes: Optional[int] = None,
        source_type: str = "unknown",
    ) -> DatasetValidationResult:
        """
        Validate tensor structure and nowcasting suitability.

        Parameters
        ----------
        tensor:
            Weather tensor with shape
            (time, latitude, longitude, features).

        timestep_minutes:
            Actual temporal spacing of the dataset.

        source_type:
            Data source description, e.g. "radar",
            "satellite", "nwp", or "daily_imd".

        Returns
        -------
        DatasetValidationResult
        """

        messages: list[str] = []
        valid = True
        eligible = True

        # --------------------------------------------------
        # Basic tensor validation
        # --------------------------------------------------

        if not isinstance(tensor, np.ndarray):
            return DatasetValidationResult(
                valid=False,
                eligible_for_nowcasting=False,
                messages=[
                    "Dataset must be a NumPy array."
                ],
            )

        if tensor.ndim != 4:
            return DatasetValidationResult(
                valid=False,
                eligible_for_nowcasting=False,
                messages=[
                    "Expected tensor shape "
                    "(time, latitude, longitude, features)."
                ],
            )

        time_steps, height, width, features = tensor.shape

        messages.append(
            f"Tensor shape: {tensor.shape}"
        )

        # --------------------------------------------------
        # Time dimension
        # --------------------------------------------------

        if time_steps < self.minimum_time_steps:
            valid = False
            eligible = False

            messages.append(
                f"Insufficient time steps: {time_steps}. "
                f"Need at least {self.minimum_time_steps}."
            )
        else:
            messages.append(
                f"Time steps: {time_steps} ✓"
            )

        # --------------------------------------------------
        # Spatial dimensions
        # --------------------------------------------------

        if height < 2 or width < 2:
            valid = False
            eligible = False

            messages.append(
                "Spatial grid is too small."
            )
        else:
            messages.append(
                f"Spatial grid: {height} × {width} ✓"
            )

        # --------------------------------------------------
        # Feature dimension
        # --------------------------------------------------

        if features != self.expected_features:
            valid = False

            messages.append(
                f"Feature count: {features}. "
                f"Expected {self.expected_features}."
            )
        else:
            messages.append(
                f"Feature count: {features} ✓"
            )

        # --------------------------------------------------
        # Temporal resolution
        # --------------------------------------------------

        if timestep_minutes is None:
            eligible = False

            messages.append(
                "Temporal resolution was not provided. "
                "Cannot verify nowcasting eligibility."
            )

        elif timestep_minutes != (
            self.expected_timestep_minutes
        ):
            eligible = False

            messages.append(
                f"Timestep: {timestep_minutes} minutes. "
                f"Expected "
                f"{self.expected_timestep_minutes} minutes "
                f"for this nowcasting configuration."
            )
        else:
            messages.append(
                f"Timestep: {timestep_minutes} minutes ✓"
            )

        # --------------------------------------------------
        # Source type
        # --------------------------------------------------

        source = source_type.lower().strip()

        if source in {
            "daily",
            "daily_imd",
            "imd_daily",
        }:
            eligible = False

            messages.append(
                "Daily rainfall data is not eligible for "
                "30-minute ConvLSTM nowcasting."
            )

        elif source in {
            "radar",
            "dwr",
            "satellite",
            "insat",
            "satellite_radar",
        }:
            messages.append(
                f"Source type '{source_type}' is "
                "compatible with high-frequency nowcasting "
                "when temporal resolution is appropriate."
            )

        else:
            messages.append(
                f"Source type '{source_type}' requires "
                "manual suitability verification."
            )

        # --------------------------------------------------
        # Missing data
        # --------------------------------------------------

        missing_fraction = float(
            np.isnan(tensor).mean()
        )

        messages.append(
            f"Missing-value fraction: "
            f"{missing_fraction:.2%}"
        )

        if missing_fraction > self.max_missing_fraction:
            eligible = False

            messages.append(
                "Missing-value fraction exceeds the "
                f"{self.max_missing_fraction:.0%} limit."
            )
        else:
            messages.append(
                "Missing-value fraction within configured limit ✓"
            )

        # --------------------------------------------------
        # Final status
        # --------------------------------------------------

        if not valid:
            eligible = False

        if eligible:
            messages.append(
                "STATUS: Dataset is eligible for "
                "ConvLSTM nowcasting."
            )
        else:
            messages.append(
                "STATUS: Dataset is NOT eligible for "
                "ConvLSTM nowcasting."
            )

        return DatasetValidationResult(
            valid=valid,
            eligible_for_nowcasting=eligible,
            messages=messages,
        )


if __name__ == "__main__":
    validator = NowcastingDatasetValidator()

    # ------------------------------------------------------
    # TEST 1: High-frequency radar-like dataset
    # ------------------------------------------------------

    radar_tensor = np.random.default_rng(42).random(
        (
            18,
            51,
            52,
            10,
        ),
        dtype=np.float32,
    )

    radar_result = validator.validate(
        radar_tensor,
        timestep_minutes=30,
        source_type="DWR radar",
    )

    print("\nRainGuard Dataset Validator")
    print("============================")
    print("\nTEST 1 — High-frequency radar")
    print("--------------------------------")

    for message in radar_result.messages:
        print(message)

    assert radar_result.valid
    assert radar_result.eligible_for_nowcasting

    # ------------------------------------------------------
    # TEST 2: Daily IMD dataset
    # ------------------------------------------------------

    daily_tensor = np.random.default_rng(123).random(
        (
            365,
            51,
            52,
            10,
        ),
        dtype=np.float32,
    )

    daily_result = validator.validate(
        daily_tensor,
        timestep_minutes=1440,
        source_type="daily_imd",
    )

    print("\nTEST 2 — Daily IMD rainfall")
    print("--------------------------------")

    for message in daily_result.messages:
        print(message)

    assert daily_result.valid
    assert not daily_result.eligible_for_nowcasting

    print("\n============================")
    print("STATUS: Dataset validator tests PASSED")
    print("============================")