"""
RainGuard AI - FastAPI Backend

SIH26071:
AI/ML-Based Integrated Heavy Rainfall Early Warning
and Inundation Prediction System.

Current capabilities:
- Live weather prototype using Open-Meteo
- Flood/runoff prediction
- Flood risk classification
- CAP-oriented JSON alert
- CAP 1.2 XML generation
- Synthetic flood demonstration

Official IMD/MOSDAC satellite, radar, AWS/ARG and NWP
connections remain pending configuration/access.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.alerts.cap_generator import CAPGenerator
from app.alerts.risk_classifier import FloodRiskClassifier
from app.data_sources.weather import get_weather
from app.flood.flood_pipeline import RainGuardFloodPipeline


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="RainGuard AI",
    description=(
        "AI/ML-based heavy rainfall early warning and "
        "flood inundation prediction API for SIH26071."
    ),
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SHARED SERVICES
# ============================================================

flood_pipeline = RainGuardFloodPipeline()

risk_classifier = FloodRiskClassifier()

cap_generator = CAPGenerator()


# ============================================================
# REQUEST MODELS
# ============================================================

class FloodPredictionRequest(BaseModel):
    rainfall_mm: list[list[float]] = Field(
        ...,
        description="Rainfall grid in millimetres.",
    )

    lulc: list[list[int]] = Field(
        ...,
        description=(
            "LULC grid. "
            "1=Water, 2=Forest, 3=Vegetation, "
            "4=Agriculture, 5=Barren/Open, "
            "6=Built-up, 7=Wetland."
        ),
    )

    dem: list[list[float]] = Field(
        ...,
        description="DEM elevation grid.",
    )

    drainage_capacity_mm: list[list[float]] | None = Field(
        default=None,
        description="Optional drainage capacity grid in mm.",
    )

    area_name: str = Field(
        default="Chennai",
        description="Geographical area represented by the grid.",
    )


# ============================================================
# JSON SERIALIZATION HELPER
# ============================================================

def _json_safe(value: Any) -> Any:
    """
    Convert NumPy values into JSON-safe Python values.
    """

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _json_safe(item)
            for item in value
        ]

    return value


# ============================================================
# GRID VALIDATION
# ============================================================

def _prepare_grids(
    rainfall_mm: list[list[float]],
    lulc: list[list[int]],
    dem: list[list[float]],
    drainage_capacity_mm: list[list[float]] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Convert incoming grids to NumPy arrays and validate shapes.
    """

    rainfall = np.asarray(
        rainfall_mm,
        dtype=float,
    )

    lulc_array = np.asarray(
        lulc,
        dtype=int,
    )

    dem_array = np.asarray(
        dem,
        dtype=float,
    )

    drainage_array = None

    if drainage_capacity_mm is not None:
        drainage_array = np.asarray(
            drainage_capacity_mm,
            dtype=float,
        )

    if rainfall.ndim != 2:
        raise HTTPException(
            status_code=400,
            detail="rainfall_mm must be a 2D grid.",
        )

    if lulc_array.ndim != 2:
        raise HTTPException(
            status_code=400,
            detail="lulc must be a 2D grid.",
        )

    if dem_array.ndim != 2:
        raise HTTPException(
            status_code=400,
            detail="dem must be a 2D grid.",
        )

    if lulc_array.shape != rainfall.shape:
        raise HTTPException(
            status_code=400,
            detail=(
                "lulc must have the same shape "
                "as rainfall_mm."
            ),
        )

    if dem_array.shape != rainfall.shape:
        raise HTTPException(
            status_code=400,
            detail=(
                "dem must have the same shape "
                "as rainfall_mm."
            ),
        )

    if drainage_array is not None:
        if drainage_array.shape != rainfall.shape:
            raise HTTPException(
                status_code=400,
                detail=(
                    "drainage_capacity_mm must have "
                    "the same shape as rainfall_mm."
                ),
            )

    if not np.all(np.isfinite(rainfall)):
        raise HTTPException(
            status_code=400,
            detail="rainfall_mm contains non-finite values.",
        )

    if not np.all(np.isfinite(dem_array)):
        raise HTTPException(
            status_code=400,
            detail="dem contains non-finite values.",
        )

    if drainage_array is not None:
        if not np.all(np.isfinite(drainage_array)):
            raise HTTPException(
                status_code=400,
                detail=(
                    "drainage_capacity_mm contains "
                    "non-finite values."
                ),
            )

    if np.any(rainfall < 0):
        raise HTTPException(
            status_code=400,
            detail="rainfall_mm cannot contain negative values.",
        )

    if np.any(drainage_array < 0) if drainage_array is not None else False:
        raise HTTPException(
            status_code=400,
            detail=(
                "drainage_capacity_mm cannot contain "
                "negative values."
            ),
        )

    return (
        rainfall,
        lulc_array,
        dem_array,
        drainage_array,
    )


