from pathlib import Path

import pandas as pd


INPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "rainfall_events_2015.csv"
)

OUTPUT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "regional_benchmark_2015.csv"
)


def classify_region(lat: float, lon: float) -> str:
    """
    Broad geographic classification for selecting a diverse
    historical benchmark across India.

    This is a project-level spatial grouping, not an official
    IMD meteorological subdivision classification.
    """

    # Northeast
    if lat >= 22 and lon >= 88:
        return "NORTHEAST"

    # North
    if lat >= 26:
        return "NORTH"

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

    # West-central / transitional area
    if lon < 84:
        return "WEST"

    return "CENTRAL"


def build_regional_benchmark(
    events: pd.DataFrame,
) -> pd.DataFrame:

    data = events.copy()

    data["region"] = data.apply(
        lambda row: classify_region(
            row["peak_latitude"],
            row["peak_longitude"],
        ),
        axis=1,
    )

    data = data.sort_values(
        "peak_rainfall_mm",
        ascending=False,
    ).reset_index(drop=True)

    return data


if __name__ == "__main__":

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    events = pd.read_csv(INPUT_FILE)

    benchmark = build_regional_benchmark(events)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    benchmark.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RainGuard India Regional Benchmark")
    print("----------------------------------")
    print(f"Total rainfall episodes : {len(benchmark)}")
    print(f"Output file             : {OUTPUT_FILE}")
    print()

    print("Events by region:")
    print(
        benchmark["region"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Top events:")
    print(
        benchmark[
            [
                "event_id",
                "peak_date",
                "peak_rainfall_mm",
                "peak_latitude",
                "peak_longitude",
                "duration_days",
                "region",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )