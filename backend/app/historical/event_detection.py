from pathlib import Path

import pandas as pd
import xarray as xr

from app.historical.imd_loader import load_imd_rainfall


OUTPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "events_2015.csv"
)


def detect_extreme_events(
    rainfall: xr.DataArray,
    heavy_threshold: float = 64.5,
    very_heavy_threshold: float = 115.6,
    extreme_threshold: float = 204.5,
) -> pd.DataFrame:
    """
    Detect India-wide extreme rainfall days.

    Thresholds are expressed in mm/day.

    NaN cells are preserved as unavailable/masked cells and are
    excluded from the spatial calculations.
    """

    records = []

    for timestamp in rainfall.TIME.values:
        daily = rainfall.sel(TIME=timestamp)

        valid = daily.where(daily.notnull(), drop=True)

        if valid.size == 0:
            continue

        max_rainfall = float(valid.max())
        mean_rainfall = float(valid.mean())

        heavy_cells = int((valid >= heavy_threshold).sum())
        very_heavy_cells = int((valid >= very_heavy_threshold).sum())
        extreme_cells = int((valid >= extreme_threshold).sum())

        records.append(
            {
                "date": pd.Timestamp(timestamp).date().isoformat(),
                "max_rainfall_mm": max_rainfall,
                "mean_rainfall_mm": mean_rainfall,
                "heavy_cells": heavy_cells,
                "very_heavy_cells": very_heavy_cells,
                "extreme_cells": extreme_cells,
            }
        )

    result = pd.DataFrame(records)

    result["severity_score"] = (
        result["max_rainfall_mm"]
        + result["very_heavy_cells"] * 0.5
        + result["extreme_cells"] * 1.0
    )

    result = result[
        (result["max_rainfall_mm"] >= extreme_threshold)
        | (result["very_heavy_cells"] >= 10)
    ]

    return result.sort_values(
        "severity_score",
        ascending=False,
    ).reset_index(drop=True)


if __name__ == "__main__":
    rainfall = load_imd_rainfall()

    events = detect_extreme_events(rainfall)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    events.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RainGuard Historical Event Detector")
    print("-----------------------------------")
    print(f"Days analysed : {len(events)}")
    print(f"Output file   : {OUTPUT_FILE}")
    print()
    print("Top 20 extreme rainfall days:")
    print(
        events.head(20).to_string(index=False)
    )