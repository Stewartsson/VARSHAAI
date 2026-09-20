from datetime import datetime, timedelta
from typing import Iterable

from app.data_sources.schemas.weather_schema import WeatherObservation


class TemporalAligner:
    """
    Align observations from different weather sources
    onto a common RainGuard time axis.
    """

    def __init__(self, timestep_minutes: int = 30):
        if timestep_minutes <= 0:
            raise ValueError(
                "timestep_minutes must be greater than zero."
            )

        self.timestep_minutes = timestep_minutes

    def align_timestamp(
        self,
        timestamp: datetime,
    ) -> datetime:
        """
        Floor a timestamp to the beginning of the
        corresponding common time window.
        """

        minute = (
            timestamp.minute
            - timestamp.minute % self.timestep_minutes
        )

        return timestamp.replace(
            minute=minute,
            second=0,
            microsecond=0,
        )

    def align_observations(
        self,
        observations: Iterable[WeatherObservation],
    ) -> list[WeatherObservation]:
        """
        Align observation timestamps to the common
        RainGuard time axis.
        """

        aligned = []

        for observation in observations:

            observation.timestamp = (
                self.align_timestamp(
                    observation.timestamp
                )
            )

            aligned.append(observation)

        return aligned

    def create_time_axis(
        self,
        start: datetime,
        end: datetime,
    ) -> list[datetime]:
        """
        Create a continuous common time axis.

        Missing observations can later be detected by
        comparing source timestamps against this axis.
        """

        if start > end:
            raise ValueError(
                "start must be before end."
            )

        start = self.align_timestamp(start)
        end = self.align_timestamp(end)

        step = timedelta(
            minutes=self.timestep_minutes
        )

        timestamps = []

        current = start

        while current <= end:
            timestamps.append(current)
            current += step

        return timestamps

    def find_missing_times(
        self,
        observations: Iterable[WeatherObservation],
        start: datetime,
        end: datetime,
    ) -> list[datetime]:
        """
        Identify missing timestamps for a source.
        """

        expected = set(
            self.create_time_axis(
                start,
                end,
            )
        )

        actual = {
            self.align_timestamp(
                observation.timestamp
            )
            for observation in observations
        }

        return sorted(
            expected - actual
        )

    def describe(self) -> dict:
        return {
            "timestep_minutes": self.timestep_minutes,
            "alignment_method": "floor_to_common_window",
            "time_axis": "continuous",
        }


if __name__ == "__main__":

    print("RainGuard Temporal Alignment Test")
    print("---------------------------------")

    aligner = TemporalAligner(
        timestep_minutes=30
    )

    observations = [
        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 7
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=5.2,
        ),
        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 22
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=8.4,
        ),
        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 21, 4
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=12.1,
        ),
    ]

    aligned = aligner.align_observations(
        observations
    )

    print("\nAligned observations:")

    for observation in aligned:
        print(
            f"  {observation.source:6s} | "
            f"{observation.timestamp} | "
            f"rain={observation.rainfall_mm}"
        )

    print("\nCreating continuous time axis:")

    time_axis = aligner.create_time_axis(
        start=datetime(
            2026, 9, 11, 20, 0
        ),
        end=datetime(
            2026, 9, 11, 22, 0
        ),
    )

    for timestamp in time_axis:
        print(f"  {timestamp}")

    print("\nChecking missing timestamps:")

    missing = aligner.find_missing_times(
        aligned,
        start=datetime(
            2026, 9, 11, 20, 0
        ),
        end=datetime(
            2026, 9, 11, 22, 0
        ),
    )

    for timestamp in missing:
        print(f"  MISSING: {timestamp}")

    print("\nConfiguration:")

    for key, value in aligner.describe().items():
        print(f"  {key}: {value}")

    print("\n---------------------------------")
    print("Temporal alignment test OK.")