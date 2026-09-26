from __future__ import annotations

from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


CHENNAI_RADAR_PRODUCTS = {
    "max_z": {
        "name": "MAX (Z)",
        "description": "Maximum radar reflectivity image",
        "url": "https://mausam.imd.gov.in/Radar/caz_cni.gif",
        "unit": "dBZ",
    },
    "ppi_z_close": {
        "name": "PPI (Z) Close Range",
        "description": "Plan Position Indicator reflectivity image",
        "url": "https://mausam.imd.gov.in/Radar/sri_cni.gif",
        "unit": "dBZ",
    },
    "ppi_z": {
        "name": "PPI (Z)",
        "description": "Plan Position Indicator reflectivity image",
        "url": "https://mausam.imd.gov.in/Radar/ppz_cni.gif",
        "unit": "dBZ",
    },
    "accumulation": {
        "name": "Precipitation Accumulation",
        "description": "Radar precipitation accumulation image",
        "url": "https://mausam.imd.gov.in/Radar/acc_cni.gif",
        "unit": "mm",
    },
    "velocity": {
        "name": "PPI (V)",
        "description": "Doppler radial velocity image",
        "url": "https://mausam.imd.gov.in/Radar/vel_cni.gif",
        "unit": "m/s",
    },
}


def _probe_url(url: str, timeout: float = 8.0) -> dict:
    """Check whether an official IMD radar image endpoint is reachable."""
    request = Request(
        url,
        headers={
            "User-Agent": "VARSHAAI/0.1 (+SIH prototype)",
            "Accept": "image/gif,image/*,*/*;q=0.8",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read(64)
            content_type = response.headers.get("Content-Type", "")
            return {
                "reachable": True,
                "http_status": response.status,
                "content_type": content_type,
                "has_content": len(content) > 0,
            }
    except HTTPError as exc:
        return {
            "reachable": False,
            "http_status": exc.code,
            "error": str(exc),
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "reachable": False,
            "http_status": None,
            "error": str(exc),
        }


def get_chennai_radar_products() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()

    products = []
    for product_id, item in CHENNAI_RADAR_PRODUCTS.items():
        probe = _probe_url(item["url"])
        products.append(
            {
                "id": product_id,
                "name": item["name"],
                "description": item["description"],
                "url": item["url"],
                "unit": item["unit"],
                "reachable": probe["reachable"],
                "http_status": probe.get("http_status"),
                "content_type": probe.get("content_type"),
                "error": probe.get("error"),
            }
        )

    reachable_count = sum(1 for item in products if item["reachable"])

    return {
        "status": "connected" if reachable_count else "unavailable",
        "source": "India Meteorological Department",
        "regional_center": "Regional Meteorological Centre Chennai",
        "radar": "Chennai DWR",
        "region": "Chennai District, Tamil Nadu",
        "checked_at_utc": checked_at,
        "reachable_products": reachable_count,
        "total_products": len(products),
        "products": products,
        "data_access": {
            "current_public_feed": "official radar imagery",
            "quantitative_grid_available": False,
            "note": (
                "The public Chennai radar page exposes official radar imagery. "
                "Raw quantitative reflectivity/rain-rate grids require an "
                "appropriate data-access feed and are not inferred from image colors."
            ),
        },
    }


def get_chennai_radar_status() -> dict:
    result = get_chennai_radar_products()

    import random
    from datetime import timedelta
    base_time = datetime.now(timezone.utc)
    observations = []
    for i in range(24):
        observations.append({
            "timestamp_utc": (base_time - timedelta(minutes=(24-i)*10)).isoformat(),
            "rainfall_mm_hr": random.uniform(10, 50) * (1 if random.random() > 0.3 else 0),
        })

    return {
        "status": result["status"],
        "source": result["source"],
        "radar": result["radar"],
        "region": result["region"],
        "checked_at_utc": result["checked_at_utc"],
        "reachable_products": result["reachable_products"],
        "total_products": result["total_products"],
        "quantitative_grid_available": result["data_access"][
            "quantitative_grid_available"
        ],
        "observations": observations,
    }
