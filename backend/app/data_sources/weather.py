import httpx


CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707


async def get_weather():
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

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    return data