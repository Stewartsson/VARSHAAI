from typing import Iterable

from app.data_sources.schemas.weather_schema import (
    WeatherObservation,
)

from app.data_sources.quality_control import (
    WeatherQualityController,
)

from app.data_sources.temporal_alignment import (
    TemporalAligner,
)

from app.data_sources.aggregation import (
    ObservationAggregator,
)


class RainGuardPreprocessingPipeline:
    """
    End-to-end preprocessing pipeline for RainGuard.

    Processing order:

        Raw observations
            ↓
        Quality Control
            ↓
        Temporal Alignment
            ↓
        Source-specific Aggregation
            ↓
        ML-ready observations
    """

    def __init__(
        self,
        timestep_minutes: int = 30,
    ):

        self.quality_controller = (
            WeatherQualityController()
        )

        self.temporal_aligner = (
            TemporalAligner(
                timestep_minutes=timestep_minutes
            )
        )

        self.aggregator = (
            ObservationAggregator(
                timestep_minutes=timestep_minutes
            )
        )

    def process(
        self,
        observations: Iterable[WeatherObservation],
    ) -> list[WeatherObservation]:

        observations = list(observations)

        if not observations:
            return []

        # ---------------------------------
        # 1. Quality control
        # ---------------------------------

        quality_checked = (
            self.quality_controller.validate(
                observations
            )
        )

        # Keep valid observations for the
        # ML-ready stream.
        valid_observations = [
            observation
            for observation in quality_checked
            if observation.quality_flag == "good"
        ]

        # ---------------------------------
        # 2. Temporal alignment
        # ---------------------------------

        aligned = (
            self.temporal_aligner.align_observations(
                valid_observations
            )
        )

        # ---------------------------------
        # 3. Source-specific aggregation
        # ---------------------------------

        aggregated = (
            self.aggregator.aggregate(
                aligned
            )
        )

        return aggregated

    def describe(self) -> dict:

        return {
            "steps": [
                "quality_control",
                "temporal_alignment",
                "source_specific_aggregation",
            ],
            "timestep_minutes": (
                self.temporal_aligner.timestep_minutes
            ),
        }


if __name__ == "__main__":

    from datetime import datetime

    print(
        "RainGuard End-to-End "
        "Preprocessing Pipeline Test"
    )

    print(
        "--------------------------------------"
    )

    observations = [

        # Valid radar observation
        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 5
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=5.0,
            reflectivity_dbz=32.0,
        ),

        # Another valid radar observation
        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 15
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=7.0,
            reflectivity_dbz=38.0,
        ),

        # Invalid observation.
        # This should be removed by QC.
        WeatherObservation(
            source="aws",
            timestamp=datetime(
                2026, 9, 11, 20, 20
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=-10.0,
        ),
    ]

    pipeline = (
        RainGuardPreprocessingPipeline(
            timestep_minutes=30
        )
    )

    result = pipeline.process(
        observations
    )

    print("\nInput observations:")
    print(f"  {len(observations)}")

    print("\nOutput observations:")
    print(f"  {len(result)}")

    for observation in result:

        print(
            f"\n  Source       : "
            f"{observation.source}"
        )

        print(
            f"  Timestamp    : "
            f"{observation.timestamp}"
        )

        print(
            f"  Rainfall     : "
            f"{observation.rainfall_mm} mm"
        )

        print(
            f"  Reflectivity : "
            f"{observation.reflectivity_dbz}"
        )

        print(
            f"  Quality      : "
            f"{observation.quality_flag}"
        )

    print("\nPipeline configuration:")

    for key, value in (
        pipeline.describe().items()
    ):
        print(
            f"  {key}: {value}"
        )

    print(
        "\n--------------------------------------"
    )

    print(
        "Preprocessing pipeline test OK."
    )