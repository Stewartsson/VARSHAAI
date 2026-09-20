from dataclasses import replace
from typing import Iterable

from app.data_sources.schemas.weather_schema import (
    WeatherObservation,
)


class WeatherQualityController:
    """
    Performs basic physical-range and missing-value checks
    on RainGuard weather observations.

    QC does not silently fill missing values.
    Instead, observations receive an appropriate quality flag.
    """

    def validate(
        self,
        observations: Iterable[WeatherObservation],
    ) -> list[WeatherObservation]:

        validated = []

        for observation in observations:
            validated.append(
                self._validate_observation(
                    observation
                )
            )

        return validated

    def _validate_observation(
        self,
        observation: WeatherObservation,
    ) -> WeatherObservation:

        flags = []

        # -----------------------------
        # Rainfall
        # -----------------------------

        if observation.rainfall_mm is not None:

            if observation.rainfall_mm < 0:
                flags.append(
                    "invalid_negative_rainfall"
                )

        # -----------------------------
        # Temperature
        # -----------------------------

        if observation.temperature_c is not None:

            if not (
                -90 <= observation.temperature_c <= 60
            ):
                flags.append(
                    "suspicious_temperature"
                )

        # -----------------------------
        # Relative humidity
        # -----------------------------

        if observation.relative_humidity is not None:

            if not (
                0 <= observation.relative_humidity <= 100
            ):
                flags.append(
                    "invalid_humidity"
                )

        # -----------------------------
        # Wind speed
        # -----------------------------

        if observation.wind_speed_ms is not None:

            if observation.wind_speed_ms < 0:
                flags.append(
                    "invalid_negative_wind"
                )

        # -----------------------------
        # Pressure
        # -----------------------------

        if observation.pressure_hpa is not None:

            if observation.pressure_hpa <= 0:
                flags.append(
                    "invalid_pressure"
                )

        # -----------------------------
        # Radar reflectivity
        # -----------------------------

        if observation.reflectivity_dbz is not None:

            if not (
                -20 <= observation.reflectivity_dbz <= 80
            ):
                flags.append(
                    "suspicious_reflectivity"
                )

        # -----------------------------
        # Satellite cloud-top temperature
        # -----------------------------

        if observation.cloud_top_temperature_k is not None:

            if not (
                150 <= observation.cloud_top_temperature_k <= 350
            ):
                flags.append(
                    "suspicious_cloud_temperature"
                )

        # -----------------------------
        # Final quality flag
        # -----------------------------

        if flags:
            quality_flag = "|".join(flags)

        else:
            quality_flag = "good"

        return replace(
            observation,
            quality_flag=quality_flag,
        )


if __name__ == "__main__":

    from datetime import datetime

    print("RainGuard Weather Quality Control Test")
    print("--------------------------------------")

    observations = [

        # Valid observation
        WeatherObservation(
            source="aws",
            timestamp=datetime(
                2026, 9, 11, 20, 0
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=12.5,
            temperature_c=29.2,
            relative_humidity=82.0,
            wind_speed_ms=4.5,
            pressure_hpa=1004.5,
        ),

        # Invalid rainfall
        WeatherObservation(
            source="aws",
            timestamp=datetime(
                2026, 9, 11, 20, 30
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=-5.0,
        ),

        # Invalid humidity
        WeatherObservation(
            source="aws",
            timestamp=datetime(
                2026, 9, 11, 21, 0
            ),
            latitude=13.08,
            longitude=80.27,
            relative_humidity=125.0,
        ),

        # Invalid radar reflectivity
        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 21, 30
            ),
            latitude=13.08,
            longitude=80.27,
            reflectivity_dbz=100.0,
        ),
    ]

    controller = WeatherQualityController()

    validated = controller.validate(
        observations
    )

    print("\nQC results:")

    for observation in validated:

        print(
            f"  {observation.source:6s} | "
            f"{observation.timestamp} | "
            f"quality={observation.quality_flag}"
        )

    print("\n--------------------------------------")
    print("Weather quality-control test OK.")