from datetime import datetime, timezone
from typing import Any
import requests


IMD_BASE_URL = "https://api.imd.gov.in/api/v1"

TAMIL_NADU_STATE_ID = 25

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707


def _fetch_json(url: str, timeout: int = 15) -> Any:
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "VARSHAAI/1.0",
            "Accept": "application/json",
        },
    )

    response.raise_for_status()
    return response.json()


def _extract_records(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in ("data", "results", "records"):
            value = payload.get(key)

            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        return [payload]

    return []


def _to_float(value):
    try:
        if value is None:
            return None

        return float(str(value).strip())

    except (TypeError, ValueError):
        return None


def _normalise_station(record: dict) -> dict:
    latitude = _to_float(
        record.get("Latitude")
        or record.get("latitude")
        or record.get("LAT")
    )

    longitude = _to_float(
        record.get("Longitude")
        or record.get("longitude")
        or record.get("LON")
    )

    return {
        "station_id": record.get("ID"),
        "call_sign": record.get("CALL_SIGN"),
        "station": record.get("STATION"),
        "district": record.get("DISTRICT"),
        "state": record.get("STATE"),
        "date": record.get("DATE"),
        "time": record.get("TIME"),
        "temperature_c": _to_float(record.get("CURR_TEMP")),
        "dew_point_c": _to_float(record.get("DEW_POINT_TEMP")),
        "relative_humidity_percent": _to_float(record.get("RH")),
        "wind_direction_deg": _to_float(record.get("WIND_DIRECTION")),
        "wind_speed_kmph": _to_float(record.get("WIND_SPEED")),
        "mslp_hpa": _to_float(record.get("MSLP")),
        "latitude": latitude,
        "longitude": longitude,
        "weather_code": record.get("WEATHER_CODE"),
        "nebulosity": _to_float(record.get("NEBULOSITY")),
        "feel_like_c": _to_float(record.get("Feel Like")),
        "raw": record,
    }


def fetch_tamil_nadu_observations() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()

    url = (
        f"{IMD_BASE_URL}/aws_data"
        f"?sid={TAMIL_NADU_STATE_ID}"
    )

    try:
        payload = _fetch_json(url)

        records = [
            _normalise_station(item)
            for item in _extract_records(payload)
        ]

        return {
            "status": "connected",
            "source": "India Meteorological Department",
            "network": "AWS/ARG",
            "state": "Tamil Nadu",
            "state_id": TAMIL_NADU_STATE_ID,
            "checked_at_utc": checked_at,
            "total_records": len(records),
            "observations": records,
            "endpoint": url,
            "access_note": (
                "Official IMD AWS/ARG API. "
                "Access may require public-IP whitelisting."
            ),
        }

    except requests.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        return {
            "status": "access_pending",
            "source": "India Meteorological Department",
            "network": "AWS/ARG",
            "state": "Tamil Nadu",
            "state_id": TAMIL_NADU_STATE_ID,
            "checked_at_utc": checked_at,
            "total_records": 0,
            "observations": [],
            "http_status": status_code,
            "error": str(exc),
            "endpoint": url,
            "access_note": (
                "IMD AWS/ARG endpoint is documented, "
                "but access may require public-IP whitelisting."
            ),
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "source": "India Meteorological Department",
            "network": "AWS/ARG",
            "state": "Tamil Nadu",
            "state_id": TAMIL_NADU_STATE_ID,
            "checked_at_utc": checked_at,
            "total_records": 0,
            "observations": [],
            "error": str(exc),
            "endpoint": url,
        }


def _distance_squared(lat, lon):
    if lat is None or lon is None:
        return float("inf")

    return (
        (lat - CHENNAI_LAT) ** 2
        + (lon - CHENNAI_LON) ** 2
    )


def get_chennai_observations() -> dict:
    result = fetch_tamil_nadu_observations()

    observations = result.get("observations", [])

    nearby = sorted(
        observations,
        key=lambda item: _distance_squared(
            item.get("latitude"),
            item.get("longitude"),
        ),
    )

    result["chennai"] = nearby[:20]

    if nearby:
        result["nearest_station"] = nearby[0]

    return result


def get_observation_status() -> dict:
    result = fetch_tamil_nadu_observations()

    return {
        "status": result.get("status"),
        "source": result.get("source"),
        "network": result.get("network"),
        "state": result.get("state"),
        "state_id": result.get("state_id"),
        "checked_at_utc": result.get("checked_at_utc"),
        "total_records": result.get("total_records", 0),
        "http_status": result.get("http_status"),
        "error": result.get("error"),
        "access_note": result.get("access_note"),
    }