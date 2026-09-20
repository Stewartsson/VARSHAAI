"""
RainGuard AI - End-to-End Flood Pipeline

Pipeline:

    Rainfall forecast
          ↓
    LULC → Curve Number
          ↓
    SCS-CN runoff
          ↓
    Flood depth
          ↓
    Inundation extent
          ↓
    Risk classification

This is a prototype screening-level flood model.
It is not a replacement for a calibrated hydraulic
model such as HEC-RAS or LISFLOOD.
"""

from __future__ import annotations

import numpy as np

from app.flood.runoff_model import SCSCNRunoffModel
from app.flood.curve_number_mapper import CurveNumberMapper
from app.flood.flood_depth import FloodDepthModel
from app.flood.inundation_map import InundationMapBuilder


class RainGuardFloodPipeline:
    """
    Connects all flood-model components into one pipeline.
    """

    def __init__(
        self,
        runoff_model: SCSCNRunoffModel | None = None,
        cn_mapper: CurveNumberMapper | None = None,
        depth_model: FloodDepthModel | None = None,
        inundation_builder: InundationMapBuilder | None = None,
    ):
        self.runoff_model = (
            runoff_model
            if runoff_model is not None
            else SCSCNRunoffModel()
        )

        self.cn_mapper = (
            cn_mapper
            if cn_mapper is not None
            else CurveNumberMapper()
        )

        self.depth_model = (
            depth_model
            if depth_model is not None
            else FloodDepthModel()
        )

        self.inundation_builder = (
            inundation_builder
            if inundation_builder is not None
            else InundationMapBuilder()
        )

    @staticmethod
    def _validate_raster(
        raster: np.ndarray | list,
        name: str,
    ) -> np.ndarray:
        """
        Validate a spatial raster.
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
        Ensure all input rasters have the same shape.
        """

        shapes = {
            name: raster.shape
            for name, raster in rasters
        }

        if len(set(shapes.values())) != 1:
            raise ValueError(
                "All rasters must have the same shape. "
                f"Received: {shapes}"
            )

    def run(
        self,
        rainfall_mm: np.ndarray,
        lulc: np.ndarray,
        dem: np.ndarray,
        drainage_capacity_mm: np.ndarray | None = None,
        lulc_nodata: int | float | None = None,
    ) -> dict:
        """
        Execute the complete flood pipeline.

        Parameters
        ----------
        rainfall_mm:
            Forecast/observed rainfall raster in mm.

        lulc:
            LULC class raster.

        dem:
            Digital Elevation Model in metres.

        drainage_capacity_mm:
            Optional drainage capacity raster in mm.

        lulc_nodata:
            Optional NoData value in the LULC raster.

        Returns
        -------
        dict
            Complete flood-model product.
        """

        rainfall = self._validate_raster(
            rainfall_mm,
            "rainfall_mm",
        )

        lulc_array = np.asarray(
            lulc
        )

        dem_array = self._validate_raster(
            dem,
            "dem",
        )

        self._validate_same_shape(
            ("rainfall_mm", rainfall),
            ("LULC", lulc_array),
            ("DEM", dem_array),
        )

        if drainage_capacity_mm is not None:
            drainage = self._validate_raster(
                drainage_capacity_mm,
                "drainage_capacity_mm",
            )

            self._validate_same_shape(
                ("rainfall_mm", rainfall),
                ("LULC", lulc_array),
                ("DEM", dem_array),
                (
                    "drainage_capacity_mm",
                    drainage,
                ),
            )
        else:
            drainage = None

        # --------------------------------------------------
        # Step 1: LULC → Curve Number
        # --------------------------------------------------

        curve_number = (
            self.cn_mapper.map_lulc_to_cn(
                lulc_array,
                nodata_value=lulc_nodata,
            )
        )

        # --------------------------------------------------
        # Step 2: Rainfall → Runoff
        # --------------------------------------------------

        runoff = (
            self.runoff_model.runoff_depth(
                rainfall,
                curve_number,
            )
        )

        # --------------------------------------------------
        # Step 3: Runoff → Flood Depth
        # --------------------------------------------------

        flood_depth_mm = (
            self.depth_model.estimate_depth(
                runoff,
                dem_array,
                drainage_capacity_mm=drainage,
            )
        )

        # --------------------------------------------------
        # Step 4: Convert mm → metres
        # --------------------------------------------------

        flood_depth_m = (
            self.depth_model.depth_meters(
                flood_depth_mm
            )
        )

        # --------------------------------------------------
        # Step 5: Build inundation product
        # --------------------------------------------------

        inundation = (
            self.inundation_builder.build(
                flood_depth_m
            )
        )

        # --------------------------------------------------
        # Step 6: Summary
        # --------------------------------------------------

        summary = (
            self.inundation_builder.summary(
                flood_depth_m
            )
        )

        return {
            "rainfall_mm": rainfall,
            "lulc": lulc_array,
            "curve_number": curve_number,
            "runoff_mm": runoff,
            "flood_depth_mm": flood_depth_mm,
            "flood_depth_m": flood_depth_m,
            "flood_extent": inundation[
                "flood_extent"
            ],
            "risk_class": inundation[
                "risk_class"
            ],
            "risk_labels": inundation[
                "risk_labels"
            ],
            "summary": summary,
        }


