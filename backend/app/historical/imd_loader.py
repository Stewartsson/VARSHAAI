from pathlib import Path

import xarray as xr


DEFAULT_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "historical"
    / "imd_rainfall"
    / "RF25_ind2015_rfp25.nc"
)


def load_imd_rainfall(path: str | Path = DEFAULT_FILE) -> xr.DataArray:
    """
    Load the IMD 0.25° daily gridded rainfall dataset.

    NaN values are preserved because they represent unavailable/masked
    grid cells and must not be blindly converted to zero or interpolated.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"IMD rainfall file not found: {path}"
        )

    ds = xr.open_dataset(path)

    required_dimensions = {
        "TIME",
        "LATITUDE",
        "LONGITUDE",
    }

    missing_dimensions = required_dimensions - set(ds.dims)

    if missing_dimensions:
        raise ValueError(
            f"Missing required dimensions: {sorted(missing_dimensions)}"
        )

    if "RAINFALL" not in ds.data_vars:
        raise ValueError(
            "RAINFALL variable not found in IMD dataset."
        )

    rainfall = ds["RAINFALL"]

    if rainfall.attrs.get("units") != "mm":
        raise ValueError(
            f"Unexpected rainfall units: "
            f"{rainfall.attrs.get('units')}"
        )

    return rainfall


if __name__ == "__main__":
    rainfall = load_imd_rainfall()

    print("RainGuard IMD historical loader")
    print("--------------------------------")
    print(f"Dimensions : {dict(rainfall.sizes)}")
    print(f"Units      : {rainfall.attrs.get('units')}")
    print(f"Start date : {rainfall.TIME.values[0]}")
    print(f"End date   : {rainfall.TIME.values[-1]}")
    print(f"Minimum    : {float(rainfall.min(skipna=True)):.2f} mm")
    print(f"Maximum    : {float(rainfall.max(skipna=True)):.2f} mm")
    print(f"Mean       : {float(rainfall.mean(skipna=True)):.2f} mm")