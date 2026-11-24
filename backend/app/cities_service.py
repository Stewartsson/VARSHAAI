from typing import Any
import numpy as np
from .data_sources.weather import get_weather, _get_baseline_weather

CITIES_METADATA = {
    "chennai": {
        "id": "chennai",
        "name": "Chennai",
        "state": "Tamil Nadu",
        "lat": 13.0827,
        "lon": 80.2707,
        "radar": {
            "name": "DWR Chennai (Sriharikota / NIOT)",
            "station_code": "VOMM_DWR",
            "band": "S-Band (2.8 GHz)",
            "range_km": 250,
            "scan_interval_min": 10,
            "status": "OPERATIONAL",
            "provider": "IMD / ISRO",
        },
        "terrain_elevation_m": 6.7,
        "drainage_basins": ["Cooum River", "Adyar River", "Kosasthalaiyar", "Buckingham Canal"],
        "hotspots": [
            {"name": "Velachery Basin", "lat": 12.9815, "lon": 80.2180, "type": "Low-Lying Lake Basin", "risk": "High"},
            {"name": "Madipakkam", "lat": 12.9647, "lon": 80.1961, "type": "Drainage Overflow", "risk": "Medium"},
            {"name": "Mudichur", "lat": 12.9150, "lon": 80.0650, "type": "Riverine Backwater", "risk": "Severe"},
            {"name": "Vyasarpadi Subway", "lat": 13.1167, "lon": 80.2611, "type": "Railway Underpass", "risk": "Critical"},
        ],
    },
    "mumbai": {
        "id": "mumbai",
        "name": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.0760,
        "lon": 72.8777,
        "radar": {
            "name": "DWR Mumbai (Colaba & Veravali Dual-Pol)",
            "station_code": "VABB_DWR",
            "band": "S-Band Dual Polarimetric",
            "range_km": 250,
            "scan_interval_min": 10,
            "status": "OPERATIONAL",
            "provider": "IMD",
        },
        "terrain_elevation_m": 8.0,
        "drainage_basins": ["Mithi River", "Poisar River", "Dahisar River", "Mahim Creek"],
        "hotspots": [
            {"name": "Milan Subway (Santacruz)", "lat": 19.0880, "lon": 72.8420, "type": "Chronic Underpass Inundation", "risk": "Critical"},
            {"name": "Hindmata (Dadar)", "lat": 19.0178, "lon": 72.8478, "type": "Tidal Lockage Basin", "risk": "Severe"},
            {"name": "Kurla West (Mithi River)", "lat": 19.0700, "lon": 72.8800, "type": "River Overflow Corridor", "risk": "Critical"},
            {"name": "Andheri Subway", "lat": 19.1197, "lon": 72.8464, "type": "Stormwater Bottleneck", "risk": "High"},
        ],
    },
    "delhi": {
        "id": "delhi",
        "name": "Delhi (NCR)",
        "state": "National Capital Territory",
        "lat": 28.6139,
        "lon": 77.2090,
        "radar": {
            "name": "DWR Delhi (Palam & Mausam Bhavan)",
            "station_code": "VIDP_DWR",
            "band": "C-Band Doppler (5.6 GHz)",
            "range_km": 250,
            "scan_interval_min": 10,
            "status": "OPERATIONAL",
            "provider": "IMD",
        },
        "terrain_elevation_m": 216.0,
        "drainage_basins": ["Yamuna River", "Najafgarh Drain", "Barapullah Basin", "Shahdara Drain"],
        "hotspots": [
            {"name": "Yamuna Floodplain (ITO)", "lat": 28.6289, "lon": 77.2489, "type": "River Floodplain Inflow", "risk": "High"},
            {"name": "Minto Bridge Underpass", "lat": 28.6340, "lon": 77.2240, "type": "Severe Water Submersion", "risk": "Critical"},
            {"name": "Kashmere Gate ISBT", "lat": 28.6670, "lon": 77.2330, "type": "Low Elevation Depression", "risk": "High"},
            {"name": "Pul Prahladpur Underpass", "lat": 28.5040, "lon": 77.2880, "type": "Transit Chokepoint", "risk": "Medium"},
        ],
    },
    "hyderabad": {
        "id": "hyderabad",
        "name": "Hyderabad",
        "state": "Telangana",
        "lat": 17.3850,
        "lon": 78.4867,
        "radar": {
            "name": "DWR Hyderabad (Begumpet Airport)",
            "station_code": "VOHY_DWR",
            "band": "C-Band Polarimetric Radar",
            "range_km": 250,
            "scan_interval_min": 10,
            "status": "OPERATIONAL",
            "provider": "IMD",
        },
        "terrain_elevation_m": 542.0,
        "drainage_basins": ["Musi River", "Hussain Sagar Lake Basin", "Kukatpally Nala"],
        "hotspots": [
            {"name": "Begumpet Underpass", "lat": 17.4440, "lon": 78.4680, "type": "Railway Submersion", "risk": "High"},
            {"name": "Nadeem Colony (Tolichowki)", "lat": 17.4020, "lon": 78.4060, "type": "Lake Backflow Inundation", "risk": "Severe"},
            {"name": "Moosarambagh Bridge (Musi)", "lat": 17.3750, "lon": 78.5120, "type": "Flash River Surge", "risk": "Severe"},
            {"name": "Alwal Lowlands", "lat": 17.5020, "lon": 78.5180, "type": "Storm Runoff Basin", "risk": "Medium"},
        ],
    },
    "kolkata": {
        "id": "kolkata",
        "name": "Kolkata",
        "state": "West Bengal",
        "lat": 22.5726,
        "lon": 88.3639,
        "radar": {
            "name": "DWR Kolkata (New Town Rajarhat)",
            "station_code": "VECC_DWR",
            "band": "S-Band Cyclone & Weather Radar",
            "range_km": 400,
            "scan_interval_min": 10,
            "status": "OPERATIONAL",
            "provider": "IMD",
        },
        "terrain_elevation_m": 9.0,
        "drainage_basins": ["Hooghly River", "East Kolkata Wetlands", "Adi Ganga Canal"],
        "hotspots": [
            {"name": "Thanthania Kalibari", "lat": 22.5810, "lon": 88.3660, "type": "High Chronic Inundation", "risk": "Critical"},
            {"name": "Park Circus 7-Point", "lat": 22.5430, "lon": 88.3670, "type": "Low-Elevation Arterial", "risk": "High"},
            {"name": "Kalighat Ghat Corridor", "lat": 22.5200, "lon": 88.3450, "type": "Hooghly Tidal Lockage", "risk": "Severe"},
            {"name": "Behala Chowrasta", "lat": 22.4980, "lon": 88.3140, "type": "Suburban Waterlogging", "risk": "High"},
        ],
    },
}


