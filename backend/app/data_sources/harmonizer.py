from typing import Iterable
import numpy as np

from app.data_sources.schemas.weather_schema import WeatherObservation
from app.data_sources.spatial_interpolator import inverse_distance_weighting

class WeatherHarmonizer:
    """
    Converts observations from different sources into
    RainGuard's common spatial/temporal representation.
    """

    def __init__(
        self,
        grid_resolution_km: float = 4.0,
        timestep_minutes: int = 30,
        grid_bounds: tuple[float, float, float, float] = (79.0, 81.0, 12.0, 14.0),
        grid_size: int = 50
    ):
        self.grid_resolution_km = grid_resolution_km
        self.timestep_minutes = timestep_minutes
        self.grid_bounds = grid_bounds
        self.grid_size = grid_size
        
        # Create the common grid (e.g. over Chennai region)
        min_lon, max_lon, min_lat, max_lat = grid_bounds
        self.grid_lon, self.grid_lat = np.meshgrid(
            np.linspace(min_lon, max_lon, grid_size),
            np.linspace(min_lat, max_lat, grid_size)
        )

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
        
    def harmonize_spatial(self, lons: np.ndarray, lats: np.ndarray, values: np.ndarray) -> np.ndarray:
        """
        Re-grid point observations or different resolution grids to the common grid.
        Uses IDW for spatial interpolation.
        """
        return inverse_distance_weighting(
            lons, lats, values, 
            self.grid_lon, self.grid_lat
        )

    def describe(self) -> dict:
        return {
            "grid_resolution_km": self.grid_resolution_km,
            "timestep_minutes": self.timestep_minutes,
            "spatial_alignment": "common_grid",
            "temporal_alignment": "common_timestep",
            "grid_bounds": self.grid_bounds,
            "grid_size": f"{self.grid_size}x{self.grid_size}"
        }