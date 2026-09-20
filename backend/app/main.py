"""
RainGuard AI
Integrated Heavy Rainfall Early Warning and Inundation Prediction System

SIH Problem Statement: SIH26071

Current implementation:
- Live weather prototype
- Multi-source ingestion status
- Historical validation API
- SCS-CN runoff screening
- DEM/LULC flood screening
- Flood risk classification
- CAP-oriented alert generation
- Dashboard API
- Analyst API

Important:
Official IMD/MOSDAC live satellite, radar, AWS, ARG and NWP feeds
remain pending until their approved access/configuration is available.
The current live weather prototype uses Open-Meteo.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .data_sources.weather import get_weather
from .alerts.risk_classifier import FloodRiskClassifier
from .alerts.cap_generator import CAPGenerator
from .data_sources.mosdac.hem_api import router as hem_router
from .data_sources.mosdac.timeseries_api import router as hem_timeseries_router
from .data_sources.radar_api import router as radar_router
from .data_sources.imd_observation_api import router as imd_observation_router
from .data_sources.nwp_api import router as nwp_router
from .nwp_ml_api import router as nwp_ml_router


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="RainGuard AI API",
    version="0.3.0",
    description=(
        "AI/ML-based integrated heavy rainfall early warning "
        "and inundation prediction prototype."
    ),
)

# MOSDAC INSAT-3DR HEM satellite API
app.include_router(hem_router)
app.include_router(hem_timeseries_router)
app.include_router(radar_router)
app.include_router(imd_observation_router)
app.include_router(nwp_router)
app.include_router(nwp_ml_router)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

HISTORICAL_DIR = (
    PROJECT_ROOT
    / "data"
    / "historical"
)


# ============================================================
# GLOBAL ENGINES
# ============================================================

risk_classifier = FloodRiskClassifier()

cap_generator = CAPGenerator()


# ============================================================
# CONSTANTS
# ============================================================

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707

COMMON_GRID_RESOLUTION_KM = 4.0
COMMON_TIMESTEP_MINUTES = 30

FLOOD_THRESHOLD_M = 0.05


# ============================================================
# JSON SAFETY
# ============================================================

def _json_safe(value: Any) -> Any:
    """
    Convert NumPy / dataclass values into JSON-safe values.
    """

    if value is None:
        return None

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if hasattr(value, "__dataclass_fields__"):
        return {
            key: _json_safe(val)
            for key, val in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): _json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

    return value


# ============================================================
# HISTORICAL CSV HELPER
# ============================================================

def _read_csv_rows(filename: str) -> list[dict[str, Any]]:
    """
    Read a historical CSV from data/historical.

    Missing files return an empty list rather than crashing
    the live dashboard.
    """

    path = HISTORICAL_DIR / filename

    if not path.exists():
        return []

    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(file)

            return [
                dict(row)
                for row in reader
            ]

    except (
        OSError,
        csv.Error,
    ):
        return []


# ============================================================
# NUMBER HELPERS
# ============================================================

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (
        TypeError,
        ValueError,
    ):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# SCS-CN RUNOFF
# ============================================================

def _scs_cn_runoff(
    rainfall_mm: np.ndarray,
    curve_number: np.ndarray,
) -> np.ndarray:
    """
    Standard SCS Curve Number runoff equation.

    S = 25400 / CN - 254

    Ia = 0.2S

    Q = (P - Ia)^2 / (P + 0.8S)

    where:
        P  = rainfall in mm
        Q  = runoff in mm
    """

    rainfall = np.asarray(
        rainfall_mm,
        dtype=float,
    )

    cn = np.asarray(
        curve_number,
        dtype=float,
    )

    if rainfall.shape != cn.shape:
        raise ValueError(
            "rainfall and curve_number "
            "must have the same shape."
        )

    cn = np.clip(
        cn,
        1.0,
        100.0,
    )

    storage = (
        25400.0 / cn
    ) - 254.0

    initial_abstraction = (
        0.2 * storage
    )

    runoff = np.zeros_like(
        rainfall,
        dtype=float,
    )

    valid = (
        np.isfinite(rainfall)
        & np.isfinite(cn)
    )

    rainfall_valid = rainfall[valid]
    storage_valid = storage[valid]
    abstraction_valid = (
        initial_abstraction[valid]
    )

    excess = (
        rainfall_valid
        > abstraction_valid
    )

    runoff_valid = np.zeros_like(
        rainfall_valid,
        dtype=float,
    )

    numerator = (
        rainfall_valid[excess]
        - abstraction_valid[excess]
    ) ** 2

    denominator = (
        rainfall_valid[excess]
        + 0.8
        * storage_valid[excess]
    )

    runoff_valid[excess] = (
        numerator
        / denominator
    )

    runoff[valid] = runoff_valid

    return runoff


# ============================================================
# LULC → CURVE NUMBER
# ============================================================

def _curve_number_from_lulc(
    lulc: np.ndarray,
) -> np.ndarray:
    """
    Prototype LULC to SCS-CN mapping.

    Classes:
        1 Water
        2 Forest
        3 Vegetation / Grassland
        4 Agriculture
        5 Barren / Open
        6 Built-up / Impervious
        7 Wetland
    """

    mapping = {
        1: 30.0,
        2: 55.0,
        3: 65.0,
        4: 75.0,
        5: 70.0,
        6: 95.0,
        7: 50.0,
    }

    result = np.full(
        np.asarray(lulc).shape,
        np.nan,
        dtype=float,
    )

    for class_id, cn in mapping.items():
        result[
            np.asarray(lulc) == class_id
        ] = cn

    return result


# ============================================================
# FLOOD DEPTH SCREENING
# ============================================================

def _calculate_flood_depth(
    runoff_mm: np.ndarray,
    dem_m: np.ndarray,
) -> np.ndarray:
    """
    Screening-level terrain-aware flood depth.

    This is not a replacement for HEC-RAS/LISFLOOD.
    It is a prototype inundation screening layer.
    """

    runoff = np.asarray(
        runoff_mm,
        dtype=float,
    )

    dem = np.asarray(
        dem_m,
        dtype=float,
    )

    if runoff.shape != dem.shape:
        raise ValueError(
            "runoff and DEM must have "
            "the same shape."
        )

    valid = (
        np.isfinite(runoff)
        & np.isfinite(dem)
    )

    depth_mm = np.full(
        runoff.shape,
        np.nan,
        dtype=float,
    )

    if not np.any(valid):
        return depth_mm

    valid_dem = dem[valid]

    dem_min = np.min(valid_dem)
    dem_max = np.max(valid_dem)

    if dem_max > dem_min:
        low_terrain = (
            dem_max
            - dem[valid]
        ) / (
            dem_max
            - dem_min
        )
    else:
        low_terrain = np.zeros_like(
            valid_dem
        )

    # Prototype drainage reduction.
    drainage_factor = 0.15

    # Small terrain amplification.
    terrain_factor = 0.05

    effective_runoff = (
        runoff[valid]
        * (1.0 - drainage_factor)
    )

    terrain_adjustment = (
        1.0
        + terrain_factor
        * low_terrain
    )

    depth_mm[valid] = (
        effective_runoff
        * terrain_adjustment
    )

    return depth_mm


# ============================================================
# INUNDATION MAP
# ============================================================

def _build_inundation_map(
    flood_depth_m: np.ndarray,
) -> dict[str, Any]:
    """
    Convert flood depth into extent and risk classes.
    """

    depth = np.asarray(
        flood_depth_m,
        dtype=float,
    )

    valid = np.isfinite(depth)

    flooded = (
        valid
        & (depth >= FLOOD_THRESHOLD_M)
    )

    risk_class = np.zeros(
        depth.shape,
        dtype=np.uint8,
    )

    risk_class[
        flooded
        & (depth < 0.15)
    ] = 1

    risk_class[
        flooded
        & (depth >= 0.15)
        & (depth < 0.30)
    ] = 2

    risk_class[
        flooded
        & (depth >= 0.30)
        & (depth < 0.60)
    ] = 3

    risk_class[
        flooded
        & (depth >= 0.60)
    ] = 4

    return {
        "flooded_mask": flooded.astype(
            np.uint8
        ),
        "risk_class": risk_class,
    }


# ============================================================
# DEMO FLOOD GRID
# ============================================================

def _demo_flood_grids() -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Deterministic demonstration grid.

    This is intentionally synthetic and is clearly labelled
    as demonstration data in the API response.
    """

    rainfall = np.array(
        [
            [95, 110, 125, 90],
            [100, 145, 180, 105],
            [85, 120, 155, 100],
            [70, 90, 115, 80],
        ],
        dtype=float,
    )

    dem = np.array(
        [
            [32, 28, 25, 31],
            [27, 20, 16, 26],
            [30, 23, 18, 28],
            [35, 30, 25, 33],
        ],
        dtype=float,
    )

    lulc = np.array(
        [
            [3, 4, 6, 3],
            [4, 6, 6, 4],
            [3, 6, 6, 3],
            [2, 3, 4, 2],
        ],
        dtype=int,
    )

    return (
        rainfall,
        dem,
        lulc,
    )


