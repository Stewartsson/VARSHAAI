from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from .radar_service import (
    get_chennai_radar_products,
    get_chennai_radar_status,
)
from .radar_processor import process_radar_grid
import numpy as np

router = APIRouter(prefix="/api/radar", tags=["Radar"])


@router.get("/status")
def radar_status():
    return get_chennai_radar_status()


@router.get("/chennai")
def chennai_radar():
    return get_chennai_radar_products()


@router.get("/products")
def radar_products():
    result = get_chennai_radar_products()
    return {
        "status": result["status"],
        "radar": result["radar"],
        "products": result["products"],
    }

class RadarProcessRequest(BaseModel):
    dbz_grid: List[List[float]]
    
@router.post("/process_zr")
def process_zr(request: RadarProcessRequest):
    """
    Apply QC and Z-R relationship to a raw radar reflectivity grid.
    """
    raw_dbz = np.array(request.dbz_grid)
    rain_rate = process_radar_grid(raw_dbz)
    
    return {
        "status": "success",
        "rainfall_mm_hr": rain_rate.tolist(),
        "info": "Processed with Marshall-Palmer Z-R relationship (a=200, b=1.6) and Ground Clutter Removal (dBZ > 65)"
    }
