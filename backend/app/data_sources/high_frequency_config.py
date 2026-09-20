"""
RainGuard AI - High-Frequency Data Source Configuration

Central configuration for the SIH26071 multi-source ingestion layer.

IMPORTANT:
- No credentials are stored here.
- No fake/live source URLs are claimed.
- Official source access can be connected later through
  environment variables or dedicated adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DataSourceConfig:
    """Configuration for one RainGuard data source."""

    name: str
    source_type: str
    provider: str

    enabled: bool

    timestep_minutes: int
    native_resolution_km: Optional[float]

    variables: tuple[str, ...]

    access_method: str

    endpoint_env_var: Optional[str] = None
    credentials_env_var: Optional[str] = None

    notes: str = ""


COMMON_TIMESTEP_MINUTES = 30
COMMON_GRID_RESOLUTION_KM = 4.0


DATA_SOURCES = {
    "satellite": DataSourceConfig(
        name="INSAT-3D/3DR",
        source_type="satellite",
        provider="MOSDAC / ISRO",
        enabled=False,
        timestep_minutes=30,
        native_resolution_km=4.0,
        variables=(
            "cloud_top_temperature_k",
            "qpe_mm",
        ),
        access_method="MOSDAC authenticated data access",
        credentials_env_var="MOSDAC_CREDENTIALS",
        notes=(
            "Enable after authorized MOSDAC access is configured."
        ),
    ),

    "radar": DataSourceConfig(
        name="DWR Radar",
        source_type="radar",
        provider="India Meteorological Department",
        enabled=False,
        timestep_minutes=10,
        native_resolution_km=1.0,
        variables=(
            "reflectivity_dbz",
            "rainfall_rate_mm_per_hour",
        ),
        access_method="IMD radar data access",
        credentials_env_var="IMD_RADAR_CREDENTIALS",
        notes=(
            "Native radar cadence is harmonized to the "
            "RainGuard 30-minute common timestep."
        ),
    ),

    "aws": DataSourceConfig(
        name="Automatic Weather Station",
        source_type="aws",
        provider="India Meteorological Department",
        enabled=False,
        timestep_minutes=30,
        native_resolution_km=None,
        variables=(
            "rainfall_mm",
            "temperature_c",
            "relative_humidity",
            "wind_speed_ms",
            "wind_direction_deg",
            "pressure_hpa",
        ),
        access_method="IMD observational data access",
        credentials_env_var="IMD_OBSERVATION_CREDENTIALS",
        notes=(
            "Point observations are mapped to the common grid."
        ),
    ),

    "arg": DataSourceConfig(
        name="Automatic Rain Gauge",
        source_type="arg",
        provider="India Meteorological Department",
        enabled=False,
        timestep_minutes=30,
        native_resolution_km=None,
        variables=(
            "rainfall_mm",
        ),
        access_method="IMD observational data access",
        credentials_env_var="IMD_OBSERVATION_CREDENTIALS",
        notes=(
            "Point rainfall observations are mapped to the "
            "common grid."
        ),
    ),

    "nwp": DataSourceConfig(
        name="Numerical Weather Prediction",
        source_type="nwp",
        provider="IMD / NWP",
        enabled=False,
        timestep_minutes=180,
        native_resolution_km=12.0,
        variables=(
            "precipitation_mm",
            "humidity",
            "wind_speed_ms",
            "pressure_hpa",
        ),
        access_method="Authorized NWP data access",
        credentials_env_var="NWP_CREDENTIALS",
        notes=(
            "Native 3-hourly NWP data is temporally aligned "
            "to the common 30-minute processing axis."
        ),
    ),
}


def get_source(
    source_key: str,
) -> DataSourceConfig:
    """Return one configured data source."""

    if source_key not in DATA_SOURCES:
        raise KeyError(
            f"Unknown data source: {source_key}"
        )

    return DATA_SOURCES[source_key]


def enabled_sources() -> list[DataSourceConfig]:
    """Return sources explicitly enabled by configuration."""

    return [
        source
        for source in DATA_SOURCES.values()
        if source.enabled
    ]


def describe_sources() -> None:
    """Print the current source configuration."""

    print("\nRainGuard High-Frequency Data Sources")
    print("======================================")

    print(
        f"Common timestep: "
        f"{COMMON_TIMESTEP_MINUTES} minutes"
    )

    print(
        f"Common grid: "
        f"{COMMON_GRID_RESOLUTION_KM} km"
    )

    print("\nSources:")

    for key, source in DATA_SOURCES.items():
        print(
            f"\n[{key}]"
        )

        print(
            f"  Name: {source.name}"
        )

        print(
            f"  Provider: {source.provider}"
        )

        print(
            f"  Enabled: {source.enabled}"
        )

        print(
            f"  Native timestep: "
            f"{source.timestep_minutes} minutes"
        )

        print(
            f"  Native resolution: "
            f"{source.native_resolution_km} km"
        )

        print(
            f"  Variables: "
            f"{', '.join(source.variables)}"
        )

        print(
            f"  Access: {source.access_method}"
        )


def validate_configuration() -> list[str]:
    """
    Validate configuration consistency.

    Returns a list of configuration errors.
    """

    errors: list[str] = []

    if COMMON_TIMESTEP_MINUTES <= 0:
        errors.append(
            "Common timestep must be positive."
        )

    if COMMON_GRID_RESOLUTION_KM <= 0:
        errors.append(
            "Common grid resolution must be positive."
        )

    for key, source in DATA_SOURCES.items():

        if not source.name:
            errors.append(
                f"{key}: source name is empty."
            )

        if not source.provider:
            errors.append(
                f"{key}: provider is empty."
            )

        if source.timestep_minutes <= 0:
            errors.append(
                f"{key}: timestep must be positive."
            )

        if not source.variables:
            errors.append(
                f"{key}: no variables configured."
            )

        if (
            source.native_resolution_km is not None
            and source.native_resolution_km <= 0
        ):
            errors.append(
                f"{key}: native resolution must be positive."
            )

    return errors


if __name__ == "__main__":

    describe_sources()

    errors = validate_configuration()

    print("\nConfiguration Validation")
    print("------------------------")

    if errors:
        for error in errors:
            print("ERROR:", error)

        raise SystemExit(1)

    print("Configuration validation PASSED")

    print(
        "\nEnabled sources:",
        len(enabled_sources()),
    )

    print(
        "\nSTATUS: High-frequency configuration test PASSED"
    )