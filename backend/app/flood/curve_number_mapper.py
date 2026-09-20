"""
RainGuard AI - Curve Number Mapper

Purpose:
    Convert Land Use / Land Cover (LULC) classes into
    SCS Curve Number (CN) values.

The resulting CN raster has the same shape as the
input LULC raster and can be passed directly into
SCSCNRunoffModel.

LULC classes used by this engineering prototype:

    1  = Water
    2  = Forest
    3  = Vegetation / Grassland
    4  = Agricultural land
    5  = Barren / Open land
    6  = Built-up / Impervious
    7  = Wetland

Important:
    These are prototype CN values for demonstration.
    A production implementation should use a validated
    soil-hydrologic-group-specific CN lookup and official
    LULC/soil datasets.
"""

from __future__ import annotations

import numpy as np


class CurveNumberMapper:
    """
    Maps LULC class IDs to Curve Number values.
    """

    DEFAULT_CN = {
        1: 30.0,   # Water
        2: 55.0,   # Forest
        3: 65.0,   # Vegetation / Grassland
        4: 75.0,   # Agriculture
        5: 70.0,   # Barren / Open land
        6: 95.0,   # Built-up / Impervious
        7: 50.0,   # Wetland
    }

    def __init__(
        self,
        cn_mapping: dict[int, float] | None = None,
    ):
        self.cn_mapping = (
            cn_mapping.copy()
            if cn_mapping is not None
            else self.DEFAULT_CN.copy()
        )

        self._validate_mapping()

    def _validate_mapping(self) -> None:
        """
        Validate the Curve Number lookup table.
        """

        for lulc_class, cn in self.cn_mapping.items():

            if not isinstance(
                lulc_class,
                (int, np.integer),
            ):
                raise ValueError(
                    "LULC class IDs must be integers."
                )

            if not (
                0.0 < float(cn) <= 100.0
            ):
                raise ValueError(
                    f"Invalid CN {cn} for "
                    f"LULC class {lulc_class}."
                )

    def map_lulc_to_cn(
        self,
        lulc: np.ndarray,
        nodata_value: int | float | None = None,
    ) -> np.ndarray:
        """
        Convert an LULC raster into a Curve Number raster.

        Parameters
        ----------
        lulc:
            2D numpy array containing integer LULC class IDs.

        nodata_value:
            Optional LULC value representing missing data.

        Returns
        -------
        np.ndarray
            Float32 Curve Number raster.

        Unknown classes and nodata pixels are represented
        by NaN rather than silently assigning a CN.
        """

        lulc_array = np.asarray(lulc)

        if lulc_array.ndim != 2:
            raise ValueError(
                "LULC raster must be a 2D array."
            )

        cn_raster = np.full(
            lulc_array.shape,
            np.nan,
            dtype=np.float32,
        )

        for lulc_class, cn in self.cn_mapping.items():

            mask = (
                lulc_array == lulc_class
            )

            cn_raster[mask] = float(cn)

        if nodata_value is not None:
            cn_raster[
                lulc_array == nodata_value
            ] = np.nan

        return cn_raster

    def supported_classes(
        self,
    ) -> list[int]:
        """
        Return supported LULC class IDs.
        """

        return sorted(
            self.cn_mapping.keys()
        )

    def describe_classes(
        self,
    ) -> dict[int, dict[str, float]]:
        """
        Return a simple description of the
        LULC -> CN mapping.
        """

        names = {
            1: "Water",
            2: "Forest",
            3: "Vegetation / Grassland",
            4: "Agriculture",
            5: "Barren / Open land",
            6: "Built-up / Impervious",
            7: "Wetland",
        }

        return {
            lulc_class: {
                "name": names.get(
                    lulc_class,
                    "Unknown",
                ),
                "curve_number": float(cn),
            }
            for lulc_class, cn
            in self.cn_mapping.items()
        }


if __name__ == "__main__":

    print("\nRainGuard Curve Number Mapper")
    print("=============================")

    mapper = CurveNumberMapper()

    # --------------------------------------------------
    # Test 1: Supported classes
    # --------------------------------------------------

    print("\nSupported LULC classes")
    print("----------------------")

    for item in mapper.describe_classes().values():
        print(
            f"{item['name']:<25}"
            f" CN = {item['curve_number']:.0f}"
        )

    # --------------------------------------------------
    # Test 2: Small LULC raster
    # --------------------------------------------------

    lulc_grid = np.array(
        [
            [1, 2, 3, 4],
            [5, 6, 7, 2],
            [3, 6, 4, 1],
        ],
        dtype=np.int16,
    )

    cn_grid = mapper.map_lulc_to_cn(
        lulc_grid
    )

    print("\nLULC raster")
    print("-----------")
    print(lulc_grid)

    print("\nCurve Number raster")
    print("-------------------")
    print(cn_grid)

    assert cn_grid.shape == (
        3,
        4,
    )

    assert np.all(
        np.isfinite(cn_grid)
    )

    # --------------------------------------------------
    # Test 3: Unknown class handling
    # --------------------------------------------------

    lulc_with_unknown = np.array(
        [
            [1, 2, 99],
            [6, 7, 4],
        ],
        dtype=np.int16,
    )

    cn_with_unknown = (
        mapper.map_lulc_to_cn(
            lulc_with_unknown
        )
    )

    print("\nUnknown class test")
    print("------------------")
    print(
        "Unknown LULC class 99 ->",
        cn_with_unknown[0, 2],
    )

    assert np.isnan(
        cn_with_unknown[0, 2]
    )

    # --------------------------------------------------
    # Test 4: Nodata handling
    # --------------------------------------------------

    lulc_with_nodata = np.array(
        [
            [1, 2, -9999],
            [6, 7, 4],
        ],
        dtype=np.int32,
    )

    cn_with_nodata = (
        mapper.map_lulc_to_cn(
            lulc_with_nodata,
            nodata_value=-9999,
        )
    )

    print("\nNoData test")
    print("-----------")
    print(
        "NoData ->",
        cn_with_nodata[0, 2],
    )

    assert np.isnan(
        cn_with_nodata[0, 2]
    )

    # --------------------------------------------------
    # Test 5: Custom mapping
    # --------------------------------------------------

    custom_mapper = CurveNumberMapper(
        {
            1: 25.0,
            2: 50.0,
            3: 60.0,
            4: 72.0,
            5: 68.0,
            6: 98.0,
            7: 45.0,
        }
    )

    custom_cn = (
        custom_mapper.map_lulc_to_cn(
            lulc_grid
        )
    )

    print("\nCustom mapping test")
    print("-------------------")
    print(
        "Built-up CN:",
        custom_cn[1, 1],
    )

    assert custom_cn[1, 1] == 98.0

    print(
        "\nSTATUS: Curve Number Mapper test PASSED"
    )