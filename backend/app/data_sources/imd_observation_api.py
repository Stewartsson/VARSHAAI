from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from .imd_observations import (
    get_observation_status,
    fetch_tamil_nadu_observations,
    get_chennai_observations,
)
from .spatial_interpolator import handle_missing_data, inverse_distance_weighting
import numpy as np

router = APIRouter(
    prefix="/api/observations",
    tags=["IMD AWS ARG"],
)


@router.get("/status")
def observation_status():
    return get_observation_status()


@router.get("/tamil-nadu")
def tamil_nadu_observations():
    return fetch_tamil_nadu_observations()


@router.get("/chennai")
def chennai_observations():
    return get_chennai_observations()


class InterpolateRequest(BaseModel):
    lons: List[float]
    lats: List[float]
    values: List[float]
    grid_bounds: List[float]  # [min_lon, max_lon, min_lat, max_lat]
    grid_size: int = 10

@router.post("/interpolate")
def interpolate_observations(request: InterpolateRequest):
    """
    Interpolate point observations to a grid using IDW and handle missing data.
    """
    lons = np.array(request.lons)
    lats = np.array(request.lats)
    values = np.array(request.values)
    
    clean_values = handle_missing_data(values, fill_value=0.0)
    
    min_lon, max_lon, min_lat, max_lat = request.grid_bounds
    grid_lon, grid_lat = np.meshgrid(
        np.linspace(min_lon, max_lon, request.grid_size),
        np.linspace(min_lat, max_lat, request.grid_size)
    )
    
    grid_values = inverse_distance_weighting(lons, lats, clean_values, grid_lon, grid_lat)
    
    return {
        "status": "success",
        "grid_values": grid_values.tolist(),
        "info": "Interpolated using IDW. Missing values replaced with 0.0."
    }