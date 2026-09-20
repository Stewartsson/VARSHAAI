from pathlib import Path
import pandas as pd

from app.historical.multi_year_loader import (
    discover_rainfall_files,
    load_year,
)
from app.historical.event_detection import (
    detect_extreme_events,
)


BASE_DIR = Path(__file__).resolve().parents[3]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "historical"
    / "multi_year_events.csv"
)


def main():
    files = discover_rainfall_files()

    all_events = []

    print("RainGuard Multi-Year Event Detection")
    print("-------------------------------------")

    for path in files:
        rainfall = load_year(path)

        year = int(
            pd.Timestamp(
                rainfall.TIME.values[0]
            ).year
        )

        print(f"\nProcessing {year}...")

        events = detect_extreme_events(rainfall)

        if events.empty:
            print("  Extreme events found : 0")
            continue

        events = events.copy()
        events.insert(0, "year", year)

        all_events.append(events)

        print(
            f"  Extreme events found : "
            f"{len(events)}"
        )

    if not all_events:
        raise RuntimeError(
            "No extreme events detected."
        )

    result = pd.concat(
        all_events,
        ignore_index=True,
    )

    # The existing event detector uses "date".
    result = result.sort_values(
        ["year", "date"]
    ).reset_index(drop=True)

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n-------------------------------------")
    print(
        f"Total extreme events : "
        f"{len(result)}"
    )

    print("\nEvents by year:")
    print(
        result["year"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()