from pathlib import Path
import xarray as xr


BASE_DIR = Path(__file__).resolve().parents[3]

RAINFALL_DIR = (
    BASE_DIR
    / "data"
    / "historical"
    / "imd_rainfall"
)


def discover_rainfall_files():
    files = sorted(RAINFALL_DIR.glob("RF25_ind*_rfp25.nc"))

    if not files:
        raise FileNotFoundError(
            f"No IMD rainfall NetCDF files found in: {RAINFALL_DIR}"
        )

    return files


def load_year(path):
    path = Path(path)

    ds = xr.open_dataset(path)

    required_dimensions = {
        "TIME",
        "LATITUDE",
        "LONGITUDE",
    }

    missing_dimensions = required_dimensions - set(ds.dims)

    if missing_dimensions:
        raise ValueError(
            f"{path.name}: missing dimensions "
            f"{sorted(missing_dimensions)}"
        )

    if "RAINFALL" not in ds.data_vars:
        raise ValueError(
            f"{path.name}: RAINFALL variable not found."
        )

    rainfall = ds["RAINFALL"]

    if rainfall.attrs.get("units") != "mm":
        raise ValueError(
            f"{path.name}: unexpected rainfall units "
            f"{rainfall.attrs.get('units')}"
        )

    return rainfall


def main():
    files = discover_rainfall_files()

    print("RainGuard Multi-Year IMD Loader")
    print("--------------------------------")
    print(f"Files discovered : {len(files)}")

    for path in files:
        rainfall = load_year(path)

        start_date = rainfall.TIME.values[0]
        end_date = rainfall.TIME.values[-1]

        print()
        print(f"File       : {path.name}")
        print(f"Dimensions : {dict(rainfall.sizes)}")
        print(f"Units      : {rainfall.attrs.get('units')}")
        print(f"Start date : {start_date}")
        print(f"End date   : {end_date}")
        print(
            f"Maximum    : "
            f"{float(rainfall.max(skipna=True)):.2f} mm"
        )
        print(
            f"Mean       : "
            f"{float(rainfall.mean(skipna=True)):.2f} mm"
        )


if __name__ == "__main__":
    main()