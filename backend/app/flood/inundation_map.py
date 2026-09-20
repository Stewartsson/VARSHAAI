"""
RainGuard AI - Inundation Map Builder

Purpose:
    Build a spatial flood-inundation product from the
    estimated flood-depth raster.

Outputs:
    1. Flood extent mask
    2. Flood depth in metres
    3. Risk classes
    4. Summary statistics

Risk classes:
    0 = No flood
    1 = Low
    2 = Moderate
    3 = High
    4 = Severe

Important:
    This is a prototype inundation classification layer.
    Final operational thresholds should be calibrated
    against observed flood-depth/extent data.
"""

from __future__ import annotations

import numpy as np


class InundationMapBuilder:
    """
    Converts flood-depth grids into an inundation/risk map.
    """

    def __init__(
        self,
        low_depth_m: float = 0.05,
        moderate_depth_m: float = 0.15,
        high_depth_m: float = 0.30,
        severe_depth_m: float = 0.60,
    ):
        thresholds = [
            low_depth_m,
            moderate_depth_m,
            high_depth_m,
            severe_depth_m,
        ]

        if any(
            threshold < 0
            for threshold in thresholds
        ):
            raise ValueError(
                "Depth thresholds cannot be negative."
            )

        if not (
            low_depth_m
            < moderate_depth_m
            < high_depth_m
            < severe_depth_m
        ):
            raise ValueError(
                "Depth thresholds must be strictly "
                "increasing."
            )

        self.low_depth_m = low_depth_m
        self.moderate_depth_m = moderate_depth_m
        self.high_depth_m = high_depth_m
        self.severe_depth_m = severe_depth_m

    @staticmethod
    def _validate_depth(
        flood_depth_m: np.ndarray | list,
    ) -> np.ndarray:
        """
        Validate flood-depth raster.
        """

        depth = np.asarray(
            flood_depth_m,
            dtype=np.float32,
        )

        if depth.ndim != 2:
            raise ValueError(
                "Flood-depth raster must be 2D."
            )

        if np.any(
            np.isfinite(depth)
            & (depth < 0)
        ):
            raise ValueError(
                "Flood depth cannot be negative."
            )

        return depth

    def flood_extent(
        self,
        flood_depth_m: np.ndarray,
    ) -> np.ndarray:
        """
        Create binary inundation mask.

        0 = not flooded
        1 = flooded

        Flooding begins at low_depth_m.
        """

        depth = self._validate_depth(
            flood_depth_m
        )

        extent = np.zeros(
            depth.shape,
            dtype=np.uint8,
        )

        flooded = (
            np.isfinite(depth)
            & (
                depth
                >= self.low_depth_m
            )
        )

        extent[flooded] = 1

        return extent

    def classify_risk(
        self,
        flood_depth_m: np.ndarray,
    ) -> np.ndarray:
        """
        Classify flood depth into five risk levels.

        0 = No flood
        1 = Low
        2 = Moderate
        3 = High
        4 = Severe
        """

        depth = self._validate_depth(
            flood_depth_m
        )

        risk = np.zeros(
            depth.shape,
            dtype=np.uint8,
        )

        finite = np.isfinite(
            depth
        )

        risk[
            finite
            & (
                depth
                >= self.low_depth_m
            )
            & (
                depth
                < self.moderate_depth_m
            )
        ] = 1

        risk[
            finite
            & (
                depth
                >= self.moderate_depth_m
            )
            & (
                depth
                < self.high_depth_m
            )
        ] = 2

        risk[
            finite
            & (
                depth
                >= self.high_depth_m
            )
            & (
                depth
                < self.severe_depth_m
            )
        ] = 3

        risk[
            finite
            & (
                depth
                >= self.severe_depth_m
            )
        ] = 4

        return risk

    def risk_labels(
        self,
        risk_grid: np.ndarray,
    ) -> dict[int, str]:
        """
        Return human-readable risk labels.
        """

        return {
            0: "No Flood",
            1: "Low",
            2: "Moderate",
            3: "High",
            4: "Severe",
        }

    def build(
        self,
        flood_depth_m: np.ndarray,
    ) -> dict[str, np.ndarray | dict]:
        """
        Build the complete inundation product.

        Returns:
            {
                "flood_depth_m": ...,
                "flood_extent": ...,
                "risk_class": ...,
                "risk_labels": ...
            }
        """

        depth = self._validate_depth(
            flood_depth_m
        )

        extent = self.flood_extent(
            depth
        )

        risk = self.classify_risk(
            depth
        )

        return {
            "flood_depth_m": depth,
            "flood_extent": extent,
            "risk_class": risk,
            "risk_labels": self.risk_labels(
                risk
            ),
        }

    def summary(
        self,
        flood_depth_m: np.ndarray,
    ) -> dict[str, float | int]:
        """
        Calculate summary statistics for the
        inundation product.
        """

        depth = self._validate_depth(
            flood_depth_m
        )

        finite = np.isfinite(
            depth
        )

        if not np.any(finite):
            return {
                "total_pixels": int(
                    depth.size
                ),
                "valid_pixels": 0,
                "flooded_pixels": 0,
                "flooded_fraction": 0.0,
                "maximum_depth_m": 0.0,
                "mean_flood_depth_m": 0.0,
            }

        extent = self.flood_extent(
            depth
        )

        flooded = (
            extent == 1
        )

        valid_count = int(
            np.sum(finite)
        )

        flooded_count = int(
            np.sum(flooded)
        )

        return {
            "total_pixels": int(
                depth.size
            ),
            "valid_pixels": valid_count,
            "flooded_pixels": flooded_count,
            "flooded_fraction": (
                flooded_count
                / valid_count
            ),
            "maximum_depth_m": float(
                np.nanmax(depth)
            ),
            "mean_flood_depth_m": float(
                np.nanmean(depth)
            ),
        }


