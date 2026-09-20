from collections import defaultdict
from typing import Iterable

import numpy as np

from app.data_sources.schemas.weather_schema import (
    WeatherObservation,
)
from app.data_sources.spatial_grid import (
    CommonGrid,
    nearest_grid_cell,
)
from app.data_sources.preprocessing_pipeline import (
    RainGuardPreprocessingPipeline,
)


class RainGuardDataFusion:
    """
    Combines preprocessed observations from multiple
    weather sources onto the RainGuard common grid.

    Current supported sources:
        - INSAT satellite
        - DWR radar
        - AWS
        - ARG
        - NWP

    The output is a common-grid representation that can
    later be converted into ML tensors.
    """

    def __init__(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        resolution_deg: float = 0.04,
        timestep_minutes: int = 30,
    ):

        self.grid = CommonGrid(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            resolution_deg=resolution_deg,
        )

        self.preprocessing = (
            RainGuardPreprocessingPipeline(
                timestep_minutes=timestep_minutes
            )
        )

    def process(
        self,
        observations: Iterable[WeatherObservation],
    ) -> dict:

        observations = list(observations)

        if not observations:
            return {
                "grid": self.grid,
                "timestamps": [],
                "sources": {},
            }

        processed = self.preprocessing.process(
            observations
        )

        timestamps = sorted(
            {
                observation.timestamp
                for observation in processed
            }
        )

        source_names = sorted(
            {
                observation.source
                for observation in processed
            }
        )

        source_fields = {}

        for source in source_names:

            source_fields[source] = (
                self._create_source_fields(
                    processed,
                    source,
                    timestamps,
                )
            )

        return {
            "grid": self.grid,
            "timestamps": timestamps,
            "sources": source_fields,
        }

    def _create_source_fields(
        self,
        observations,
        source,
        timestamps,
    ):

        fields = {}

        source_observations = [
            observation
            for observation in observations
            if observation.source == source
        ]

        for timestamp in timestamps:

            field = np.full(
                self.grid.shape,
                np.nan,
                dtype=float,
            )

            timestamp_observations = [
                observation
                for observation
                in source_observations
                if observation.timestamp == timestamp
            ]

            for observation in timestamp_observations:

                cell = nearest_grid_cell(
                    observation.latitude,
                    observation.longitude,
                    self.grid,
                )

                row = cell["row"]
                column = cell["column"]

                if observation.rainfall_mm is not None:

                    field[row, column] = (
                        observation.rainfall_mm
                    )

            fields[timestamp] = field

        return fields

    def describe(self):

        return {
            "grid": self.grid.describe(),
            "preprocessing": (
                self.preprocessing.describe()
            ),
        }


if __name__ == "__main__":

    from datetime import datetime

    print("RainGuard Multi-Source Data Fusion Test")
    print("---------------------------------------")

    observations = [

        WeatherObservation(
            source="aws",
            timestamp=datetime(
                2026, 9, 11, 20, 5
            ),
            latitude=13.0827,
            longitude=80.2707,
            rainfall_mm=12.0,
            temperature_c=29.2,
            relative_humidity=82.0,
            pressure_hpa=1004.5,
        ),

        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 10
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=5.0,
            reflectivity_dbz=35.0,
        ),

        WeatherObservation(
            source="radar",
            timestamp=datetime(
                2026, 9, 11, 20, 20
            ),
            latitude=13.08,
            longitude=80.27,
            rainfall_mm=7.0,
            reflectivity_dbz=40.0,
        ),
    ]

    fusion = RainGuardDataFusion(
        min_lat=12.0,
        max_lat=14.0,
        min_lon=79.0,
        max_lon=81.0,
        resolution_deg=0.04,
        timestep_minutes=30,
    )

    result = fusion.process(
        observations
    )

    print("\nGrid:")
    print(
        f"  Shape: "
        f"{result['grid'].shape}"
    )

    print(
        f"  Resolution: "
        f"{result['grid'].resolution_deg} degrees"
    )

    print("\nTimestamps:")

    for timestamp in result["timestamps"]:
        print(
            f"  {timestamp}"
        )

    print("\nSources:")

    for source, fields in (
        result["sources"].items()
    ):

        print(
            f"  {source}: "
            f"{len(fields)} time field(s)"
        )

        for timestamp, field in fields.items():

            valid = np.isfinite(field)

            print(
                f"    {timestamp} → "
                f"valid_cells={int(valid.sum())}"
            )

            if valid.any():
                print(
                    f"      rainfall_min="
                    f"{np.nanmin(field):.2f} mm"
                )

                print(
                    f"      rainfall_max="
                    f"{np.nanmax(field):.2f} mm"
                )

    print("\n---------------------------------------")
    print("Multi-source data fusion test OK.")