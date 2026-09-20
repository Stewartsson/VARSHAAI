from collections import defaultdict
from statistics import mean
from typing import Iterable

from app.data_sources.schemas.weather_schema import WeatherObservation
from app.data_sources.temporal_alignment import TemporalAligner


AGGREGATION_RULES = {
    "rainfall_mm": "sum",
    "temperature_c": "mean",
    "relative_humidity": "mean",
    "wind_speed_ms": "mean",
    "wind_direction_deg": "mean",
    "pressure_hpa": "mean",
    "reflectivity_dbz": "max",
    "cloud_top_temperature_k": "mean",
}


class ObservationAggregator:
    """
    Aggregates multiple observations that fall inside
    the same RainGuard common time window.
    """

    def __init__(self, timestep_minutes: int = 30):
        self.aligner = TemporalAligner(
            timestep_minutes=timestep_minutes
        )

    def aggregate(
        self,
        observations: Iterable[WeatherObservation],
    ) -> list[WeatherObservation]:

        groups = defaultdict(list)

        for observation in observations:

            aligned_time = (
                self.aligner.align_timestamp(
                    observation.timestamp
                )
            )

            key = (
                observation.source,
                aligned_time,
                round(observation.latitude, 6),
                round(observation.longitude, 6),
            )

            groups[key].append(observation)

        aggregated = []

        for (
            source,
            timestamp,
            latitude,
            longitude,
        ), group in groups.items():

            aggregated_observation = (
                self._aggregate_group(
                    source,
                    timestamp,
                    latitude,
                    longitude,
                    group,
                )
            )

            aggregated.append(
                aggregated_observation
            )

        return sorted(
            aggregated,
            key=lambda item: (
                item.timestamp,
                item.source,
                item.latitude,
                item.longitude,
            ),
        )

    def _aggregate_group(
        self,
        source,
        timestamp,
        latitude,
        longitude,
        observations,
    ):

        result = WeatherObservation(
            source=source,
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            quality_flag="aggregated",
        )

        for field_name, rule in AGGREGATION_RULES.items():

            values = []

            for observation in observations:
                value = getattr(
                    observation,
                    field_name,
                )

                if value is not None:
                    values.append(float(value))

            if not values:
                continue

            if rule == "sum":
                value = sum(values)

            elif rule == "mean":
                value = mean(values)

            elif rule == "max":
                value = max(values)

            else:
                raise ValueError(
                    f"Unknown aggregation rule: {rule}"
                )

            setattr(
                result,
                field_name,
                value,
            )

        return result

    def describe(self):
        return {
            "timestep_minutes": (
                self.aligner.timestep_minutes
            ),
            "rules": AGGREGATION_RULES,
        }


if __name__ == "__main__":

    from datetime import datetime

    print("RainGuard Observation Aggregation Test")
    print("--------------------------------------")

    observations = [
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

        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 25
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=3.0,
            reflectivity_dbz=35.0,
        ),
    ]

    aggregator = ObservationAggregator(
        timestep_minutes=30
    )

    result = aggregator.aggregate(
        observations
    )

    print("\nAggregated observations:")

    for observation in result:
        print(
            f"  source={observation.source}"
        )

        print(
            f"  timestamp={observation.timestamp}"
        )

        print(
            f"  rainfall={observation.rainfall_mm} mm"
        )

        print(
            f"  reflectivity="
            f"{observation.reflectivity_dbz} dBZ"
        )

    print("\nAggregation configuration:")

    description = aggregator.describe()

    print(
        f"  timestep: "
        f"{description['timestep_minutes']} minutes"
    )

    for field, rule in description["rules"].items():
        print(
            f"  {field}: {rule}"
        )

    print("\n--------------------------------------")
    print("Observation aggregation test OK.")