if __name__ == "__main__":

    print("\nRainGuard Inundation Map Builder")
    print("================================")

    builder = InundationMapBuilder(
        low_depth_m=0.05,
        moderate_depth_m=0.15,
        high_depth_m=0.30,
        severe_depth_m=0.60,
    )

    # --------------------------------------------------
    # Synthetic flood-depth raster
    # --------------------------------------------------

    flood_depth = np.array(
        [
            [0.00, 0.03, 0.07, 0.12],
            [0.05, 0.18, 0.25, 0.35],
            [0.02, 0.14, 0.42, 0.65],
            [0.00, 0.08, 0.31, 0.80],
        ],
        dtype=np.float32,
    )

    print("\nFlood depth raster (m)")
    print("----------------------")
    print(flood_depth)

    # --------------------------------------------------
    # Build inundation product
    # --------------------------------------------------

    product = builder.build(
        flood_depth
    )

    extent = product[
        "flood_extent"
    ]

    risk = product[
        "risk_class"
    ]

    print("\nFlood extent")
    print("------------")
    print(extent)

    print("\nRisk classification")
    print("-------------------")
    print(risk)

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    statistics = builder.summary(
        flood_depth
    )

    print("\nInundation summary")
    print("------------------")

    print(
        "Total pixels:",
        statistics["total_pixels"],
    )

    print(
        "Valid pixels:",
        statistics["valid_pixels"],
    )

    print(
        "Flooded pixels:",
        statistics["flooded_pixels"],
    )

    print(
        "Flooded fraction:",
        f"{statistics['flooded_fraction']:.2%}",
    )

    print(
        "Maximum depth:",
        f"{statistics['maximum_depth_m']:.2f}",
        "m",
    )

    print(
        "Mean depth:",
        f"{statistics['mean_flood_depth_m']:.3f}",
        "m",
    )

    # --------------------------------------------------
    # Risk counts
    # --------------------------------------------------

    print("\nRisk counts")
    print("-----------")

    labels = builder.risk_labels(
        risk
    )

    for risk_id in range(5):
        count = int(
            np.sum(
                risk == risk_id
            )
        )

        print(
            f"{risk_id} - "
            f"{labels[risk_id]:<10}: "
            f"{count}"
        )

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert (
        product["flood_depth_m"].shape
        == flood_depth.shape
    )

    assert (
        product["flood_extent"].shape
        == flood_depth.shape
    )

    assert (
        product["risk_class"].shape
        == flood_depth.shape
    )

    assert np.all(
        np.isin(
            extent,
            [0, 1],
        )
    )

    assert np.all(
        np.isin(
            risk,
            [0, 1, 2, 3, 4],
        )
    )

    assert (
        risk[0, 0] == 0
    )

    assert (
        risk[3, 3] == 4
    )

    assert (
        extent[0, 0] == 0
    )

    assert (
        extent[3, 3] == 1
    )

    print(
        "\nSTATUS: Inundation Map Builder test PASSED"
    )