import numpy as np

from app.data_sources.spatial_grid import CommonGrid
from app.data_sources.regridder import bilinear_regrid


class GriddedFieldFusion:
    """
    Regrids a gridded weather field onto the RainGuard
    common spatial grid.

    Intended for:
        - DWR radar fields
        - INSAT satellite products
        - NWP model fields
    """

    def __init__(self, target_grid: CommonGrid):
        self.target_grid = target_grid

    def regrid(
        self,
        source_latitudes,
        source_longitudes,
        source_values,
    ):
        """
        Regrid one 2D source field onto the common grid.
        """

        source_values = np.asarray(
            source_values,
            dtype=float,
        )

        return bilinear_regrid(
            source_latitudes=source_latitudes,
            source_longitudes=source_longitudes,
            source_values=source_values,
            target_grid=self.target_grid,
        )

    def validate_field(
        self,
        field,
    ):
        """
        Basic validation of a regridded field.
        """

        field = np.asarray(
            field,
            dtype=float,
        )

        if field.shape != self.target_grid.shape:
            raise ValueError(
                "Field shape does not match "
                "the RainGuard common grid."
            )

        valid = np.isfinite(field)

        return {
            "shape": field.shape,
            "valid_cells": int(valid.sum()),
            "missing_cells": int((~valid).sum()),
            "minimum": (
                float(np.nanmin(field))
                if valid.any()
                else None
            ),
            "maximum": (
                float(np.nanmax(field))
                if valid.any()
                else None
            ),
        }

    def describe(self):
        return {
            "target_grid_shape": self.target_grid.shape,
            "target_resolution_deg": (
                self.target_grid.resolution_deg
            ),
            "method": "bilinear_interpolation",
        }


if __name__ == "__main__":

    print("RainGuard Gridded Field Fusion Test")
    print("-----------------------------------")

    # Synthetic source grid representing a
    # higher-resolution radar-like field.
    source_latitudes = np.array([
        12.0,
        12.2,
        12.4,
        12.6,
        12.8,
        13.0,
        13.2,
        13.4,
        13.6,
        13.8,
        14.0,
    ])

    source_longitudes = np.array([
        79.0,
        79.2,
        79.4,
        79.6,
        79.8,
        80.0,
        80.2,
        80.4,
        80.6,
        80.8,
        81.0,
    ])

    # Create a synthetic rainfall field.
    source_values = np.zeros(
        (
            len(source_latitudes),
            len(source_longitudes),
        ),
        dtype=float,
    )

    for i in range(
        len(source_latitudes)
    ):
        for j in range(
            len(source_longitudes)
        ):

            distance = (
                (
                    source_latitudes[i]
                    - 13.08
                ) ** 2
                +
                (
                    source_longitudes[j]
                    - 80.27
                ) ** 2
            )

            source_values[i, j] = (
                200.0
                * np.exp(
                    -distance / 0.03
                )
            )

    target_grid = CommonGrid(
        min_lat=12.0,
        max_lat=14.0,
        min_lon=79.0,
        max_lon=81.0,
        resolution_deg=0.04,
    )

    fusion = GriddedFieldFusion(
        target_grid
    )

    print("\nSource field:")
    print(
        f"  Shape: "
        f"{source_values.shape}"
    )

    print("\nTarget grid:")
    print(
        f"  Shape: "
        f"{target_grid.shape}"
    )

    print(
        f"  Resolution: "
        f"{target_grid.resolution_deg} degrees"
    )

    print("\nRegridding field...")

    result = fusion.regrid(
        source_latitudes,
        source_longitudes,
        source_values,
    )

    statistics = fusion.validate_field(
        result
    )

    print("\nRegridded field:")

    for key, value in statistics.items():
        print(
            f"  {key}: {value}"
        )

    print("\nConfiguration:")

    for key, value in fusion.describe().items():
        print(
            f"  {key}: {value}"
        )

    print("\n-----------------------------------")
    print("Gridded field fusion test OK.")