def _calculate_city_risk(precipitation_mm: float) -> dict[str, Any]:
    """Calculate flood risk classification based on precipitation."""
    p = float(precipitation_mm)
    if p >= 64.5:
        return {
            "level": "ORANGE",
            "code": 2,
            "label": "Flood Warning / Severe Rainfall",
            "max_depth_m": round(0.15 + (p - 64.5) * 0.005, 2),
            "flooded_fraction": round(min(0.75, 0.25 + (p - 64.5) * 0.01), 2),
            "confidence": 0.88,
        }
    elif p >= 15.5:
        return {
            "level": "YELLOW",
            "code": 1,
            "label": "Flood Watch / Be Prepared",
            "max_depth_m": round(0.04 + (p - 15.5) * 0.002, 2),
            "flooded_fraction": 0.08,
            "confidence": 0.82,
        }
    else:
        return {
            "level": "GREEN",
            "code": 0,
            "label": "Normal / No Significant Flood Risk",
            "max_depth_m": 0.0,
            "flooded_fraction": 0.0,
            "confidence": 0.94,
        }


async def get_all_cities_summary() -> list[dict[str, Any]]:
    """Return live summary of all 5 major metros."""
    results = []

    for city_id, meta in CITIES_METADATA.items():
        try:
            weather = await get_weather(meta["lat"], meta["lon"])
            current = weather.get("current", {})
            hourly = weather.get("hourly", {})

            current_p = float(current.get("precipitation") or 0.0)
            hourly_p = hourly.get("precipitation", [])
            max_3h_p = max([float(x or 0.0) for x in hourly_p[:3]]) if hourly_p else 0.0
            effective_rain = max(current_p, max_3h_p)

            risk_eval = _calculate_city_risk(effective_rain)

            results.append({
                "id": city_id,
                "name": meta["name"],
                "state": meta["state"],
                "lat": meta["lat"],
                "lon": meta["lon"],
                "radar_name": meta["radar"]["name"],
                "radar_band": meta["radar"]["band"],
                "radar_status": meta["radar"]["status"],
                "current_weather": {
                    "temperature_c": current.get("temperature_2m"),
                    "humidity_percent": current.get("relative_humidity_2m"),
                    "precipitation_mm": current_p,
                    "rain_mm": current.get("rain", 0.0),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                    "pressure_hpa": current.get("surface_pressure"),
                    "observed_at": current.get("time"),
                },
                "risk": risk_eval,
                "hotspot_count": len(meta["hotspots"]),
            })
        except Exception:
            # Fallback safe with coordinate-matched city baseline
            fallback_w = _get_baseline_weather(meta["lat"], meta["lon"])
            cur_fb = fallback_w.get("current", {})
            results.append({
                "id": city_id,
                "name": meta["name"],
                "state": meta["state"],
                "lat": meta["lat"],
                "lon": meta["lon"],
                "radar_name": meta["radar"]["name"],
                "radar_band": meta["radar"]["band"],
                "radar_status": meta["radar"]["status"],
                "current_weather": {
                    "temperature_c": cur_fb.get("temperature_2m", 26.0),
                    "humidity_percent": cur_fb.get("relative_humidity_2m", 60),
                    "precipitation_mm": cur_fb.get("precipitation", 0.0),
                    "rain_mm": cur_fb.get("rain", 0.0),
                    "wind_speed_kmh": cur_fb.get("wind_speed_10m", 10.0),
                    "pressure_hpa": cur_fb.get("surface_pressure", 1013.0),
                    "observed_at": cur_fb.get("time"),
                },
                "risk": _calculate_city_risk(cur_fb.get("precipitation", 0.0)),
                "hotspot_count": len(meta["hotspots"]),
            })

    return results


