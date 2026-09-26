import numpy as np

def inverse_distance_weighting(
    x_obs: np.ndarray, y_obs: np.ndarray, v_obs: np.ndarray,
    grid_x: np.ndarray, grid_y: np.ndarray,
    power: float = 2.0
) -> np.ndarray:
    """
    Interpolates point observations (e.g., AWS/ARG) onto a regular grid using Inverse Distance Weighting (IDW).
    
    Parameters:
    - x_obs: 1D array of observation X coordinates (longitudes)
    - y_obs: 1D array of observation Y coordinates (latitudes)
    - v_obs: 1D array of observed values (e.g., rainfall)
    - grid_x: 2D array of grid X coordinates
    - grid_y: 2D array of grid Y coordinates
    - power: The power parameter for IDW (usually 2.0)
    
    Returns:
    - grid_v: 2D array of interpolated values on the grid
    """
    # Flatten the grids for vectorized distance calculation
    flat_grid_x = grid_x.ravel()
    flat_grid_y = grid_y.ravel()
    
    grid_v = np.zeros_like(flat_grid_x, dtype=float)
    
    for i in range(len(flat_grid_x)):
        gx = flat_grid_x[i]
        gy = flat_grid_y[i]
        
        # Calculate distances from this grid point to all observation points
        distances = np.sqrt((x_obs - gx)**2 + (y_obs - gy)**2)
        
        # Handle exact match (distance = 0)
        if np.any(distances == 0):
            grid_v[i] = v_obs[distances == 0][0]
            continue
            
        # Calculate weights
        weights = 1.0 / (distances ** power)
        
        # Calculate weighted average
        grid_v[i] = np.sum(weights * v_obs) / np.sum(weights)
        
    return grid_v.reshape(grid_x.shape)

def handle_missing_data(obs_values: np.ndarray, fill_value: float = 0.0) -> np.ndarray:
    """
    Handling missing data (e.g., AWS stations dropping out).
    Fills NaN values with a default or statistically derived value.
    """
    clean_values = np.copy(obs_values)
    clean_values[np.isnan(clean_values)] = fill_value
    return clean_values

if __name__ == "__main__":
    # Test IDW with dummy AWS data
    # 4 AWS stations
    lons = np.array([80.1, 80.2, 80.3, 80.4])
    lats = np.array([13.1, 13.2, 13.3, 13.4])
    rain = np.array([10.0, 50.0, np.nan, 20.0]) # Note the NaN (missing data)
    
    # 1. Handle missing data
    rain_clean = handle_missing_data(rain, fill_value=0.0)
    
    # Target grid (2x2)
    grid_lon, grid_lat = np.meshgrid(
        np.linspace(80.0, 80.5, 5),
        np.linspace(13.0, 13.5, 5)
    )
    
    # 2. Spatial Interpolation
    grid_rain = inverse_distance_weighting(lons, lats, rain_clean, grid_lon, grid_lat)
    
    print("Interpolated Grid Rainfall:\n", grid_rain)
