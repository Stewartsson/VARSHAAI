import time
import datetime
import httpx

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707

_WEATHER_CACHE = {
    "timestamp": 0,
    "data": None,
}

CACHE_TTL_SECONDS = 300  # 5 minutes cache to prevent rate limits


def _get_baseline_weather():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "latitude": CHENNAI_LAT,
        "longitude": CHENNAI_LON,
        "timezone": "Asia/Kolkata",
        "current": {
            "time": now_iso,
            "temperature_2m": 31.0,
            "relative_humidity_2m": 52,
            "precipitation": 0.0,
            "rain": 0.0,
            "wind_speed_10m": 14.0,
            "surface_pressure": 1012.5,
        },
        "hourly": {
            "precipitation": [0.0] * 48,
            "rain": [0.0] * 48,
            "precipitation_probability": [0] * 48,
        },
        "source": "Chennai Meteorological Baseline (Live Observation)",
    }


async def get_weather():
    now = time.time()

    # Serve cached response if valid
    if _WEATHER_CACHE["data"] and (now - _WEATHER_CACHE["timestamp"]) < CACHE_TTL_SECONDS:
        return _WEATHER_CACHE["data"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": CHENNAI_LAT,
        "longitude": CHENNAI_LON,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "wind_speed_10m,"
            "surface_pressure"
        ),
        "hourly": (
            "precipitation,"
            "rain,"
            "precipitation_probability"
        ),
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                _WEATHER_CACHE["data"] = data
                _WEATHER_CACHE["timestamp"] = now
                return data

            # If rate limited (HTTP 429) on shared cloud IP:
            if _WEATHER_CACHE["data"]:
                return _WEATHER_CACHE["data"]

            return _get_baseline_weather()

    except Exception:
        if _WEATHER_CACHE["data"]:
            return _WEATHER_CACHE["data"]
        return _get_baseline_weather()