if __name__ == "__main__":

    print("\nRainGuard End-to-End Flood Pipeline")
    print("===================================")

    pipeline = RainGuardFloodPipeline()

    # --------------------------------------------------
    # Synthetic 4 x 4 rainfall grid
    # --------------------------------------------------

    rainfall = np.array(
        [
            [20.0, 40.0, 80.0, 120.0],
            [30.0, 60.0, 100.0, 160.0],
            [15.0, 70.0, 140.0, 220.0],
            [10.0, 90.0, 180.0, 300.0],
        ],
        dtype=np.float32,
    )

    # --------------------------------------------------
    # Synthetic LULC
    #
    # 1 = Water
    # 2 = Forest
    # 3 = Vegetation
    # 4 = Agriculture
    # 5 = Barren
    # 6 = Built-up
    # 7 = Wetland
    # --------------------------------------------------

    lulc = np.array(
        [
            [2, 3, 4, 6],
            [3, 4, 6, 6],
            [2, 6, 6, 5],
            [3, 6, 5, 7],
        ],
        dtype=np.int16,
    )

    # --------------------------------------------------
    # Synthetic DEM in metres
    # --------------------------------------------------

    dem = np.array(
        [
            [18.0, 16.0, 14.0, 12.0],
            [17.0, 13.0, 10.0, 9.0],
            [15.0, 11.0, 8.0, 6.0],
            [14.0, 9.0, 5.0, 3.0],
        ],
        dtype=np.float32,
    )

    # --------------------------------------------------
    # Run complete pipeline
    # --------------------------------------------------

    result = pipeline.run(
        rainfall_mm=rainfall,
        lulc=lulc,
        dem=dem,
    )

    # --------------------------------------------------
    # Display results
    # --------------------------------------------------

    print("\nRainfall (mm)")
    print("-------------")
    print(result["rainfall_mm"])

    print("\nCurve Number")
    print("------------")
    print(result["curve_number"])

    print("\nRunoff (mm)")
    print("-----------")
    print(
        np.round(
            result["runoff_mm"],
            2,
        )
    )

    print("\nFlood Depth (m)")
    print("----------------")
    print(
        np.round(
            result["flood_depth_m"],
            3,
        )
    )

    print("\nFlood Extent")
    print("------------")
    print(result["flood_extent"])

    print("\nRisk Class")
    print("----------")
    print(result["risk_class"])

    print("\nSummary")
    print("-------")

    for key, value in result[
        "summary"
    ].items():
        print(
            f"{key}: {value}"
        )

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert (
        result["curve_number"].shape
        == rainfall.shape
    )

    assert (
        result["runoff_mm"].shape
        == rainfall.shape
    )

    assert (
        result["flood_depth_m"].shape
        == rainfall.shape
    )

    assert (
        result["flood_extent"].shape
        == rainfall.shape
    )

    assert (
        result["risk_class"].shape
        == rainfall.shape
    )

    assert np.all(
        result["runoff_mm"] >= 0
    )

    assert np.all(
        result["flood_depth_m"] >= 0
    )

    assert np.all(
        np.isin(
            result["flood_extent"],
            [0, 1],
        )
    )

    assert np.all(
        np.isin(
            result["risk_class"],
            [0, 1, 2, 3, 4],
        )
    )

    print(
        "\nSTATUS: End-to-End Flood Pipeline test PASSED"
    )