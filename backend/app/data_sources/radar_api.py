from fastapi import APIRouter

from .radar_service import (
    get_chennai_radar_products,
    get_chennai_radar_status,
)

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
