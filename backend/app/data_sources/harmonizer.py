from typing import Iterable

from app.data_sources.schemas.weather_schema import WeatherObservation


class WeatherHarmonizer:
    """
    Converts observations from different sources into
    RainGuard's common spatial/temporal representation.
    """

    def __init__(
        self,
        grid_resolution_km: float = 4.0,
        timestep_minutes: int = 30,
    ):
        self.grid_resolution_km = grid_resolution_km
        self.timestep_minutes = timestep_minutes

    def harmonize(
        self,
        observations: Iterable[WeatherObservation],
    ) -> list[WeatherObservation]:

        observations = list(observations)

        if not observations:
            return []

        normalized = []

        for observation in observations:
            normalized.append(
                self._normalize_timestamp(observation)
            )

        return normalized

    def _normalize_timestamp(
        self,
        observation: WeatherObservation,
    ) -> WeatherObservation:

        timestamp = observation.timestamp

        minute = (
            timestamp.minute
            - timestamp.minute % self.timestep_minutes
        )

        normalized_timestamp = timestamp.replace(
            minute=minute,
            second=0,
            microsecond=0,
        )

        observation.timestamp = normalized_timestamp

        return observation

    def describe(self) -> dict:
        return {
            "grid_resolution_km": self.grid_resolution_km,
            "timestep_minutes": self.timestep_minutes,
            "spatial_alignment": "common_grid",
            "temporal_alignment": "common_timestep",
        }