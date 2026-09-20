from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "selected_benchmark_2015.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "benchmark_report_2015.csv"
)


def load_benchmark():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Benchmark file not found: {INPUT_FILE}"
        )

    return pd.read_csv(INPUT_FILE)


def classify_severity(rainfall_mm):
    if rainfall_mm >= 204.5:
        return "EXTREME"
    if rainfall_mm >= 115.6:
        return "VERY_HEAVY"
    if rainfall_mm >= 64.5:
        return "HEAVY"
    return "BELOW_HEAVY"


def build_report(df):
    report = df.copy()

    report["severity"] = report["peak_rainfall_mm"].apply(
        classify_severity
    )

    report["chennai_south_event"] = (
        (report["benchmark_region"] == "SOUTH")
        & (report["peak_latitude"].between(12.0, 14.5))
        & (report["peak_longitude"].between(79.0, 81.5))
    )

    report["west_coast_coverage"] = (
        (report["peak_latitude"].between(8.0, 23.0))
        & (report["peak_longitude"].between(72.0, 76.0))
    )

    columns = [
        "event_id",
        "peak_date",
        "duration_days",
        "peak_rainfall_mm",
        "peak_latitude",
        "peak_longitude",
        "benchmark_region",
        "severity",
        "chennai_south_event",
        "west_coast_coverage",
    ]

    return report[columns]


def main():
    df = load_benchmark()
    report = build_report(df)

    report.to_csv(OUTPUT_FILE, index=False)

    print("RainGuard Historical Benchmark Report")
    print("-------------------------------------")
    print(f"Events analysed : {len(report)}")
    print(f"Output file     : {OUTPUT_FILE}")

    print("\nEvents by region:")
    print(
        report["benchmark_region"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nSeverity distribution:")
    print(
        report["severity"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nChennai/South representation:")
    print(
        f"  Events near Chennai : "
        f"{int(report['chennai_south_event'].sum())}"
    )

    print("\nWest Coast coverage:")
    west_coast_count = int(
        report["west_coast_coverage"].sum()
    )
    print(f"  Selected events : {west_coast_count}")

    if west_coast_count == 0:
        print(
            "  Status          : NOT REPRESENTED "
            "in selected 2015 benchmark"
        )
    else:
        print(
            "  Status          : REPRESENTED"
        )

    print("\nSelected benchmark events:")
    print(
        report.to_string(index=False)
    )


if __name__ == "__main__":
    main()