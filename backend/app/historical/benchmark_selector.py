from pathlib import Path

import pandas as pd


INPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "regional_benchmark_2015.csv"
)

OUTPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "selected_benchmark_2015.csv"
)


REGION_LIMITS = {
    "NORTH": 2,
    "NORTHEAST": 2,
    "EAST": 2,
    "CENTRAL": 2,
    "WEST": 2,
    "WEST_COAST": 2,
    "SOUTH": 2,
}


def classify_benchmark_region(
    lat: float,
    lon: float,
) -> str:
    """
    Broad RainGuard benchmark regions.

    These are engineering groups for historical validation,
    not official IMD meteorological subdivisions.
    """

    # Northeast
    if lat >= 22 and lon >= 88:
        return "NORTHEAST"

    # North
    if lat >= 26:
        return "NORTH"

    # West Coast / Western Ghats
    if (
        8 <= lat <= 23
        and 72 <= lon <= 76
    ):
        return "WEST_COAST"

    # East
    if lon >= 84 and lat >= 20:
        return "EAST"

    # West
    if lon < 74:
        return "WEST"

    # Central
    if 18 <= lat < 26 and 74 <= lon < 84:
        return "CENTRAL"

    # South
    if lat < 18:
        return "SOUTH"

    return "CENTRAL"


def select_events(
    events: pd.DataFrame,
) -> pd.DataFrame:

    data = events.copy()

    data["benchmark_region"] = data.apply(
        lambda row: classify_benchmark_region(
            row["peak_latitude"],
            row["peak_longitude"],
        ),
        axis=1,
    )

    selected = []

    for region, limit in REGION_LIMITS.items():

        regional = data[
            data["benchmark_region"] == region
        ].copy()

        regional = regional.sort_values(
            [
                "peak_extreme_cells",
                "peak_heavy_cells",
                "peak_rainfall_mm",
            ],
            ascending=False,
        )

        selected.append(
            regional.head(limit)
        )

    if not selected:
        return pd.DataFrame()

    result = pd.concat(
        selected,
        ignore_index=True,
    )

    result = result.sort_values(
        [
            "benchmark_region",
            "peak_rainfall_mm",
        ],
        ascending=[True, False],
    )

    return result.reset_index(drop=True)


if __name__ == "__main__":

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    events = pd.read_csv(INPUT_FILE)

    selected = select_events(events)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    selected.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RainGuard Historical Benchmark Selection")
    print("----------------------------------------")
    print(
        f"Candidate events : {len(events)}"
    )
    print(
        f"Selected events  : {len(selected)}"
    )
    print(
        f"Output file      : {OUTPUT_FILE}"
    )
    print()

    print("Selected benchmark:")
    print(
        selected[
            [
                "event_id",
                "peak_date",
                "peak_rainfall_mm",
                "peak_latitude",
                "peak_longitude",
                "duration_days",
                "benchmark_region",
            ]
        ].to_string(index=False)
    )

    print()
    print("Events per region:")
    print(
        selected["benchmark_region"]
        .value_counts()
        .sort_index()
        .to_string()
    )