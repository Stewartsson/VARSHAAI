from pathlib import Path

from app.data_sources.mosdac.hem_reader import (
    read_hem_file,
    get_chennai_rainfall,
    get_chennai_statistics,
)


# ============================================================
# VARSHAAI
# MOSDAC INSAT-3DR HEM TEST
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

HEM_FILE = (
    BASE_DIR
    / "data"
    / "mosdac"
    / "hem"
    / "3RIMG_15SEP2026_0015_L2B_HEM_V01R00.h5"
)


def main():

    print("=" * 70)
    print("VARSHAAI - INSAT-3DR HEM TEST")
    print("=" * 70)

    print()
    print("FILE:")
    print(HEM_FILE)

    if not HEM_FILE.exists():

        print()
        print("ERROR: HEM file not found.")

        return

    print()
    print("File exists: TRUE")

    # ========================================================
    # READ HEM
    # ========================================================

    data = read_hem_file(
        HEM_FILE
    )

    print()
    print("SATELLITE")
    print("-" * 70)

    print(
        data["satellite"]
    )

    print()
    print("PRODUCT")
    print("-" * 70)

    print(
        data["product"]
    )

    print()
    print("TIME")
    print("-" * 70)

    print(
        "UTC:",
        data["timestamp_utc"]
    )

    print(
        "IST:",
        data["timestamp_ist"]
    )

    print()
    print("RAINFALL DATA")
    print("-" * 70)

    print(
        "Shape:",
        data["rainfall"].shape
    )

    print(
        "Units:",
        data["metadata"]["units"]
    )

    print(
        "Fill value:",
        data["metadata"]["fill_value"]
    )

    # ========================================================
    # CHENNAI PIXEL
    # ========================================================

    chennai = get_chennai_rainfall(
        HEM_FILE
    )

    print()
    print("CHENNAI NEAREST PIXEL")
    print("-" * 70)

    print(
        "Latitude:",
        chennai["latitude"]
    )

    print(
        "Longitude:",
        chennai["longitude"]
    )

    print(
        "Rainfall:",
        chennai["rainfall_mm_hr"],
        "mm/hr"
    )

    print(
        "Pixel:",
        (
            chennai["pixel_row"],
            chennai["pixel_column"],
        )
    )

    # ========================================================
    # CHENNAI AREA
    # ========================================================

    stats = get_chennai_statistics(
        HEM_FILE
    )

    print()
    print("CHENNAI AREA STATISTICS")
    print("-" * 70)

    print(
        "Status:",
        stats["status"]
    )

    if stats["status"] == "success":

        print(
            "Minimum:",
            stats["minimum_mm_hr"],
            "mm/hr"
        )

        print(
            "Maximum:",
            stats["maximum_mm_hr"],
            "mm/hr"
        )

        print(
            "Mean:",
            stats["mean_mm_hr"],
            "mm/hr"
        )

        print(
            "Median:",
            stats["median_mm_hr"],
            "mm/hr"
        )

        print(
            "Valid pixels:",
            stats["valid_pixel_count"]
        )

    print()
    print("=" * 70)
    print("MOSDAC HEM TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()