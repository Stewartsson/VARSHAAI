import numpy as np

from app.historical.imd_loader import load_imd_rainfall
from app.data_sources.spatial_grid import CommonGrid
from app.data_sources.regridder import bilinear_regrid


def main():

    print("RainGuard IMD → Common Grid Regridding Test")
    print("--------------------------------------------")

    print("\nLoading official IMD 2015 rainfall dataset...")

    rainfall = load_imd_rainfall()

    print(
        f"  Original dimensions: "
        f"{dict(rainfall.sizes)}"
    )

    print(
        f"  Units: "
        f"{rainfall.attrs.get('units')}"
    )

    # Use December 2, 2015, one of our
    # previously identified heavy-rain event days.
    rainfall_day = rainfall.sel(
        TIME="2015-12-02"
    )

    print(
        f"\nSelected date: "
        f"{rainfall_day.TIME.values}"
    )

    source_latitudes = rainfall_day.LATITUDE.values
    source_longitudes = rainfall_day.LONGITUDE.values
    source_values = rainfall_day.values

    print(
        f"  Source latitude points: "
        f"{len(source_latitudes)}"
    )

    print(
        f"  Source longitude points: "
        f"{len(source_longitudes)}"
    )

    print(
        f"  Source field shape: "
        f"{source_values.shape}"
    )

    print("\nCreating Chennai-area common grid...")

    target_grid = CommonGrid(
        min_lat=12.0,
        max_lat=14.0,
        min_lon=79.0,
        max_lon=81.0,
        resolution_deg=0.04,
    )

    print(
        f"  Target grid shape: "
        f"{target_grid.shape}"
    )

    print("\nPerforming bilinear regridding...")

    regridded = bilinear_regrid(
        source_latitudes,
        source_longitudes,
        source_values,
        target_grid,
    )

    valid_cells = np.isfinite(
        regridded
    )

    print(
        f"  Regridded shape: "
        f"{regridded.shape}"
    )

    print(
        f"  Valid cells: "
        f"{int(valid_cells.sum())}"
    )

    if valid_cells.any():

        print(
            f"  Minimum: "
            f"{np.nanmin(regridded):.2f} mm"
        )

        print(
            f"  Maximum: "
            f"{np.nanmax(regridded):.2f} mm"
        )

        print(
            f"  Mean: "
            f"{np.nanmean(regridded):.2f} mm"
        )

    print("\n--------------------------------------------")
    print(
        "IMD → RainGuard common-grid "
        "regridding test complete."
    )


if __name__ == "__main__":
    main()