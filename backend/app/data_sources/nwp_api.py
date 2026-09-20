from fastapi import APIRouter

from .nwp_service import fetch_chennai_gfs, get_gfs_status


router = APIRouter(
    prefix="/api/nwp",
    tags=["NWP"],
)


@router.get("/status")
def nwp_status():
    return get_gfs_status()


@router.get("/chennai")
def nwp_chennai():
    return fetch_chennai_gfs()


@router.get("/forecast")
def nwp_forecast():
    result = fetch_chennai_gfs()

    return {
        "status": result.get("status"),
        "source": result.get("source"),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "region": result.get("region"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "checked_at_utc": result.get("checked_at_utc"),
        "forecast_horizon_hours": result.get("forecast_horizon_hours"),
        "observation_count": result.get("observation_count", 0),
        "observations": result.get("observations", []),
        "model_metadata": result.get("model_metadata"),
        "postprocessing": result.get("postprocessing"),
        "error": result.get("error"),
    }