# ============================================================
# FLOOD RISK RESPONSE
# ============================================================

def _build_risk_response(
    flood_depth_m: np.ndarray,
    area_name: str = "Chennai",
) -> dict[str, Any]:

    assessment = risk_classifier.classify(
        flood_depth_m=flood_depth_m,
    )

    cap_payload = (
        risk_classifier.build_alert_payload(
            assessment=assessment,
            area_name=area_name,
        )
    )

    cap_xml = (
        cap_generator.generate_from_assessment(
            assessment=assessment,
            area_name=area_name,
        )
    )

    inundation = _build_inundation_map(
        flood_depth_m
    )

    return {
        "assessment": _json_safe(
            assessment
        ),

        "cap_payload": _json_safe(
            cap_payload
        ),

        "cap_xml": cap_xml,

        "inundation": {
            "flooded_mask": _json_safe(
                inundation[
                    "flooded_mask"
                ]
            ),
            "risk_class": _json_safe(
                inundation[
                    "risk_class"
                ]
            ),
        },
    }


# ============================================================
# FLOOD PREDICTION REQUEST
# ============================================================

class FloodPredictionRequest(BaseModel):
    """
    API request for flood prediction.

    Arrays are supplied as nested lists.
    """

    rainfall_mm: list[list[float]] = Field(
        ...,
        description="Rainfall grid in mm.",
    )

    dem_m: list[list[float]] = Field(
        ...,
        description="DEM grid in metres.",
    )

    lulc: list[list[int]] = Field(
        ...,
        description="LULC class grid.",
    )

    area_name: str = "Chennai"


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "RainGuard AI",
        "version": "0.3.0",
        "problem_statement": "SIH26071",
        "message": (
            "RainGuard AI disaster intelligence "
            "backend is running."
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "service": "RainGuard AI",
        "backend": "online",
        "version": "0.3.0",
        "timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
async def dashboard():

    try:
        weather = await get_weather()

    except Exception as error:

        weather = {
            "status": "unavailable",
            "error": str(error),
        }

    return {
        "status": "success",

        "location": {
            "name": "Chennai",
            "state": "Tamil Nadu",
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
        },

        "weather": weather,

        "system": {
            "backend": "online",

            "source_status": {
                "weather": "LIVE PROTOTYPE",
                "aws": "PENDING",
                "arg": "PENDING",
                "nwp": "PENDING",
                "satellite": "PENDING",
                "radar": "PENDING",
            },

            "harmonization": {
                "grid_resolution_km": (
                    COMMON_GRID_RESOLUTION_KM
                ),
                "timestep_minutes": (
                    COMMON_TIMESTEP_MINUTES
                ),
            },

            "models": {
                "nowcasting": (
                    "ConvLSTM / U-Net architecture ready"
                ),
                "nwp_postprocessing": (
                    "Gradient Boosting model ready"
                ),
                "flood_model": (
                    "SCS-CN + DEM/LULC screening"
                ),
            },
        },
    }


# ============================================================
# ALERTS
# ============================================================

@app.get("/api/alerts")
def alerts():

    return {
        "status": "success",

        "count": 0,

        "alerts": [],

        "message": (
            "No live IMD warning feed is currently "
            "connected. RainGuard-generated flood alerts "
            "are available through the flood prediction API."
        ),

        "source": "IMD warning feed",

        "source_status": "PENDING",
    }


# ============================================================
# ANALYST
# ============================================================

@app.get("/api/analyst")
def analyst():

    return {
        "status": "prototype",

        "summary": (
            "RainGuard AI combines rainfall prediction, "
            "runoff modelling, inundation mapping and "
            "risk classification for operational "
            "decision support."
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

        "model_horizons": {
            "nowcast": "0-3 hours",
            "nwp_blend": "3-72 hours",
        },

        "data_status": {
            "satellite": "PENDING",
            "radar": "PENDING",
            "aws": "PENDING",
            "arg": "PENDING",
            "nwp": "PENDING",
        },

        "note": (
            "ConvLSTM and NWP post-processing "
            "architectures are implemented, but final "
            "operational performance requires real "
            "high-frequency multi-source training data."
        ),
    }


# ============================================================
# FLOOD DEMONSTRATION
# ============================================================

@app.get("/api/flood/demo")
def flood_demo():

    rainfall, dem, lulc = (
        _demo_flood_grids()
    )

    curve_number = (
        _curve_number_from_lulc(
            lulc
        )
    )

    runoff = _scs_cn_runoff(
        rainfall_mm=rainfall,
        curve_number=curve_number,
    )

    flood_depth_mm = (
        _calculate_flood_depth(
            runoff_mm=runoff,
            dem_m=dem,
        )
    )

    flood_depth_m = (
        flood_depth_mm / 1000.0
    )

    risk_response = (
        _build_risk_response(
            flood_depth_m=flood_depth_m,
            area_name="Chennai",
        )
    )

    assessment = (
        risk_response["assessment"]
    )

    return {
        "status": "success",

        "demo": True,

        "warning": (
            "Synthetic flood demonstration only "
            "— not a real-time flood forecast."
        ),

        "area": "Chennai",

        "method": {
            "runoff": "SCS-CN",
            "terrain": "DEM screening",
            "land_use": "LULC-based curve number",
            "inundation": (
                "Terrain-aware screening model"
            ),
        },

        "input": {
            "rainfall_mm": _json_safe(
                rainfall
            ),
            "dem_m": _json_safe(
                dem
            ),
            "lulc": _json_safe(
                lulc
            ),
            "curve_number": _json_safe(
                curve_number
            ),
        },

        "runoff_mm": _json_safe(
            runoff
        ),

        "flood_depth_m": _json_safe(
            flood_depth_m
        ),

        "risk": assessment,

        "cap_payload": (
            risk_response[
                "cap_payload"
            ]
        ),

        "cap_xml": (
            risk_response[
                "cap_xml"
            ]
        ),

        "inundation": (
            risk_response[
                "inundation"
            ]
        ),
    }


# ============================================================
# FLOOD PREDICTION
# ============================================================

@app.post("/api/flood/predict")
def flood_predict(
    request: FloodPredictionRequest,
):

    try:

        rainfall = np.asarray(
            request.rainfall_mm,
            dtype=float,
        )

        dem = np.asarray(
            request.dem_m,
            dtype=float,
        )

        lulc = np.asarray(
            request.lulc,
            dtype=int,
        )

        if rainfall.ndim != 2:
            raise ValueError(
                "rainfall_mm must be a 2D grid."
            )

        if dem.ndim != 2:
            raise ValueError(
                "dem_m must be a 2D grid."
            )

        if lulc.ndim != 2:
            raise ValueError(
                "lulc must be a 2D grid."
            )

        if (
            rainfall.shape
            != dem.shape
            or rainfall.shape
            != lulc.shape
        ):
            raise ValueError(
                "rainfall_mm, dem_m and lulc "
                "must have identical grid shapes."
            )

        curve_number = (
            _curve_number_from_lulc(
                lulc
            )
        )

        runoff = _scs_cn_runoff(
            rainfall_mm=rainfall,
            curve_number=curve_number,
        )

        flood_depth_mm = (
            _calculate_flood_depth(
                runoff_mm=runoff,
                dem_m=dem,
            )
        )

        flood_depth_m = (
            flood_depth_mm / 1000.0
        )

        risk_response = (
            _build_risk_response(
                flood_depth_m=flood_depth_m,
                area_name=request.area_name,
            )
        )

        return {
            "status": "success",

            "demo": False,

            "area": request.area_name,

            "grid": {
                "rows": rainfall.shape[0],
                "columns": rainfall.shape[1],
            },

            "curve_number": _json_safe(
                curve_number
            ),

            "runoff_mm": _json_safe(
                runoff
            ),

            "flood_depth_m": _json_safe(
                flood_depth_m
            ),

            "risk": (
                risk_response[
                    "assessment"
                ]
            ),

            "cap_payload": (
                risk_response[
                    "cap_payload"
                ]
            ),

            "cap_xml": (
                risk_response[
                    "cap_xml"
                ]
            ),

            "inundation": (
                risk_response[
                    "inundation"
                ]
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Flood prediction failed: "
                f"{error}"
            ),
        ) from error


# ============================================================
# FLOOD RISK ONLY
# ============================================================

@app.get("/api/flood/risk")
def flood_risk():
    result = flood_demo()

    return {
        "status": result["status"],
        "demo": result["demo"],
        "area": result["area"],
        "risk": result["risk"],
        "inundation": result["inundation"],
        "cap_payload": result.get("cap_payload"),
        "cap_xml": result.get("cap_xml"),
    }


# ============================================================
# HISTORICAL VALIDATION
# ============================================================

@app.get("/api/validation")
def validation():

    persistence = (
        _read_csv_rows(
            "baseline_validation_results.csv"
        )
    )

    historical_ml = (
        _read_csv_rows(
            "historical_ml_validation_results.csv"
        )
    )

    heavy_rain_classifier = (
        _read_csv_rows(
            "heavy_rain_classifier_results.csv"
        )
    )

    feature_classifier = (
        _read_csv_rows(
            "feature_classifier_results.csv"
        )
    )

    return {
        "status": "validated",

        "validation_type": (
            "historical_daily_rainfall_benchmark"
        ),

        "dataset": {
            "source": (
                "Official IMD gridded rainfall"
            ),

            "resolution": (
                "0.25 degree"
            ),

            "years": [
                2015,
                2018,
            ],

            "training_period": "2015",

            "testing_period": "2018",
        },

        "headline_metrics": {
            "pod": 0.9323,
            "far": 0.0668,
            "csi": 0.8739,

            "pod_percent": 93.23,
            "far_percent": 6.68,
            "csi_percent": 87.39,

            "tp": 8742,
            "fp": 626,
            "fn": 635,
            "tn": 1767109,
        },

        "regression": {
            "mae": None,
            "rmse": None,
            "note": (
                "Regression metrics are retained in "
                "the model-specific validation outputs."
            ),
        },

        "models": {
            "persistence_baseline": persistence,

            "historical_ml": historical_ml,

            "heavy_rain_classifier": (
                heavy_rain_classifier
            ),

            "feature_based_classifier": (
                feature_classifier
            ),
        },

        "interpretation": {
            "pod": (
                "Probability of detecting heavy-rain cases."
            ),

            "far": (
                "False-alarm ratio."
            ),

            "csi": (
                "Critical Success Index."
            ),
        },

        "important_note": (
            "The headline metrics represent the "
            "historical daily feature-based rainfall "
            "classifier benchmark. They are NOT claimed "
            "as 0-3 hour ConvLSTM radar-nowcasting "
            "performance."
        ),

        "high_frequency_nowcasting": {
            "status": "NOT_VALIDATED_YET",

            "reason": (
                "Final 0-3h validation requires real "
                "high-frequency DWR radar and INSAT "
                "sequence data."
            ),

            "expected_timestep_minutes": 30,

            "target": (
                "Radar rainfall field"
            ),
        },
    }


# ============================================================
# VALIDATION SUMMARY
# ============================================================

@app.get("/api/validation/summary")
def validation_summary():

    return {
        "status": "success",

        "benchmark": (
            "2015 train → 2018 held-out test"
        ),

        "data_source": (
            "Official IMD gridded rainfall"
        ),

        "resolution": (
            "0.25 degree"
        ),

        "heavy_rain_threshold_mm_day": 64.5,

        "metrics": {
            "POD": 93.23,
            "FAR": 6.68,
            "CSI": 87.39,
        },

        "confusion_matrix": {
            "TP": 8742,
            "FP": 626,
            "FN": 635,
            "TN": 1767109,
        },

        "model": (
            "HistGradientBoostingClassifier"
        ),

        "scope_note": (
            "Daily historical benchmark; not "
            "0-3h radar nowcasting validation."
        ),
    }


# ============================================================
# SOURCE STATUS
# ============================================================

@app.get("/api/sources")
def sources():

    return {
        "status": "success",

        "common_grid": {
            "resolution_km": (
                COMMON_GRID_RESOLUTION_KM
            ),

            "timestep_minutes": (
                COMMON_TIMESTEP_MINUTES
            ),
        },

        "sources": {
            "satellite": {
                "provider": "MOSDAC / ISRO",
                "dataset": "INSAT-3D / INSAT-3DR",
                "native_timestep": "30 min",
                "native_resolution": "~4 km",
                "status": "PENDING",
            },

            "radar": {
                "provider": "IMD",
                "dataset": "DWR",
                "native_timestep": "10 min",
                "native_resolution": "~1 km",
                "status": "PENDING",
            },

            "aws": {
                "provider": "IMD",
                "type": "Automatic Weather Station",
                "status": "PENDING",
            },

            "arg": {
                "provider": "IMD",
                "type": "Agrometeorological observatory",
                "status": "PENDING",
            },

            "nwp": {
                "provider": "IMD / NWP",
                "native_timestep": "3-6 hours",
                "native_resolution": "~12 km",
                "status": "PENDING",
            },

            "weather_prototype": {
                "provider": "Open-Meteo",
                "status": "LIVE PROTOTYPE",
            },
        },
    }


# ============================================================
# MODEL STATUS
# ============================================================

@app.get("/api/models")
def models():

    return {
        "status": "success",

        "nowcasting": {
            "model": "ConvLSTM",
            "horizon": "0-3 hours",
            "input_timestep_minutes": 30,
            "status": "ARCHITECTURE READY",
            "training_status": (
                "AWAITING REAL HIGH-FREQUENCY DATA"
            ),
        },

        "nwp_postprocessing": {
            "model": "HistGradientBoostingRegressor",
            "horizon": "3-72 hours",
            "status": "MODEL READY",
            "training_status": (
                "IMPLEMENTATION READY"
            ),
        },

        "flood_model": {
            "runoff": "SCS-CN",
            "terrain": "DEM",
            "land_use": "LULC",
            "status": "SCREENING READY",
        },
    }


# ============================================================
# STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
async def startup_event():

    print()
    print("=" * 70)
    print("RAIN GUARD AI")
    print("DISASTER INTELLIGENCE BACKEND")
    print("=" * 70)
    print()
    print("Version              : 0.3.0")
    print("Problem Statement    : SIH26071")
    print("Primary Area         : Chennai, Tamil Nadu")
    print()
    print("Weather              : LIVE PROTOTYPE")
    print("AWS                  : PENDING")
    print("ARG                  : PENDING")
    print("NWP                  : PENDING")
    print("Satellite            : PENDING")
    print("Radar                : PENDING")
    print()
    print("Nowcasting           : ConvLSTM architecture ready")
    print("NWP Post-processing  : Gradient Boosting ready")
    print("Flood Model          : SCS-CN + DEM/LULC")
    print("Validation           : Historical benchmark ready")
    print()
    print("=" * 70)
    print()


# ============================================================
# LOCAL RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )