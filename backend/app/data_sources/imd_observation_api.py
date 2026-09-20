from fastapi import APIRouter

from .imd_observations import (
    get_observation_status,
    fetch_tamil_nadu_observations,
    get_chennai_observations,
)


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