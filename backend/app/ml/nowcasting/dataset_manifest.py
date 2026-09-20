"""
RainGuard AI - High-Frequency Dataset Manifest

Defines the metadata required for a dataset to enter the
0–3 hour nowcasting pipeline.

This does not download or fabricate data.
It only describes and validates the expected dataset contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


EXPECTED_FEATURES = [
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


@dataclass
class DatasetManifest:
    """Metadata describing one nowcasting dataset."""

    dataset_name: str
    source_type: str
    region: str

    start_time: str
    end_time: str

    timestep_minutes: int

    grid_resolution_km: float
    latitude_points: int
    longitude_points: int

    feature_names: list[str]

    target_variable: str

    missing_value_policy: str
    spatial_regridding: str
    temporal_alignment: str

    notes: str = ""

    def validate(self) -> list[str]:
        """Validate the dataset contract."""

        errors: list[str] = []

        if self.timestep_minutes != 30:
            errors.append(
                "Nowcasting dataset must use a "
                "30-minute common timestep."
            )

        if self.grid_resolution_km <= 0:
            errors.append(
                "Grid resolution must be positive."
            )

        if self.latitude_points < 2:
            errors.append(
                "At least 2 latitude grid points are required."
            )

        if self.longitude_points < 2:
            errors.append(
                "At least 2 longitude grid points are required."
            )

        if not self.feature_names:
            errors.append(
                "At least one feature is required."
            )

        if self.target_variable not in self.feature_names:
            errors.append(
                "Target variable must exist in feature_names."
            )

        return errors

    def to_dict(self) -> dict:
        """Convert manifest to a JSON-compatible dictionary."""

        return asdict(self)

    def save(self, path: str | Path) -> None:
        """Save manifest as JSON."""

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.to_dict(),
                file,
                indent=2,
            )


def build_rainguard_manifest() -> DatasetManifest:
    """
    Build the standard RainGuard high-frequency
    nowcasting dataset manifest.
    """

    return DatasetManifest(
        dataset_name="RainGuard High-Frequency Nowcasting Dataset",
        source_type="DWR + INSAT + AWS + ARG + NWP",
        region="Configurable IMD region",

        start_time="YYYY-MM-DDTHH:MM:SS+05:30",
        end_time="YYYY-MM-DDTHH:MM:SS+05:30",

        timestep_minutes=30,

        grid_resolution_km=4.0,
        latitude_points=51,
        longitude_points=52,

        feature_names=EXPECTED_FEATURES.copy(),

        target_variable="radar_rainfall_mm",

        missing_value_policy=(
            "Preserve source missingness during ingestion; "
            "apply source-specific QC and controlled gap handling."
        ),

        spatial_regridding=(
            "Regrid gridded fields to the common 4-km grid; "
            "map point observations to the nearest common-grid cell."
        ),

        temporal_alignment=(
            "Align source observations to common 30-minute "
            "time windows using source-appropriate aggregation."
        ),

        notes=(
            "Dataset must contain genuine time-resolved "
            "observations. Daily rainfall datasets are not "
            "eligible for 30-minute ConvLSTM nowcasting."
        ),
    )


if __name__ == "__main__":

    manifest = build_rainguard_manifest()

    print("\nRainGuard Dataset Manifest")
    print("==========================")

    print(
        "Dataset:",
        manifest.dataset_name,
    )

    print(
        "Sources:",
        manifest.source_type,
    )

    print(
        "Timestep:",
        f"{manifest.timestep_minutes} minutes",
    )

    print(
        "Grid:",
        f"{manifest.grid_resolution_km} km",
    )

    print(
        "Dimensions:",
        f"{manifest.latitude_points} × "
        f"{manifest.longitude_points}",
    )

    print("\nFeatures:")
    for index, feature in enumerate(
        manifest.feature_names,
        start=1,
    ):
        print(
            f"  {index:02d}. {feature}"
        )

    print(
        "\nTarget:",
        manifest.target_variable,
    )

    errors = manifest.validate()

    print("\nValidation")
    print("----------")

    if errors:
        for error in errors:
            print("ERROR:", error)

        raise SystemExit(1)

    print("Manifest validation PASSED")

    output_path = (
        Path("data")
        / "nowcasting"
        / "rainguard_dataset_manifest.json"
    )

    manifest.save(output_path)

    print(
        "Manifest saved:",
        output_path,
    )

    print(
        "\nSTATUS: Dataset manifest test PASSED"
    )