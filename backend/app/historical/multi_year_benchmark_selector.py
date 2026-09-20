from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "multi_year_rainfall_events.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "master_benchmark_events.csv"
)


REGION_LIMITS = {
    "NORTH": 3,
    "NORTHEAST": 3,
    "EAST": 3,
    "CENTRAL": 3,
    "WEST": 3,
    "WEST_COAST": 3,
    "SOUTH": 3,
}


def classify_region(latitude, longitude):
    lat = float(latitude)
    lon = float(longitude)

    if lat >= 22 and lon >= 88:
        return "NORTHEAST"

    if lat >= 26:
        return "NORTH"

    if (
        8 <= lat <= 23
        and 72 <= lon <= 76
    ):
        return "WEST_COAST"

    if lon >= 84 and lat >= 20:
        return "EAST"

    if lon < 74:
        return "WEST"

    if (
        18 <= lat < 26
        and 74 <= lon < 84
    ):
        return "CENTRAL"

    if lat < 18:
        return "SOUTH"

    return "CENTRAL"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        "event_id",
        "year",
        "start_date",
        "end_date",
        "duration_days",
        "peak_date",
        "peak_rainfall_mm",
        "peak_latitude",
        "peak_longitude",
        "peak_extreme_cells",
        "peak_very_heavy_cells",
        "peak_heavy_cells",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    df["benchmark_region"] = df.apply(
        lambda row: classify_region(
            row["peak_latitude"],
            row["peak_longitude"],
        ),
        axis=1,
    )

    selected = []

    for region, limit in REGION_LIMITS.items():
        regional = df[
            df["benchmark_region"] == region
        ].copy()

        regional = regional.sort_values(
            [
                "peak_extreme_cells",
                "peak_very_heavy_cells",
                "peak_heavy_cells",
                "peak_rainfall_mm",
                "duration_days",
            ],
            ascending=False,
        )

        selected.append(
            regional.head(limit)
        )

    result = pd.concat(
        selected,
        ignore_index=True,
    )

    result = result.sort_values(
        [
            "benchmark_region",
            "year",
            "peak_date",
        ]
    ).reset_index(drop=True)

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RainGuard Multi-Year Benchmark Selection")
    print("----------------------------------------")
    print(
        f"Candidate episodes : {len(df)}"
    )
    print(
        f"Selected events    : {len(result)}"
    )

    print("\nEvents per region:")
    print(
        result["benchmark_region"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nEvents per year:")
    print(
        result["year"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nSelected benchmark:")
    print(
        result[
            [
                "event_id",
                "year",
                "peak_date",
                "peak_rainfall_mm",
                "peak_latitude",
                "peak_longitude",
                "duration_days",
                "benchmark_region",
            ]
        ].to_string(index=False)
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()