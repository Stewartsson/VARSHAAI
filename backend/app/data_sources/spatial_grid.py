import numpy as np


class CommonGrid:
    """
    RainGuard common spatial grid.

    Target:
    - Approximately 4 km spatial resolution
    - Geographic latitude/longitude coordinates
    - Suitable as the common target grid for
      satellite, radar, AWS/ARG and NWP data.
    """

    def __init__(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        resolution_deg: float = 0.04,
    ):
        if min_lat >= max_lat:
            raise ValueError(
                "min_lat must be smaller than max_lat."
            )

        if min_lon >= max_lon:
            raise ValueError(
                "min_lon must be smaller than max_lon."
            )

        if resolution_deg <= 0:
            raise ValueError(
                "resolution_deg must be greater than zero."
            )

        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.resolution_deg = resolution_deg

        self.latitudes = np.arange(
            min_lat,
            max_lat + resolution_deg,
            resolution_deg,
        )

        self.longitudes = np.arange(
            min_lon,
            max_lon + resolution_deg,
            resolution_deg,
        )

    @property
    def shape(self):
        return (
            len(self.latitudes),
            len(self.longitudes),
        )

    def mesh(self):
        return np.meshgrid(
            self.latitudes,
            self.longitudes,
            indexing="ij",
        )

    def describe(self):
        return {
            "min_lat": self.min_lat,
            "max_lat": self.max_lat,
            "min_lon": self.min_lon,
            "max_lon": self.max_lon,
            "resolution_deg": self.resolution_deg,
            "rows": len(self.latitudes),
            "columns": len(self.longitudes),
            "shape": self.shape,
        }


def nearest_grid_cell(
    latitude: float,
    longitude: float,
    grid: CommonGrid,
):
    """
    Find the nearest common-grid cell for a point observation.
    Useful for AWS/ARG station observations.
    """

    lat_index = int(
        np.abs(
            grid.latitudes - latitude
        ).argmin()
    )

    lon_index = int(
        np.abs(
            grid.longitudes - longitude
        ).argmin()
    )

    return {
        "row": lat_index,
        "column": lon_index,
        "latitude": float(
            grid.latitudes[lat_index]
        ),
        "longitude": float(
            grid.longitudes[lon_index]
        ),
    }


if __name__ == "__main__":

    print("RainGuard Common Spatial Grid")
    print("-----------------------------")

    # Chennai demonstration area.
    grid = CommonGrid(
        min_lat=12.0,
        max_lat=14.0,
        min_lon=79.0,
        max_lon=81.0,
        resolution_deg=0.04,
    )

    print("\nGrid configuration:")

    for key, value in grid.describe().items():
        print(f"  {key}: {value}")

    point = nearest_grid_cell(
        latitude=13.0827,
        longitude=80.2707,
        grid=grid,
    )

    print("\nChennai station mapping:")

    for key, value in point.items():
        print(f"  {key}: {value}")

    print("\n-----------------------------")
    print("Common spatial grid OK.")