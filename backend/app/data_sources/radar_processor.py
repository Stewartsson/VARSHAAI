import numpy as np

def remove_ground_clutter(dbz_grid: np.ndarray, clutter_threshold_dbz: float = 65.0) -> np.ndarray:
    """
    Radar QC: Ground clutter removal.
    Extremely high reflectivity near the surface is often ground clutter (buildings, hills).
    We mask out values above a certain unrealistic threshold for precipitation.
    """
    clean_grid = np.copy(dbz_grid)
    clean_grid[clean_grid >= clutter_threshold_dbz] = np.nan
    
    # Also mask out negative dBZ which are practically no rain
    clean_grid[clean_grid < 0] = np.nan
    return clean_grid

def dbz_to_rainfall_rate(dbz_grid: np.ndarray, a: float = 200.0, b: float = 1.6) -> np.ndarray:
    """
    Converts Radar Reflectivity (dBZ) to Rainfall Rate (mm/hr) using the Z-R relationship.
    Marshall-Palmer: Z = a * R^b
    Z = 10^(dBZ/10)
    R = (Z/a)^(1/b)
    """
    # Convert dBZ to Z (linear scale)
    z_grid = 10.0 ** (dbz_grid / 10.0)
    
    # Apply Z-R relationship to get Rainfall Rate (R)
    rainfall_rate = (z_grid / a) ** (1.0 / b)
    
    # Fill NaN values with 0 mm/hr
    rainfall_rate = np.nan_to_num(rainfall_rate, nan=0.0)
    
    return rainfall_rate

def process_radar_grid(raw_dbz: np.ndarray) -> np.ndarray:
    """
    End-to-end processing of a raw radar reflectivity grid.
    1. QC: Clutter removal
    2. Conversion: Z-R relationship
    """
    clean_dbz = remove_ground_clutter(raw_dbz)
    rainfall_mm_hr = dbz_to_rainfall_rate(clean_dbz)
    return rainfall_mm_hr

if __name__ == "__main__":
    # Test with dummy data
    dummy_dbz = np.array([
        [10.0, 20.0, 30.0],
        [40.0, 50.0, 70.0], # 70 dBZ is ground clutter
        [-10.0, 0.0, 15.0]
    ])
    print("Raw dBZ:\n", dummy_dbz)
    rain_rate = process_radar_grid(dummy_dbz)
    print("Processed Rainfall Rate (mm/hr):\n", rain_rate)
