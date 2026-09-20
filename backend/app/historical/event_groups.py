from pathlib import Path

import pandas as pd


INPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "event_catalogue_2015.csv"
)

OUTPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "rainfall_events_2015.csv"
)


def group_rainfall_events(
    catalogue: pd.DataFrame,
    max_gap_days: int = 1,
) -> pd.DataFrame:
    """
    Group consecutive extreme-rainfall days into rainfall episodes.

    Days separated by at most max_gap_days are considered part of
    the same rainfall episode.
    """

    if catalogue.empty:
        return pd.DataFrame()

    data = catalogue.copy()

    data["date"] = pd.to_datetime(data["date"])

    data = data.sort_values("date").reset_index(drop=True)

    date_gap = data["date"].diff().dt.days

    data["event_group"] = (
        (date_gap > max_gap_days)
        .fillna(True)
        .cumsum()
    )

    grouped = []

    for group_id, group in data.groupby("event_group"):

        peak_row = group.loc[
            group["max_rainfall_mm"].idxmax()
        ]

        grouped.append(
            {
                "event_id": f"RG2015-{int(group_id):03d}",
                "start_date": group["date"].min().date().isoformat(),
                "end_date": group["date"].max().date().isoformat(),
                "duration_days": int(len(group)),
                "peak_date": peak_row["date"].date().isoformat(),
                "peak_rainfall_mm": float(
                    peak_row["max_rainfall_mm"]
                ),
                "peak_latitude": float(
                    peak_row["peak_latitude"]
                ),
                "peak_longitude": float(
                    peak_row["peak_longitude"]
                ),
                "peak_heavy_cells": int(
                    peak_row["heavy_cells"]
                ),
                "peak_very_heavy_cells": int(
                    peak_row["very_heavy_cells"]
                ),
                "peak_extreme_cells": int(
                    peak_row["extreme_cells"]
                ),
                "peak_event_category": peak_row[
                    "event_category"
                ],
            }
        )

    result = pd.DataFrame(grouped)

    result = result.sort_values(
        "peak_rainfall_mm",
        ascending=False,
    ).reset_index(drop=True)

    return result


if __name__ == "__main__":

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Event catalogue not found: {INPUT_FILE}"
        )

    catalogue = pd.read_csv(INPUT_FILE)

    events = group_rainfall_events(catalogue)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    events.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RainGuard Historical Event Grouping")
    print("-----------------------------------")
    print(f"Extreme days     : {len(catalogue)}")
    print(f"Rainfall events  : {len(events)}")
    print(f"Output file      : {OUTPUT_FILE}")
    print()

    print("Top rainfall episodes:")
    print(
        events.head(20).to_string(index=False)
    )