async def get_city_detail(city_id: str) -> dict[str, Any]:
    """Return comprehensive deep-dive metrics, 48h timeline, and radar specs for a specific city."""
    if city_id not in CITIES_METADATA:
        city_id = "chennai"

    meta = CITIES_METADATA[city_id]
    weather = await get_weather(meta["lat"], meta["lon"])
    current = weather.get("current", {})
    hourly = weather.get("hourly", {})

    current_p = float(current.get("precipitation") or 0.0)
    current_r = float(current.get("rain") or 0.0)
    current_s = float(current.get("showers") or 0.0)
    eff_val = float(current.get("effective_rainfall_mm") or 0.0)
    hourly_p = hourly.get("precipitation", [])
    hourly_time = hourly.get("time", [])
    hourly_temp = hourly.get("temperature_2m", [])

    timeline = []
    for i in range(min(48, len(hourly_time))):
        timeline.append({
            "time_iso": hourly_time[i],
            "precipitation_mm": round(float(hourly_p[i] or 0.0), 2) if i < len(hourly_p) else 0.0,
            "temperature_c": round(float(hourly_temp[i] or 28.0), 1) if i < len(hourly_temp) else 28.0,
        })

    max_rain_48h = max([t["precipitation_mm"] for t in timeline]) if timeline else 0.0
    effective_rain = round(max(eff_val, current_p, current_r + current_s, max_rain_48h), 2)
    risk_eval = _calculate_city_risk(effective_rain)

    return {
        "status": "success",
        "city": meta,
        "current_weather": {
            "temperature_c": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": round(max(eff_val, current_p, current_r + current_s), 2),
            "rain_mm": current.get("rain", 0.0),
            "showers_mm": current.get("showers", 0.0),
            "weather_code": current.get("weather_code"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "pressure_hpa": current.get("surface_pressure"),
            "observed_at": current.get("time"),
        },
        "risk": risk_eval,
        "timeline_48h": timeline,
        "max_rain_48h_mm": max_rain_48h,
        "hotspots": meta["hotspots"],
        "drainage_basins": meta["drainage_basins"],
        "radar": meta["radar"],
    }
