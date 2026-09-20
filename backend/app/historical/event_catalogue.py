from pathlib import Path

import pandas as pd
import xarray as xr

from app.historical.imd_loader import load_imd_rainfall


OUTPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "event_catalogue_2015.csv"
)


def build_event_catalogue(
    rainfall: xr.DataArray,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add spatial information to the candidate extreme rainfall events.

    For every event day, identify:
    - peak rainfall
    - peak latitude
    - peak longitude
    - number of valid grid cells
    - spatial footprint above heavy-rain thresholds
    """

    records = []

    for _, event in events.iterrows():

        date = event["date"]

        daily = rainfall.sel(
            TIME=date
        )

        valid = daily.where(
            daily.notnull()
        )

        if int(valid.notnull().sum()) == 0:
            continue

        peak_value = float(
            valid.max()
        )

        peak_location = valid.where(
            valid == peak_value,
            drop=True
        )

        peak_lat = float(
            peak_location.LATITUDE.values[0]
        )

        peak_lon = float(
            peak_location.LONGITUDE.values[0]
        )

        valid_cells = int(
            valid.notnull().sum()
        )

        heavy_cells = int(
            (valid >= 64.5).sum()
        )

        very_heavy_cells = int(
            (valid >= 115.6).sum()
        )

        extreme_cells = int(
            (valid >= 204.5).sum()
        )

        records.append(
            {
                "date": date,
                "max_rainfall_mm": peak_value,
                "peak_latitude": peak_lat,
                "peak_longitude": peak_lon,
                "valid_grid_cells": valid_cells,
                "heavy_cells": heavy_cells,
                "very_heavy_cells": very_heavy_cells,
                "extreme_cells": extreme_cells,
                "mean_rainfall_mm": float(
                    valid.mean()
                ),
            }
        )

    catalogue = pd.DataFrame(records)

    if catalogue.empty:
        return catalogue

    catalogue["event_area_ratio"] = (
        catalogue["heavy_cells"]
        / catalogue["valid_grid_cells"]
    )

    catalogue["event_category"] = "HEAVY"

    catalogue.loc[
        catalogue["very_heavy_cells"] > 0,
        "event_category"
    ] = "VERY_HEAVY"

    catalogue.loc[
        catalogue["extreme_cells"] > 0,
        "event_category"
    ] = "EXTREME"

    catalogue = catalogue.sort_values(
        [
            "event_category",
            "max_rainfall_mm",
        ],
        ascending=[True, False],
    )

    return catalogue.reset_index(drop=True)


if __name__ == "__main__":

    rainfall = load_imd_rainfall()

    events_file = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "historical"
        / "events_2015.csv"
    )

    events = pd.read_csv(events_file)

    catalogue = build_event_catalogue(
        rainfall,
        events,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalogue.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RainGuard Historical Event Catalogue")
    print("------------------------------------")
    print(f"Events analysed : {len(catalogue)}")
    print(f"Output file     : {OUTPUT_FILE}")
    print()

    print(
        catalogue.head(20).to_string(
            index=False
        )
    )