# ============================================================
# RISK + ALERT BUILDER
# ============================================================

def _build_risk_response(
    flood_result: dict[str, Any],
    area_name: str,
) -> dict[str, Any]:
    """
    Convert flood pipeline output into:

    1. RiskAssessment
    2. CAP-oriented JSON payload
    3. CAP 1.2 XML alert
    """

    # --------------------------------------------------------
    # Get flood depth from pipeline
    # --------------------------------------------------------

    flood_depth_m = np.asarray(
        flood_result["flood_depth_m"],
        dtype=float,
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # FloodRiskClassifier expects the flood depth raster.
    # Its classify() method creates the flood mask internally.
    # --------------------------------------------------------

    assessment = risk_classifier.classify(
        flood_depth_m=flood_depth_m,
    )

    # --------------------------------------------------------
    # CAP-oriented JSON metadata
    # --------------------------------------------------------

    cap_payload = risk_classifier.build_alert_payload(
        assessment=assessment,
        area_name=area_name,
    )

    # --------------------------------------------------------
    # Complete CAP XML
    # --------------------------------------------------------

    cap_xml = cap_generator.generate_from_assessment(
        assessment=assessment,
        area_name=area_name,
    )

    # --------------------------------------------------------
    # Risk summary
    # --------------------------------------------------------

    risk = {
        "alert_level": assessment.alert_level,
        "alert_code": int(assessment.alert_code),
        "risk_label": assessment.risk_label,

        "flooded_pixels": int(
            assessment.flooded_pixels
        ),

        "total_valid_pixels": int(
            assessment.total_valid_pixels
        ),

        "flooded_fraction": float(
            assessment.flooded_fraction
        ),

        "maximum_depth_m": float(
            assessment.maximum_depth_m
        ),

        "mean_flood_depth_m": float(
            assessment.mean_flood_depth_m
        ),

        "confidence": float(
            assessment.confidence
        ),
    }

    return {
        "risk": risk,
        "cap_payload": cap_payload,
        "cap_xml": cap_xml,
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health() -> dict[str, Any]:
    """
    Backend health check.
    """

    return {
        "status": "ok",
        "service": "RainGuard AI",
        "version": "0.3.0",
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
async def dashboard() -> dict[str, Any]:
    """
    Dashboard data.

    Open-Meteo is currently used as the live weather
    prototype. Official IMD/MOSDAC sources remain pending.
    """

    weather = None
    weather_status = "offline"

    try:
        weather = await get_weather()
        weather_status = "online"

    except Exception as exc:
        weather = {
            "error": str(exc),
        }

    return {
        "system": {
            "name": "RainGuard AI",
            "status": "operational",
            "mode": "prototype",
        },

        "location": {
            "name": "Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707,
        },

        "sources": {
            "weather": {
                "status": weather_status,
                "provider": "Open-Meteo",
                "type": "live prototype",
            },

            "aws": {
                "status": "pending",
                "provider": "IMD",
            },

            "arg": {
                "status": "pending",
                "provider": "IMD",
            },

            "nwp": {
                "status": "pending",
                "provider": "IMD/NWP",
            },

            "satellite": {
                "status": "pending",
                "provider": (
                    "MOSDAC / INSAT-3D / INSAT-3DR"
                ),
            },

            "radar": {
                "status": "pending",
                "provider": "IMD DWR",
            },
        },

        "weather": weather,

        "models": {
            "nowcasting": {
                "model": "ConvLSTM",
                "lead_time": "0-3h",
                "status": "architecture ready",
            },

            "nwp_postprocessing": {
                "model": (
                    "HistGradientBoostingRegressor"
                ),
                "lead_time": "3-72h",
                "status": "architecture ready",
            },

            "inundation": {
                "model": "SCS-CN + DEM + LULC",
                "status": "operational prototype",
            },
        },
    }


# ============================================================
# ALERTS
# ============================================================

@app.get("/api/alerts")
def alerts() -> dict[str, Any]:
    """
    Current alert feed.

    Live IMD warnings are not connected yet.
    """

    return {
        "status": "prototype",
        "active_alerts": [],
        "message": (
            "No live IMD warning feed is currently "
            "connected. RainGuard-generated flood alerts "
            "are available through the flood prediction API."
        ),
    }


# ============================================================
# AI ANALYST
# ============================================================

@app.get("/api/analyst")
def analyst() -> dict[str, Any]:
    """
    AI analyst summary for the command center.
    """

    return {
        "status": "prototype",

        "summary": (
            "RainGuard AI combines rainfall prediction, "
            "runoff modelling, terrain and land-use "
            "information to estimate flood inundation risk."
        ),

        "pipeline": [
            "Multi-source weather ingestion",
            "Data harmonization",
            "Radar and observation quality control",
            "0-3h ConvLSTM nowcasting",
            "3-72h NWP post-processing",
            "SCS-CN runoff estimation",
            "DEM/LULC flood modelling",
            "Flood risk classification",
            "CAP-oriented alert generation",
        ],
    }


# ============================================================
# FLOOD PREDICTION
# ============================================================

@app.post("/api/flood/predict")
def flood_predict(
    request: FloodPredictionRequest,
) -> dict[str, Any]:
    """
    Execute the complete flood prediction pipeline.
    """

    (
        rainfall,
        lulc,
        dem,
        drainage_capacity,
    ) = _prepare_grids(
        rainfall_mm=request.rainfall_mm,
        lulc=request.lulc,
        dem=request.dem,
        drainage_capacity_mm=(
            request.drainage_capacity_mm
        ),
    )

    try:
        flood_result = flood_pipeline.run(
            rainfall_mm=rainfall,
            lulc=lulc,
            dem=dem,
            drainage_capacity_mm=drainage_capacity,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Flood pipeline failed: {exc}",
        ) from exc

    try:
        risk_response = _build_risk_response(
            flood_result=flood_result,
            area_name=request.area_name,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Risk/alert generation failed: {exc}",
        ) from exc

    return {
        "status": "success",
        "mode": "prediction",

        "input": {
            "area_name": request.area_name,
            "grid_shape": list(rainfall.shape),
        },

        "flood": _json_safe(
            flood_result
        ),

        "risk": risk_response["risk"],

        "cap_payload": _json_safe(
            risk_response["cap_payload"]
        ),

        "cap_xml": risk_response["cap_xml"],
    }


# ============================================================
# FLOOD DEMO
# ============================================================

@app.get("/api/flood/demo")
def flood_demo() -> dict[str, Any]:
    """
    Deterministic synthetic flood demonstration.

    This endpoint tests the complete:

        Rainfall
            ↓
        LULC → Curve Number
            ↓
        SCS-CN runoff
            ↓
        DEM + drainage
            ↓
        Flood depth
            ↓
        Risk classification
            ↓
        CAP JSON + XML

    This is NOT a real-time flood forecast.
    """

    # --------------------------------------------------------
    # Synthetic rainfall
    # --------------------------------------------------------

    rainfall = np.array(
        [
            [20, 35, 45, 25],
            [40, 80, 120, 60],
            [55, 100, 180, 90],
            [30, 70, 110, 50],
        ],
        dtype=float,
    )

    # --------------------------------------------------------
    # Synthetic LULC
    # --------------------------------------------------------

    lulc = np.array(
        [
            [3, 3, 4, 4],
            [3, 6, 6, 4],
            [4, 6, 6, 6],
            [3, 4, 6, 3],
        ],
        dtype=int,
    )

    # --------------------------------------------------------
    # Synthetic DEM
    #
    # Lower elevation = lower terrain.
    # --------------------------------------------------------

    dem = np.array(
        [
            [18, 17, 16, 18],
            [15, 12, 10, 15],
            [13, 8, 5, 11],
            [17, 14, 10, 16],
        ],
        dtype=float,
    )

    # --------------------------------------------------------
    # Synthetic drainage capacity
    # --------------------------------------------------------

    drainage_capacity = np.array(
        [
            [8, 8, 10, 8],
            [8, 10, 12, 8],
            [8, 12, 15, 10],
            [8, 8, 10, 8],
        ],
        dtype=float,
    )

    try:
        flood_result = flood_pipeline.run(
            rainfall_mm=rainfall,
            lulc=lulc,
            dem=dem,
            drainage_capacity_mm=drainage_capacity,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Flood demo pipeline failed: {exc}",
        ) from exc

    try:
        risk_response = _build_risk_response(
            flood_result=flood_result,
            area_name="Chennai Synthetic Demo",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Flood demo risk generation failed: {exc}",
        ) from exc

    return {
        "status": "success",

        "mode": "synthetic_demo",

        "warning": (
            "Synthetic demonstration only. "
            "This is not a real-time flood forecast."
        ),

        "area_name": "Chennai Synthetic Demo",

        "inputs": {
            "rainfall_mm": rainfall.tolist(),
            "lulc": lulc.tolist(),
            "dem": dem.tolist(),
            "drainage_capacity_mm": (
                drainage_capacity.tolist()
            ),
        },

        "flood": _json_safe(
            flood_result
        ),

        "risk": risk_response["risk"],

        "cap_payload": _json_safe(
            risk_response["cap_payload"]
        ),

        "cap_xml": risk_response["cap_xml"],
    }


# ============================================================
# FLOOD RISK
# ============================================================

@app.post("/api/flood/risk")
def flood_risk(
    request: FloodPredictionRequest,
) -> dict[str, Any]:
    """
    Run the flood pipeline and return only
    the risk and alert products.
    """

    (
        rainfall,
        lulc,
        dem,
        drainage_capacity,
    ) = _prepare_grids(
        rainfall_mm=request.rainfall_mm,
        lulc=request.lulc,
        dem=request.dem,
        drainage_capacity_mm=(
            request.drainage_capacity_mm
        ),
    )

    try:
        flood_result = flood_pipeline.run(
            rainfall_mm=rainfall,
            lulc=lulc,
            dem=dem,
            drainage_capacity_mm=drainage_capacity,
        )

        risk_response = _build_risk_response(
            flood_result=flood_result,
            area_name=request.area_name,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction failed: {exc}",
        ) from exc

    return {
        "status": "success",

        "area_name": request.area_name,

        "risk": risk_response["risk"],

        "cap_payload": _json_safe(
            risk_response["cap_payload"]
        ),

        "cap_xml": risk_response["cap_xml"],
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> dict[str, Any]:
    """
    API overview.
    """

    return {
        "name": "RainGuard AI",
        "project": "SIH26071",
        "version": "0.3.0",
        "status": "operational",

        "endpoints": {
            "health": "/api/health",
            "dashboard": "/api/dashboard",
            "alerts": "/api/alerts",
            "analyst": "/api/analyst",
            "flood_demo": "/api/flood/demo",
            "flood_predict": "/api/flood/predict",
            "flood_risk": "/api/flood/risk",
            "docs": "/docs",
        },
    }