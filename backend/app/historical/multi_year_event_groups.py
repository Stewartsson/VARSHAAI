from pathlib import Path
import pandas as pd
import numpy as np

from app.historical.multi_year_loader import (
    discover_rainfall_files,
    load_year,
)
from app.historical.event_detection import (
    detect_extreme_events,
)


BASE_DIR = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "multi_year_events.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "multi_year_rainfall_events.csv"
)


def find_peak_coordinates(rainfall, peak_date):
    day = rainfall.sel(TIME=peak_date)
    values = day.values

    if not np.isfinite(values).any():
        return None, None

    flat_index = np.nanargmax(values)

    lat_index, lon_index = np.unravel_index(
        flat_index,
        values.shape,
    )

    latitude = float(
        rainfall.LATITUDE.values[lat_index]
    )

    longitude = float(
        rainfall.LONGITUDE.values[lon_index]
    )

    return latitude, longitude


def load_events():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    if "date" not in df.columns:
        raise ValueError(
            "Expected 'date' column not found."
        )

    df["date"] = pd.to_datetime(df["date"])

    return df.sort_values(
        ["year", "date"]
    ).reset_index(drop=True)


def build_episode(year, rows, rainfall):
    group = pd.DataFrame(rows)

    peak_index = group[
        "max_rainfall_mm"
    ].idxmax()

    peak = group.loc[peak_index]

    peak_date = pd.Timestamp(
        peak["date"]
    )

    latitude, longitude = find_peak_coordinates(
        rainfall,
        peak_date,
    )

    return {
        "year": int(year),
        "start_date": group["date"].min().date(),
        "end_date": group["date"].max().date(),
        "duration_days": len(group),
        "peak_date": peak_date.date(),
        "peak_rainfall_mm": float(
            peak["max_rainfall_mm"]
        ),
        "peak_latitude": latitude,
        "peak_longitude": longitude,
        "peak_heavy_cells": int(
            group["heavy_cells"].max()
        ),
        "peak_very_heavy_cells": int(
            group["very_heavy_cells"].max()
        ),
        "peak_extreme_cells": int(
            group["extreme_cells"].max()
        ),
    }


def group_events(
    df,
    rainfall,
    year,
    max_gap_days=1,
):
    group = df[
        df["year"] == year
    ].sort_values(
        "date"
    ).reset_index(drop=True)

    episodes = []

    if group.empty:
        return episodes

    current_rows = [group.iloc[0]]

    for i in range(1, len(group)):
        previous_date = current_rows[-1]["date"]
        current_date = group.iloc[i]["date"]

        gap = (
            current_date - previous_date
        ).days

        if gap <= max_gap_days:
            current_rows.append(
                group.iloc[i]
            )
        else:
            episodes.append(
                build_episode(
                    year,
                    current_rows,
                    rainfall,
                )
            )

            current_rows = [
                group.iloc[i]
            ]

    episodes.append(
        build_episode(
            year,
            current_rows,
            rainfall,
        )
    )

    return episodes


def main():
    df = load_events()

    files = discover_rainfall_files()

    all_episodes = []

    print("RainGuard Multi-Year Rainfall Episodes")
    print("---------------------------------------")

    for path in files:
        rainfall = load_year(path)

        year = int(
            pd.Timestamp(
                rainfall.TIME.values[0]
            ).year
        )

        episodes = group_events(
            df,
            rainfall,
            year,
            max_gap_days=1,
        )

        all_episodes.extend(episodes)

        print(
            f"\nProcessing {year}..."
        )
        print(
            f"  Episodes created : "
            f"{len(episodes)}"
        )

    episodes = pd.DataFrame(
        all_episodes
    )

    if episodes.empty:
        raise RuntimeError(
            "No rainfall episodes were created."
        )

    episodes = episodes.sort_values(
        ["year", "start_date"]
    ).reset_index(drop=True)

    episodes.insert(
        0,
        "event_id",
        [
            f"RG{int(row.year)}-{i:03d}"
            for i, row in episodes.iterrows()
        ],
    )

    episodes.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n---------------------------------------")
    print(
        f"Extreme event-days : {len(df)}"
    )
    print(
        f"Rainfall episodes  : {len(episodes)}"
    )

    print("\nEpisodes by year:")
    print(
        episodes["year"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nTop rainfall episodes:")

    display_columns = [
        "event_id",
        "start_date",
        "end_date",
        "duration_days",
        "peak_date",
        "peak_rainfall_mm",
        "peak_latitude",
        "peak_longitude",
    ]

    top_events = (
        episodes
        .sort_values(
            "peak_rainfall_mm",
            ascending=False,
        )[display_columns]
        .head(15)
        .copy()
    )

    top_events["peak_latitude"] = (
        top_events["peak_latitude"]
        .map(
            lambda x:
            f"{x:.2f}"
            if pd.notna(x)
            else "N/A"
        )
    )

    top_events["peak_longitude"] = (
        top_events["peak_longitude"]
        .map(
            lambda x:
            f"{x:.2f}"
            if pd.notna(x)
            else "N/A"
        )
    )

    print(
        top_events.to_string(
            index=False
        )
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()