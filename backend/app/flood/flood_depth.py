"""
RainGuard AI - Simplified Flood Depth Engine

Purpose:
    Convert rainfall-runoff depth into an estimated
    spatial flood-depth raster and flooded-area mask.

This is a simplified screening-level inundation model.
It is NOT a replacement for a calibrated HEC-RAS,
LISFLOOD, or other full hydraulic model.

Concept:

    Runoff depth
         +
    DEM / terrain
         +
    Drainage adjustment
         ↓
    Estimated flood depth
         ↓
    Flood extent mask
"""

from __future__ import annotations

import numpy as np


class FloodDepthModel:
    """
    Simplified spatial flood-depth estimator.

    The model represents:
        1. Runoff accumulation
        2. Terrain influence
        3. Drainage capacity

    All raster inputs must have identical spatial shapes.
    """

    def __init__(
        self,
        drainage_factor: float = 0.15,
        terrain_factor: float = 0.05,
        minimum_flood_depth_mm: float = 10.0,
    ):
        if not 0.0 <= drainage_factor <= 1.0:
            raise ValueError(
                "drainage_factor must be between 0 and 1."
            )

        if terrain_factor < 0:
            raise ValueError(
                "terrain_factor cannot be negative."
            )

        if minimum_flood_depth_mm < 0:
            raise ValueError(
                "minimum_flood_depth_mm cannot be negative."
            )

        self.drainage_factor = drainage_factor
        self.terrain_factor = terrain_factor
        self.minimum_flood_depth_mm = (
            minimum_flood_depth_mm
        )

    @staticmethod
    def _validate_raster(
        raster: np.ndarray | list,
        name: str,
    ) -> np.ndarray:
        """
        Convert a raster to float32 and validate it.
        """

        array = np.asarray(
            raster,
            dtype=np.float32,
        )

        if array.ndim != 2:
            raise ValueError(
                f"{name} must be a 2D raster."
            )

        return array

    @staticmethod
    def _validate_same_shape(
        *rasters: tuple[str, np.ndarray],
    ) -> None:
        """
        Ensure all rasters have the same spatial shape.
        """

        shapes = {
            name: raster.shape
            for name, raster in rasters
        }

        unique_shapes = set(
            shapes.values()
        )

        if len(unique_shapes) != 1:
            raise ValueError(
                "All rasters must have identical "
                f"spatial shapes. Received: {shapes}"
            )

    def terrain_normalized(
        self,
        dem: np.ndarray,
    ) -> np.ndarray:
        """
        Normalize DEM between 0 and 1.

        Lower terrain receives a larger inundation
        contribution than higher terrain.

        Returns:
            terrain_low_factor in range [0, 1]
        """

        dem_array = self._validate_raster(
            dem,
            "DEM",
        )

        finite = np.isfinite(
            dem_array
        )

        if not np.any(finite):
            raise ValueError(
                "DEM contains no valid values."
            )

        dem_min = np.nanmin(
            dem_array
        )

        dem_max = np.nanmax(
            dem_array
        )

        if dem_max == dem_min:
            return np.zeros_like(
                dem_array,
                dtype=np.float32,
            )

        normalized = (
            dem_array - dem_min
        ) / (
            dem_max - dem_min
        )

        # Invert elevation:
        # low elevation -> high inundation factor
        low_terrain = 1.0 - normalized

        low_terrain[
            ~finite
        ] = np.nan

        return np.clip(
            low_terrain,
            0.0,
            1.0,
        )

    def estimate_depth(
        self,
        runoff_mm: np.ndarray,
        dem: np.ndarray,
        drainage_capacity_mm: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Estimate flood depth in millimetres.

        Parameters
        ----------
        runoff_mm:
            Direct runoff depth.

        dem:
            Digital Elevation Model.

        drainage_capacity_mm:
            Optional spatial drainage capacity.
            Higher values represent areas capable of
            removing more water.

        Returns
        -------
        np.ndarray
            Estimated flood depth in millimetres.

        Simplified formulation:

            effective_runoff =
                runoff × (1 - drainage_factor)

            terrain_effect =
                1 + terrain_factor × low_terrain

            flood_depth =
                effective_runoff × terrain_effect

        If drainage_capacity_mm is supplied:

            flood_depth =
                max(
                    flood_depth - drainage_capacity,
                    0
                )
        """

        runoff = self._validate_raster(
            runoff_mm,
            "runoff_mm",
        )

        dem_array = self._validate_raster(
            dem,
            "DEM",
        )

        self._validate_same_shape(
            ("runoff_mm", runoff),
            ("DEM", dem_array),
        )

        if np.any(
            np.isfinite(runoff)
            & (runoff < 0)
        ):
            raise ValueError(
                "Runoff cannot contain negative values."
            )

        low_terrain = (
            self.terrain_normalized(
                dem_array
            )
        )

        effective_runoff = (
            runoff
            * (
                1.0
                - self.drainage_factor
            )
        )

        terrain_effect = (
            1.0
            + (
                self.terrain_factor
                * low_terrain
            )
        )

        flood_depth = (
            effective_runoff
            * terrain_effect
        )

        if drainage_capacity_mm is not None:

            drainage = self._validate_raster(
                drainage_capacity_mm,
                "drainage_capacity_mm",
            )

            self._validate_same_shape(
                ("runoff_mm", runoff),
                ("DEM", dem_array),
                (
                    "drainage_capacity_mm",
                    drainage,
                ),
            )

            if np.any(
                np.isfinite(drainage)
                & (drainage < 0)
            ):
                raise ValueError(
                    "Drainage capacity cannot "
                    "contain negative values."
                )

            flood_depth = np.maximum(
                flood_depth - drainage,
                0.0,
            )

        invalid = (
            ~np.isfinite(runoff)
            | ~np.isfinite(dem_array)
        )

        flood_depth[
            invalid
        ] = np.nan

        return np.maximum(
            flood_depth,
            0.0,
        )

    def flood_extent(
        self,
        flood_depth_mm: np.ndarray,
    ) -> np.ndarray:
        """
        Convert flood depth into a binary
        inundation mask.

        1 = flooded
        0 = not flooded

        Pixels below the configured minimum
        depth threshold are considered not flooded.
        """

        depth = self._validate_raster(
            flood_depth_mm,
            "flood_depth_mm",
        )

        extent = np.zeros(
            depth.shape,
            dtype=np.uint8,
        )

        flooded = (
            np.isfinite(depth)
            & (
                depth
                >= self.minimum_flood_depth_mm
            )
        )

        extent[flooded] = 1

        return extent

    def depth_meters(
        self,
        flood_depth_mm: np.ndarray,
    ) -> np.ndarray:
        """
        Convert flood depth from millimetres
        to metres.
        """

        depth = self._validate_raster(
            flood_depth_mm,
            "flood_depth_mm",
        )

        return depth / 1000.0


if __name__ == "__main__":

    print("\nRainGuard Flood Depth Model")
    print("===========================")

    model = FloodDepthModel(
        drainage_factor=0.15,
        terrain_factor=0.05,
        minimum_flood_depth_mm=10.0,
    )

    # --------------------------------------------------
    # Test 1: Synthetic runoff + DEM
    # --------------------------------------------------

    runoff = np.array(
        [
            [5.0, 20.0, 50.0],
            [30.0, 100.0, 200.0],
            [10.0, 75.0, 150.0],
        ],
        dtype=np.float32,
    )

    dem = np.array(
        [
            [8.0, 10.0, 12.0],
            [6.0, 7.0, 11.0],
            [4.0, 5.0, 9.0],
        ],
        dtype=np.float32,
    )

    flood_depth = model.estimate_depth(
        runoff,
        dem,
    )

    print("\nFlood depth test")
    print("----------------")
    print(
        "Runoff shape:",
        runoff.shape,
    )

    print(
        "DEM shape:",
        dem.shape,
    )

    print(
        "Flood depth shape:",
        flood_depth.shape,
    )

    print(
        "Minimum depth:",
        f"{np.nanmin(flood_depth):.2f}",
        "mm",
    )

    print(
        "Maximum depth:",
        f"{np.nanmax(flood_depth):.2f}",
        "mm",
    )

    assert flood_depth.shape == (
        3,
        3,
    )

    assert np.all(
        flood_depth >= 0
    )

    # --------------------------------------------------
    # Test 2: Flood extent
    # --------------------------------------------------

    extent = model.flood_extent(
        flood_depth
    )

    print("\nFlood extent")
    print("------------")
    print(extent)

    assert extent.shape == (
        3,
        3,
    )

    assert extent.dtype == np.uint8

    assert np.all(
        np.isin(
            extent,
            [0, 1],
        )
    )

    flooded_pixels = int(
        np.sum(extent)
    )

    print(
        "Flooded pixels:",
        flooded_pixels,
    )

    # --------------------------------------------------
    # Test 3: Metres conversion
    # --------------------------------------------------

    depth_m = model.depth_meters(
        flood_depth
    )

    print("\nDepth conversion")
    print("----------------")
    print(
        "Maximum depth:",
        f"{np.nanmax(depth_m):.3f}",
        "m",
    )

    assert np.allclose(
        depth_m * 1000.0,
        flood_depth,
    )

    # --------------------------------------------------
    # Test 4: Drainage capacity
    # --------------------------------------------------

    drainage = np.full(
        runoff.shape,
        20.0,
        dtype=np.float32,
    )

    drained_depth = (
        model.estimate_depth(
            runoff,
            dem,
            drainage_capacity_mm=drainage,
        )
    )

    print("\nDrainage test")
    print("-------------")
    print(
        "Maximum depth after drainage:",
        f"{np.nanmax(drained_depth):.2f}",
        "mm",
    )

    assert np.all(
        drained_depth
        <= flood_depth + 1e-6
    )

    print(
        "\nSTATUS: Flood Depth Model test PASSED"
    )