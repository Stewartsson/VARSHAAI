from datetime import datetime

from app.data_sources.schemas.weather_schema import (
    WeatherObservation,
)

from app.data_sources.source_registry import (
    SOURCE_REGISTRY,
)

from app.data_sources.harmonizer import (
    WeatherHarmonizer,
)


def main():

    print("RainGuard Multi-Source Ingestion Test")
    print("--------------------------------------")

    print("\nRegistered sources:")

    for source, config in SOURCE_REGISTRY.items():
        print(
            f"  {source.upper():10s} "
            f"{config['name']:15s} "
            f"status={config['status']}"
        )

    print("\nCreating sample observations...")

    observations = [
        WeatherObservation(
            source="aws",
            timestamp=datetime(
                2026, 9, 11, 20, 17
            ),
            latitude=13.0827,
            longitude=80.2707,
            rainfall_mm=12.4,
            temperature_c=29.1,
            relative_humidity=82.0,
            wind_speed_ms=4.2,
            pressure_hpa=1004.8,
            quality_flag="good",
        ),

        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 21
            ),
            latitude=13.0827,
            longitude=80.2707,
            reflectivity_dbz=38.5,
            rainfall_mm=22.1,
            quality_flag="good",
        ),
    ]

    harmonizer = WeatherHarmonizer(
        grid_resolution_km=4.0,
        timestep_minutes=30,
    )

    harmonized = harmonizer.harmonize(
        observations
    )

    print("\nHarmonized observations:")

    for observation in harmonized:
        print(
            f"  {observation.source:6s} | "
            f"{observation.timestamp} | "
            f"rain={observation.rainfall_mm}"
        )

    print("\nHarmonization configuration:")

    for key, value in harmonizer.describe().items():
        print(f"  {key}: {value}")

    print("\n--------------------------------------")
    print("Multi-source ingestion foundation OK.")


if __name__ == "__main__":
    main()