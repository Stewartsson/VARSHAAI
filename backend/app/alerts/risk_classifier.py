"""
RainGuard AI - Flood Risk Classifier

Purpose:
    Convert flood depth and inundation information into
    operational risk levels and warning categories.

Prototype warning levels:

    GREEN  = No significant flood risk
    YELLOW = Flood Watch
    ORANGE = Flood Warning
    RED    = Severe Flood Warning

Important:
    These thresholds are prototype engineering thresholds
    for the SIH system. They are NOT claimed to be official
    IMD warning thresholds.

This module also creates a CAP-oriented alert payload.
It is not yet a complete OASIS CAP XML document.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import numpy as np


@dataclass
class RiskAssessment:
    """Summary of a spatial flood-risk assessment."""

    alert_level: str
    alert_code: int
    risk_label: str
    flooded_pixels: int
    total_valid_pixels: int
    flooded_fraction: float
    maximum_depth_m: float
    mean_flood_depth_m: float
    confidence: float


class FloodRiskClassifier:
    """
    Classify a flood-depth raster into operational
    risk levels.

    Risk codes:

        0 = GREEN
        1 = YELLOW
        2 = ORANGE
        3 = RED
    """

    LEVELS = {
        0: "GREEN",
        1: "YELLOW",
        2: "ORANGE",
        3: "RED",
    }

    LABELS = {
        0: "No significant flood risk",
        1: "Flood Watch",
        2: "Flood Warning",
        3: "Severe Flood Warning",
    }

    def __init__(
        self,
        flood_threshold_m: float = 0.05,
        orange_depth_m: float = 0.30,
        red_depth_m: float = 0.60,
        orange_fraction: float = 0.25,
        red_fraction: float = 0.50,
    ):
        """
        Configure flood-risk thresholds.

        flood_threshold_m:
            Minimum depth considered flooded.

        orange_depth_m:
            Depth supporting ORANGE risk.

        red_depth_m:
            Depth supporting RED risk.

        orange_fraction:
            Flooded spatial fraction supporting ORANGE.

        red_fraction:
            Flooded spatial fraction supporting RED.
        """

        if flood_threshold_m < 0:
            raise ValueError(
                "flood_threshold_m cannot be negative."
            )

        if orange_depth_m <= flood_threshold_m:
            raise ValueError(
                "orange_depth_m must be greater than "
                "flood_threshold_m."
            )

        if red_depth_m <= orange_depth_m:
            raise ValueError(
                "red_depth_m must be greater than "
                "orange_depth_m."
            )

        if not 0.0 <= orange_fraction <= 1.0:
            raise ValueError(
                "orange_fraction must be between 0 and 1."
            )

        if not 0.0 <= red_fraction <= 1.0:
            raise ValueError(
                "red_fraction must be between 0 and 1."
            )

        if orange_fraction > red_fraction:
            raise ValueError(
                "orange_fraction cannot exceed "
                "red_fraction."
            )

        self.flood_threshold_m = flood_threshold_m
        self.orange_depth_m = orange_depth_m
        self.red_depth_m = red_depth_m
        self.orange_fraction = orange_fraction
        self.red_fraction = red_fraction

    @staticmethod
    def _validate_depth(
        flood_depth_m: np.ndarray | list,
    ) -> np.ndarray:
        """Validate the flood-depth raster."""

        depth = np.asarray(
            flood_depth_m,
            dtype=np.float32,
        )

        if depth.ndim != 2:
            raise ValueError(
                "Flood depth must be a 2D raster."
            )

        if np.any(
            np.isfinite(depth) & (depth < 0)
        ):
            raise ValueError(
                "Flood depth cannot be negative."
            )

        return depth

    def flooded_mask(
        self,
        flood_depth_m: np.ndarray,
    ) -> np.ndarray:
        """
        Create a binary flood mask.

        0 = not flooded
        1 = flooded
        """

        depth = self._validate_depth(
            flood_depth_m
        )

        mask = np.zeros(
            depth.shape,
            dtype=np.uint8,
        )

        flooded = (
            np.isfinite(depth)
            & (
                depth >= self.flood_threshold_m
            )
        )

        mask[flooded] = 1

        return mask

    def spatial_statistics(
        self,
        flood_depth_m: np.ndarray,
    ) -> dict[str, float | int]:
        """Calculate spatial flood statistics."""

        depth = self._validate_depth(
            flood_depth_m
        )

        valid = np.isfinite(depth)

        valid_pixels = int(
            np.sum(valid)
        )

        if valid_pixels == 0:
            return {
                "total_pixels": int(depth.size),
                "valid_pixels": 0,
                "flooded_pixels": 0,
                "flooded_fraction": 0.0,
                "maximum_depth_m": 0.0,
                "mean_flood_depth_m": 0.0,
            }

        flooded = (
            valid
            & (
                depth >= self.flood_threshold_m
            )
        )

        flooded_pixels = int(
            np.sum(flooded)
        )

        flooded_fraction = (
            flooded_pixels / valid_pixels
        )

        return {
            "total_pixels": int(depth.size),
            "valid_pixels": valid_pixels,
            "flooded_pixels": flooded_pixels,
            "flooded_fraction": flooded_fraction,
            "maximum_depth_m": float(
                np.nanmax(depth)
            ),
            "mean_flood_depth_m": float(
                np.nanmean(depth)
            ),
        }

    def classify(
        self,
        flood_depth_m: np.ndarray,
    ) -> RiskAssessment:
        """
        Classify the spatial flood product.

        Decision rules:

        RED:
            maximum depth >= red_depth_m
            OR
            flooded fraction >= red_fraction

        ORANGE:
            maximum depth >= orange_depth_m
            OR
            flooded fraction >= orange_fraction

        YELLOW:
            flooding exists but ORANGE criteria
            are not reached

        GREEN:
            no flooding detected
        """

        statistics = self.spatial_statistics(
            flood_depth_m
        )

        flooded_pixels = int(
            statistics["flooded_pixels"]
        )

        flooded_fraction = float(
            statistics["flooded_fraction"]
        )

        maximum_depth = float(
            statistics["maximum_depth_m"]
        )

        mean_depth = float(
            statistics["mean_flood_depth_m"]
        )

        # --------------------------------------------------
        # IMPORTANT:
        #
        # Depth is compared with depth thresholds.
        # Fraction is compared with fraction thresholds.
        # --------------------------------------------------

        if (
            maximum_depth >= self.red_depth_m
            or flooded_fraction >= self.red_fraction
        ):
            alert_code = 3

        elif (
            maximum_depth >= self.orange_depth_m
            or flooded_fraction >= self.orange_fraction
        ):
            alert_code = 2

        elif flooded_pixels > 0:
            alert_code = 1

        else:
            alert_code = 0

        # --------------------------------------------------
        # Prototype evidence-strength score.
        #
        # This is NOT a machine-learning probability.
        # --------------------------------------------------

        if alert_code == 0:
            confidence = 1.0

        elif alert_code == 1:
            area_strength = min(
                flooded_fraction
                / max(
                    self.orange_fraction,
                    0.01,
                ),
                1.0,
            )

            depth_strength = min(
                maximum_depth
                / max(
                    self.orange_depth_m,
                    0.01,
                ),
                1.0,
            )

            confidence = min(
                1.0,
                0.50
                + 0.20 * area_strength
                + 0.10 * depth_strength,
            )

        elif alert_code == 2:
            area_strength = min(
                flooded_fraction
                / max(
                    self.red_fraction,
                    0.01,
                ),
                1.0,
            )

            depth_strength = min(
                maximum_depth
                / max(
                    self.red_depth_m,
                    0.01,
                ),
                1.0,
            )

            confidence = min(
                1.0,
                0.65
                + 0.15 * area_strength
                + 0.15 * depth_strength,
            )

        else:
            area_strength = min(
                flooded_fraction
                / max(
                    self.red_fraction,
                    0.01,
                ),
                1.0,
            )

            depth_strength = min(
                maximum_depth
                / max(
                    self.red_depth_m,
                    0.01,
                ),
                1.0,
            )

            confidence = min(
                1.0,
                0.80
                + 0.10 * area_strength
                + 0.10 * depth_strength,
            )

        return RiskAssessment(
            alert_level=self.LEVELS[alert_code],
            alert_code=alert_code,
            risk_label=self.LABELS[alert_code],
            flooded_pixels=flooded_pixels,
            total_valid_pixels=int(
                statistics["valid_pixels"]
            ),
            flooded_fraction=flooded_fraction,
            maximum_depth_m=maximum_depth,
            mean_flood_depth_m=mean_depth,
            confidence=float(confidence),
        )

    def build_alert_payload(
        self,
        assessment: RiskAssessment,
        area_name: str,
        valid_from: str | None = None,
        valid_until: str | None = None,
    ) -> dict:
        """
        Build CAP-oriented alert metadata.

        This is not yet a complete CAP XML document.
        """

        if not area_name.strip():
            raise ValueError(
                "area_name cannot be empty."
            )

        now = datetime.now(
            timezone.utc
        )

        if valid_from is None:
            valid_from = now.isoformat()

        if valid_until is None:
            valid_until = now.isoformat()

        return {
            "identifier": (
                "RAINGUARD-"
                + now.strftime(
                    "%Y%m%d%H%M%S"
                )
            ),
            "sender": "RainGuard AI",
            "sent": now.isoformat(),
            "status": "Actual",
            "msgType": "Alert",
            "scope": "Public",
            "area": area_name,
            "severity": assessment.alert_level,
            "event": (
                "Heavy Rainfall / "
                "Flood Inundation"
            ),
            "headline": (
                f"{assessment.alert_level}: "
                f"Flood Risk for {area_name}"
            ),
            "description": (
                f"Estimated maximum flood depth "
                f"{assessment.maximum_depth_m:.2f} m; "
                f"estimated flooded fraction "
                f"{assessment.flooded_fraction:.1%}."
            ),
            "instruction": (
                "Follow official emergency guidance "
                "and local authority instructions."
            ),
            "effective": valid_from,
            "expires": valid_until,
            "risk_code": assessment.alert_code,
            "confidence": assessment.confidence,
        }


if __name__ == "__main__":

    print("\nRainGuard Flood Risk Classifier")
    print("================================")

    classifier = FloodRiskClassifier(
        flood_threshold_m=0.05,
        orange_depth_m=0.30,
        red_depth_m=0.60,
        orange_fraction=0.25,
        red_fraction=0.50,
    )

    # ==================================================
    # TEST 1 - GREEN
    # ==================================================

    green_depth = np.array(
        [
            [0.00, 0.01],
            [0.02, 0.03],
        ],
        dtype=np.float32,
    )

    green = classifier.classify(
        green_depth
    )

    print("\nGREEN test")
    print("----------")
    print(
        "Alert:",
        green.alert_level,
    )

    assert green.alert_code == 0
    assert green.alert_level == "GREEN"

    # ==================================================
    # TEST 2 - YELLOW
    # ==================================================

    yellow_depth = np.array(
        [
            [0.00, 0.00, 0.00],
            [0.00, 0.00, 0.08],
        ],
        dtype=np.float32,
    )

    yellow = classifier.classify(
        yellow_depth
    )

    print("\nYELLOW test")
    print("-----------")
    print(
        "Alert:",
        yellow.alert_level,
    )

    assert yellow.alert_code == 1
    assert yellow.alert_level == "YELLOW"

    # ==================================================
    # TEST 3 - ORANGE
    # ==================================================

    orange_depth = np.array(
        [
            [0.00, 0.00, 0.00],
            [0.00, 0.20, 0.35],
            [0.00, 0.00, 0.00],
        ],
        dtype=np.float32,
    )

    orange = classifier.classify(
        orange_depth
    )

    print("\nORANGE test")
    print("-----------")
    print(
        "Alert:",
        orange.alert_level,
    )

    assert orange.alert_code == 2
    assert orange.alert_level == "ORANGE"

    # ==================================================
    # TEST 4 - RED
    # ==================================================

    red_depth = np.array(
        [
            [0.10, 0.20, 0.40],
            [0.15, 0.60, 0.70],
            [0.20, 0.30, 0.50],
        ],
        dtype=np.float32,
    )

    red = classifier.classify(
        red_depth
    )

    print("\nRED test")
    print("--------")
    print(
        "Alert:",
        red.alert_level,
    )

    assert red.alert_code == 3
    assert red.alert_level == "RED"

    # ==================================================
    # TEST 5 - CAP-ORIENTED PAYLOAD
    # ==================================================

    payload = classifier.build_alert_payload(
        red,
        area_name="Chennai",
        valid_from=(
            "2026-09-13T12:00:00+00:00"
        ),
        valid_until=(
            "2026-09-13T18:00:00+00:00"
        ),
    )

    print("\nCAP-oriented alert payload")
    print("--------------------------")

    for key, value in payload.items():
        print(
            f"{key}: {value}"
        )

    assert payload["severity"] == "RED"
    assert payload["area"] == "Chennai"
    assert payload["msgType"] == "Alert"

    # ==================================================
    # TEST 6 - DATACLASS SERIALIZATION
    # ==================================================

    assessment_dict = asdict(
        red
    )

    assert (
        assessment_dict["alert_level"]
        == "RED"
    )

    print(
        "\nSTATUS: Flood Risk Classifier test PASSED"
    )