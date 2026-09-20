"""
RainGuard AI - SCS-CN Rainfall-Runoff Model

Purpose:
    Convert forecast rainfall into estimated runoff depth.

Method:
    Simplified SCS Curve Number (SCS-CN) method.

Inputs:
    - Rainfall depth (mm)
    - Curve Number (CN)

Output:
    - Direct runoff depth (mm)

Important:
    This is a screening-level hydrological model.
    It is not a replacement for a calibrated HEC-RAS/
    LISFLOOD model.

CN interpretation:
    Higher CN -> more runoff
    Lower CN  -> more infiltration/storage
"""

from __future__ import annotations

import numpy as np


class SCSCNRunoffModel:
    """
    Simplified SCS Curve Number runoff model.
    """

    def __init__(
        self,
        initial_abstraction_ratio: float = 0.2,
    ):
        if not (
            0.0 < initial_abstraction_ratio < 1.0
        ):
            raise ValueError(
                "initial_abstraction_ratio must be "
                "between 0 and 1."
            )

        self.initial_abstraction_ratio = (
            initial_abstraction_ratio
        )

    def validate_curve_number(
        self,
        curve_number: np.ndarray | float,
    ) -> np.ndarray:
        """
        Validate and convert Curve Number values.
        """

        cn = np.asarray(
            curve_number,
            dtype=np.float32,
        )

        if np.any(
            (cn <= 0)
            | (cn > 100)
        ):
            raise ValueError(
                "Curve Number must be > 0 and <= 100."
            )

        return cn

    def potential_max_retention(
        self,
        curve_number: np.ndarray | float,
    ) -> np.ndarray:
        """
        Calculate potential maximum retention S.

        S = 25400 / CN - 254

        Units:
            millimetres
        """

        cn = self.validate_curve_number(
            curve_number
        )

        return (
            25400.0 / cn
        ) - 254.0

    def runoff_depth(
        self,
        rainfall_mm: np.ndarray | float,
        curve_number: np.ndarray | float,
    ) -> np.ndarray:
        """
        Calculate direct runoff depth.

        Standard SCS-CN formulation:

            Ia = 0.2S

            Q = (P - Ia)^2 / (P + 0.8S)

        where:

            P  = rainfall depth
            S  = potential maximum retention
            Ia = initial abstraction
            Q  = direct runoff

        If P <= Ia, runoff is zero.
        """

        rainfall = np.asarray(
            rainfall_mm,
            dtype=np.float32,
        )

        if np.any(
            rainfall < 0
        ):
            raise ValueError(
                "Rainfall cannot be negative."
            )

        S = self.potential_max_retention(
            curve_number
        )

        Ia = (
            self.initial_abstraction_ratio
            * S
        )

        excess = (
            rainfall - Ia
        )

        runoff = np.zeros_like(
            rainfall,
            dtype=np.float32,
        )

        valid = excess > 0

        runoff[valid] = (
            excess[valid] ** 2
        ) / (
            rainfall[valid]
            + (
                1.0
                - self.initial_abstraction_ratio
            )
            * S[valid]
        )

        return np.maximum(
            runoff,
            0.0,
        )

    def runoff_coefficient(
        self,
        rainfall_mm: np.ndarray | float,
        curve_number: np.ndarray | float,
    ) -> np.ndarray:
        """
        Estimate the fraction of rainfall becoming
        direct runoff.
        """

        rainfall = np.asarray(
            rainfall_mm,
            dtype=np.float32,
        )

        runoff = self.runoff_depth(
            rainfall,
            curve_number,
        )

        coefficient = np.zeros_like(
            rainfall,
            dtype=np.float32,
        )

        positive_rain = rainfall > 0

        coefficient[
            positive_rain
        ] = (
            runoff[positive_rain]
            / rainfall[positive_rain]
        )

        return np.clip(
            coefficient,
            0.0,
            1.0,
        )


if __name__ == "__main__":

    print("\nRainGuard SCS-CN Runoff Model")
    print("============================")

    model = SCSCNRunoffModel()

    # --------------------------------------------------
    # Test 1: Scalar rainfall
    # --------------------------------------------------

    rainfall = 100.0
    curve_number = 80.0

    runoff = model.runoff_depth(
        rainfall,
        curve_number,
    )

    print("\nScalar test")
    print("-----------")
    print(
        "Rainfall:",
        rainfall,
        "mm",
    )

    print(
        "Curve Number:",
        curve_number,
    )

    print(
        "Runoff:",
        f"{float(runoff):.2f}",
        "mm",
    )

    assert float(runoff) > 0
    assert float(runoff) < rainfall

    # --------------------------------------------------
    # Test 2: No runoff below initial abstraction
    # --------------------------------------------------

    low_rainfall = 1.0

    low_runoff = model.runoff_depth(
        low_rainfall,
        curve_number,
    )

    print("\nLow rainfall test")
    print("-----------------")
    print(
        "Rainfall:",
        low_rainfall,
        "mm",
    )

    print(
        "Runoff:",
        f"{float(low_runoff):.2f}",
        "mm",
    )

    assert float(low_runoff) == 0.0

    # --------------------------------------------------
    # Test 3: Spatial grid
    # --------------------------------------------------

    rainfall_grid = np.array(
        [
            [25.0, 50.0, 100.0],
            [75.0, 125.0, 200.0],
            [10.0, 150.0, 300.0],
        ],
        dtype=np.float32,
    )

    cn_grid = np.array(
        [
            [60.0, 70.0, 80.0],
            [65.0, 75.0, 85.0],
            [55.0, 90.0, 95.0],
        ],
        dtype=np.float32,
    )

    runoff_grid = model.runoff_depth(
        rainfall_grid,
        cn_grid,
    )

    coefficient_grid = (
        model.runoff_coefficient(
            rainfall_grid,
            cn_grid,
        )
    )

    print("\nSpatial grid test")
    print("-----------------")
    print(
        "Rainfall grid shape:",
        rainfall_grid.shape,
    )

    print(
        "Runoff grid shape:",
        runoff_grid.shape,
    )

    print(
        "Runoff minimum:",
        f"{runoff_grid.min():.2f}",
        "mm",
    )

    print(
        "Runoff maximum:",
        f"{runoff_grid.max():.2f}",
        "mm",
    )

    print(
        "Runoff coefficient range:",
        f"{coefficient_grid.min():.2f}"
        f" - "
        f"{coefficient_grid.max():.2f}",
    )

    assert runoff_grid.shape == (
        3,
        3,
    )

    assert np.all(
        runoff_grid >= 0
    )

    assert np.all(
        runoff_grid <= rainfall_grid
    )

    assert np.all(
        coefficient_grid >= 0
    )

    assert np.all(
        coefficient_grid <= 1
    )

    print(
        "\nSTATUS: SCS-CN runoff model test PASSED"
    )