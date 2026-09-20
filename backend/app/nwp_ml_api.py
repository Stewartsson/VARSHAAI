"""
VARSHAAI AI
Integrated NWP ML + Flood Screening API

SIH Problem Statement: SIH26071

Pipeline:

    NWP / GFS
        ↓
    ML post-processing
        ↓
    72-hour rainfall forecast
        ↓
    Cumulative rainfall
        ↓
    SCS-CN runoff
        ↓
    Flood depth
        ↓
    Inundation
        ↓
    Flood risk
        ↓
    CAP-oriented alert

Important:

    The current NWP source is Open-Meteo GFS.

    The current DEM/LULC spatial grid used by the
    integrated endpoint is a screening/prototype grid.

    It must NOT be interpreted as a production
    georeferenced Chennai flood map until real
    DEM/LULC rasters are connected.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from fastapi import APIRouter, HTTPException

from .ml.nwp_ml_service import (
    FEATURE_NAMES,
    MODEL_PATH,
    generate_postprocessed_forecast,
    load_model_payload,
)

from .flood.flood_pipeline import (
    RainGuardFloodPipeline,
)

from .alerts.risk_classifier import (
    FloodRiskClassifier,
)

from .alerts.cap_generator import (
    CAPGenerator,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/nwp/ml",
    tags=["NWP ML"],
)


# ============================================================
# PATHS
# ============================================================

APP_DIR = Path(__file__).resolve().parent

BACKEND_DIR = APP_DIR.parent

HISTORICAL_FEATURE_CACHE = (
    BACKEND_DIR
    / "data"
    / "historical"
    / "imd_rainfall"
    / "chennai_historical_features.json"
)


# ============================================================
# CHENNAI
# ============================================================

CHENNAI_LAT = 13.0827

CHENNAI_LON = 80.2707


# ============================================================
# SCREENING GRID
# ============================================================

SCREENING_GRID_ROWS = 4

SCREENING_GRID_COLUMNS = 4


# ============================================================
# SCREENING LULC
# ============================================================

"""
Prototype LULC classes used by the existing
RainGuard flood-pipeline demonstration.

    1 = Water
    2 = Forest
    3 = Vegetation
    4 = Agriculture
    5 = Barren
    6 = Built-up
    7 = Wetland

This grid is ONLY a screening template.

Replace it with a real Chennai LULC raster
when geospatial data is available.
"""

SCREENING_LULC = np.array(
    [
        [2, 3, 4, 6],
        [3, 4, 6, 6],
        [2, 6, 6, 5],
        [3, 6, 5, 7],
    ],
    dtype=np.int16,
)


# ============================================================
# SCREENING DEM
# ============================================================

"""
Prototype DEM in metres.

This follows the spatial demonstration grid used
by the existing flood pipeline.

It is NOT a real Chennai DEM.
"""

SCREENING_DEM_M = np.array(
    [
        [18.0, 16.0, 14.0, 12.0],
        [17.0, 13.0, 10.0, 9.0],
        [15.0, 11.0, 8.0, 6.0],
        [14.0, 9.0, 5.0, 3.0],
    ],
    dtype=np.float32,
)


# ============================================================
# GLOBAL FLOOD ENGINES
# ============================================================

flood_pipeline = RainGuardFloodPipeline()

risk_classifier = FloodRiskClassifier()

cap_generator = CAPGenerator()


# ============================================================
# HELPERS
# ============================================================

def _utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def _json_safe(value: Any) -> Any:
    """
    Convert NumPy/dataclass values into JSON-safe
    Python values.
    """

    if value is None:

        return None

    if isinstance(
        value,
        np.ndarray,
    ):

        return value.tolist()

    if isinstance(
        value,
        np.generic,
    ):

        return value.item()

    if hasattr(
        value,
        "__dataclass_fields__",
    ):

        return {
            key: _json_safe(val)
            for key, val in value.__dict__.items()
        }

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key): _json_safe(val)
            for key, val in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):

        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        float,
    ):

        if not np.isfinite(value):

            return None

    return value


def load_historical_cache() -> dict[str, Any]:
    """
    Load the historical rainfall feature cache.
    """

    if not HISTORICAL_FEATURE_CACHE.exists():

        raise FileNotFoundError(
            "Historical feature cache not found: "
            f"{HISTORICAL_FEATURE_CACHE}"
        )

    with open(
        HISTORICAL_FEATURE_CACHE,
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    if not isinstance(
        payload,
        dict,
    ):

        raise ValueError(
            "Historical feature cache must contain "
            "a JSON object."
        )

    return payload


# ============================================================
# BUILD SPATIAL RAINFALL GRID
# ============================================================

def rainfall_to_screening_grid(
    rainfall_mm: float,
) -> np.ndarray:
    """
    Convert a scalar NWP rainfall forecast into
    a spatial screening grid.

    The same rainfall value is applied to every
    screening cell.

    This is deliberately labelled as a prototype
    because the current NWP API provides a point
    forecast rather than a spatial rainfall raster.

    Real production implementation should replace
    this with a geospatial NWP rainfall field.
    """

    value = float(
        rainfall_mm
    )

    if not np.isfinite(value):

        value = 0.0

    value = max(
        value,
        0.0,
    )

    return np.full(
        (
            SCREENING_GRID_ROWS,
            SCREENING_GRID_COLUMNS,
        ),
        value,
        dtype=np.float32,
    )


# ============================================================
# RUN FLOOD SCREENING
# ============================================================

def run_flood_screening(
    cumulative_rainfall_mm: float,
) -> dict[str, Any]:
    """
    Run the existing RainGuard flood pipeline
    using cumulative NWP rainfall.

    Pipeline:

        Rainfall
            ↓
        LULC → CN
            ↓
        SCS-CN runoff
            ↓
        Flood depth
            ↓
        Inundation
    """

    rainfall_grid = (
        rainfall_to_screening_grid(
            cumulative_rainfall_mm
        )
    )

    result = flood_pipeline.run(
        rainfall_mm=rainfall_grid,
        lulc=SCREENING_LULC,
        dem=SCREENING_DEM_M,
    )

    # --------------------------------------------------------
    # Risk assessment
    # --------------------------------------------------------

    assessment = (
        risk_classifier.classify(
            result["flood_depth_m"]
        )
    )

    # --------------------------------------------------------
    # CAP-oriented XML
    # --------------------------------------------------------

    cap_xml = (
        cap_generator.generate_from_assessment(
            assessment=assessment,
            area_name="Chennai",
        )
    )

    # --------------------------------------------------------
    # Prepare response
    # --------------------------------------------------------

    return {

        "rainfall_mm": _json_safe(
            result["rainfall_mm"]
        ),

        "curve_number": _json_safe(
            result["curve_number"]
        ),

        "runoff_mm": _json_safe(
            result["runoff_mm"]
        ),

        "flood_depth_m": _json_safe(
            result["flood_depth_m"]
        ),

        "flood_extent": _json_safe(
            result["flood_extent"]
        ),

        "risk_class": _json_safe(
            result["risk_class"]
        ),

        "risk_labels": _json_safe(
            result["risk_labels"]
        ),

        "summary": _json_safe(
            result["summary"]
        ),

        "risk_assessment": _json_safe(
            assessment
        ),

        "cap_xml": cap_xml,
    }


# ============================================================
# MODEL STATUS
# ============================================================

@router.get("/status")
def nwp_ml_status() -> dict[str, Any]:
    """
    Return NWP ML model status.
    """

    try:

        payload = load_model_payload()

        model = payload.get(
            "model"
        )

        feature_names = payload.get(
            "feature_names",
            FEATURE_NAMES,
        )

        if model is None:

            raise ValueError(
                "Trained model is missing "
                "from model payload."
            )

        return {

            "status": "ready",

            "model": type(
                model
            ).__name__,

            "feature_count": len(
                feature_names
            ),

            "feature_names": list(
                feature_names
            ),

            "model_file": MODEL_PATH.name,

            "trained_model_available": (
                MODEL_PATH.exists()
            ),

            "inference_mode": (
                "live-data-gated"
            ),

            "nwp_source": (
                "Open-Meteo GFS"
            ),

            "historical_rainfall_source": (
                "Open-Meteo Historical Archive"
            ),

            "forecast_hours": 72,

            "flood_integration": True,

            "flood_pipeline": (
                "SCS-CN + DEM/LULC + "
                "Inundation + Risk + CAP"
            ),

            "spatial_mode": (
                "screening-grid"
            ),

            "note": (
                "NWP ML inference is connected to "
                "the flood screening pipeline. "
                "The current spatial grid is a "
                "prototype screening grid and is not "
                "a production georeferenced Chennai "
                "flood map."
            ),

            "timestamp": _utc_now(),
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# NWP POST-PROCESSED FORECAST
# ============================================================

@router.get("/postprocessed")
def nwp_ml_postprocessed() -> dict[str, Any]:
    """
    Generate the 72-hour NWP ML rainfall forecast.
    """

    try:

        result = (
            generate_postprocessed_forecast()
        )

        if not isinstance(
            result,
            dict,
        ):

            raise ValueError(
                "NWP ML service returned "
                "an unexpected response."
            )

        return result

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "NWP post-processing service failed: "
                f"{exc}"
            ),
        ) from exc


# ============================================================
# INTEGRATED NWP → FLOOD FORECAST
# ============================================================

@router.get("/flood-forecast")
def nwp_ml_flood_forecast() -> dict[str, Any]:
    """
    Full NWP → ML → Flood integration.

    For every NWP forecast hour:

        1. Get ML-corrected rainfall
        2. Calculate cumulative rainfall
        3. Feed cumulative rainfall into SCS-CN
        4. Estimate runoff
        5. Estimate flood depth
        6. Calculate inundation
        7. Calculate risk
        8. Generate CAP-oriented XML

    This endpoint uses the current prototype
    spatial screening grid.
    """

    try:

        # ----------------------------------------------------
        # Step 1
        # Get 72-hour post-processed NWP forecast
        # ----------------------------------------------------

        nwp_result = (
            generate_postprocessed_forecast()
        )

        if not isinstance(
            nwp_result,
            dict,
        ):

            raise ValueError(
                "Unexpected NWP forecast response."
            )

        records = nwp_result.get(
            "records",
            [],
        )

        if not isinstance(
            records,
            list,
        ):

            raise ValueError(
                "NWP forecast records must be a list."
            )

        if not records:

            raise ValueError(
                "No NWP forecast records available."
            )

        # ----------------------------------------------------
        # Step 2
        # Process every forecast hour
        # ----------------------------------------------------

        integrated_records = []

        cumulative_rainfall = 0.0

        maximum_depth_seen = 0.0

        maximum_flood_fraction = 0.0

        highest_risk_code = 0

        highest_risk_level = "GREEN"

        # ----------------------------------------------------
        # Risk ordering
        # ----------------------------------------------------

        risk_order = {
            "GREEN": 0,
            "YELLOW": 1,
            "ORANGE": 2,
            "RED": 3,
        }

        for index, record in enumerate(
            records
        ):

            if not isinstance(
                record,
                dict,
            ):

                continue

            # ------------------------------------------------
            # Extract ML rainfall
            # ------------------------------------------------

            rainfall_value = record.get(
                "postprocessed_rainfall_mm"
            )

            try:

                rainfall_mm = float(
                    rainfall_value
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            if not np.isfinite(
                rainfall_mm
            ):

                continue

            rainfall_mm = max(
                rainfall_mm,
                0.0,
            )

            # ------------------------------------------------
            # Cumulative rainfall
            # ------------------------------------------------

            cumulative_rainfall += (
                rainfall_mm
            )

            # ------------------------------------------------
            # Flood model
            # ------------------------------------------------

            flood_result = (
                run_flood_screening(
                    cumulative_rainfall
                )
            )

            # ------------------------------------------------
            # Risk
            # ------------------------------------------------

            assessment = (
                flood_result[
                    "risk_assessment"
                ]
            )

            alert_level = str(
                assessment.get(
                    "alert_level",
                    "GREEN",
                )
            ).upper()

            alert_code = int(
                assessment.get(
                    "alert_code",
                    0,
                )
            )

            # ------------------------------------------------
            # Statistics
            # ------------------------------------------------

            summary = (
                flood_result[
                    "summary"
                ]
            )

            maximum_depth = float(
                summary.get(
                    "maximum_depth_m",
                    0.0,
                )
            )

            flooded_fraction = float(
                summary.get(
                    "flooded_fraction",
                    0.0,
                )
            )

            maximum_depth_seen = max(
                maximum_depth_seen,
                maximum_depth,
            )

            maximum_flood_fraction = max(
                maximum_flood_fraction,
                flooded_fraction,
            )

            if (
                risk_order.get(
                    alert_level,
                    0,
                )
                >
                risk_order.get(
                    highest_risk_level,
                    0,
                )
            ):

                highest_risk_level = (
                    alert_level
                )

                highest_risk_code = (
                    alert_code
                )

            # ------------------------------------------------
            # Forecast record
            # ------------------------------------------------

            integrated_records.append(
                {

                    "forecast_hour": (
                        index + 1
                    ),

                    "timestamp_utc": (
                        record.get(
                            "timestamp_utc"
                        )
                    ),

                    "nwp_precipitation_mm": (
                        record.get(
                            "nwp_precipitation_mm"
                        )
                    ),

                    "postprocessed_rainfall_mm": (
                        rainfall_mm
                    ),

                    "cumulative_rainfall_mm": (
                        cumulative_rainfall
                    ),

                    "runoff_mm": (
                        flood_result[
                            "summary"
                        ].get(
                            "runoff_mean_mm",
                            float(
                                np.nanmean(
                                    np.asarray(
                                        flood_result[
                                            "runoff_mm"
                                        ],
                                        dtype=float,
                                    )
                                )
                            ),
                        )
                    ),

                    "maximum_flood_depth_m": (
                        maximum_depth
                    ),

                    "flooded_fraction": (
                        flooded_fraction
                    ),

                    "flooded_pixels": (
                        summary.get(
                            "flooded_pixels",
                            0,
                        )
                    ),

                    "risk_level": (
                        alert_level
                    ),

                    "risk_code": (
                        alert_code
                    ),

                    "flood_extent": (
                        flood_result[
                            "flood_extent"
                        ]
                    ),

                    "risk_class": (
                        flood_result[
                            "risk_class"
                        ]
                    ),

                    "risk_labels": (
                        flood_result[
                            "risk_labels"
                        ]
                    ),
                }
            )

        # ----------------------------------------------------
        # Validate processed records
        # ----------------------------------------------------

        if not integrated_records:

            raise ValueError(
                "No valid integrated forecast "
                "records were generated."
            )

        # ----------------------------------------------------
        # Highest-risk CAP
        # ----------------------------------------------------

        final_record = integrated_records[-1]

        final_risk = run_flood_screening(
            cumulative_rainfall
        )

        final_assessment = (
            final_risk[
                "risk_assessment"
            ]
        )

        cap_xml = (
            final_risk[
                "cap_xml"
            ]
        )

        # ----------------------------------------------------
        # Return integrated product
        # ----------------------------------------------------

        return {

            "status": "success",

            "service": (
                "VARSHAAI NWP ML + Flood Integration"
            ),

            "location": {

                "name": "Chennai",

                "latitude": CHENNAI_LAT,

                "longitude": CHENNAI_LON,
            },

            "forecast_hours": len(
                integrated_records
            ),

            "model": {

                "type": (
                    "HistGradientBoostingRegressor"
                ),

                "file": MODEL_PATH.name,

                "features": list(
                    FEATURE_NAMES
                ),
            },

            "integration": {

                "nwp": True,

                "ml_postprocessing": True,

                "cumulative_rainfall": True,

                "scs_cn": True,

                "dem": True,

                "lulc": True,

                "flood_depth": True,

                "inundation": True,

                "risk_classification": True,

                "cap_generation": True,
            },

            "spatial_grid": {

                "rows": (
                    SCREENING_GRID_ROWS
                ),

                "columns": (
                    SCREENING_GRID_COLUMNS
                ),

                "mode": (
                    "prototype-screening-grid"
                ),

                "georeferenced": False,

                "note": (
                    "Replace the prototype DEM/LULC "
                    "grid with real georeferenced "
                    "Chennai rasters for operational "
                    "spatial prediction."
                ),
            },

            "summary": {

                "total_forecast_records": (
                    len(
                        integrated_records
                    )
                ),

                "total_forecast_rainfall_mm": (
                    cumulative_rainfall
                ),

                "maximum_flood_depth_m": (
                    maximum_depth_seen
                ),

                "maximum_flooded_fraction": (
                    maximum_flood_fraction
                ),

                "highest_risk_level": (
                    highest_risk_level
                ),

                "highest_risk_code": (
                    highest_risk_code
                ),
            },

            "records": (
                integrated_records
            ),

            "final_risk": (
                _json_safe(
                    final_assessment
                )
            ),

            "cap_xml": cap_xml,

            "timestamp": _utc_now(),
        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "Integrated NWP-to-flood "
                f"forecast failed: {exc}"
            ),
        ) from exc


# ============================================================
# HISTORICAL FEATURES
# ============================================================

@router.get("/historical/features")
def historical_features() -> dict[str, Any]:
    """
    Return historical rainfall features.
    """

    try:

        payload = (
            load_historical_cache()
        )

        observations = payload.get(
            "observations",
            [],
        )

        if not isinstance(
            observations,
            list,
        ):

            observations = []

        complete_rows = []

        for row in observations:

            if not isinstance(
                row,
                dict,
            ):

                continue

            if (
                row.get(
                    "recent_rainfall_mm"
                )
                is None
            ):

                continue

            if (
                row.get(
                    "rolling_3_day_rainfall_mm"
                )
                is None
            ):

                continue

            if (
                row.get(
                    "rolling_7_day_rainfall_mm"
                )
                is None
            ):

                continue

            complete_rows.append(
                row
            )

        latest_complete = (
            complete_rows[-1]
            if complete_rows
            else None
        )

        return {

            "status": "available",

            "source": payload.get(
                "source",
                "IMD",
            ),

            "dataset": payload.get(
                "dataset",
                "RF25_ind2015_rfp25.nc",
            ),

            "region": payload.get(
                "region",
                "Chennai-area IMD grid cell",
            ),

            "latitude": payload.get(
                "latitude",
                13.25,
            ),

            "longitude": payload.get(
                "longitude",
                80.25,
            ),

            "year": payload.get(
                "year",
                2015,
            ),

            "total_days": payload.get(
                "total_days",
                len(observations),
            ),

            "complete_feature_days": payload.get(
                "complete_feature_days",
                len(complete_rows),
            ),

            "feature_names": [
                "recent_rainfall_mm",
                "rolling_3_day_rainfall_mm",
                "rolling_7_day_rainfall_mm",
            ],

            "latest_complete_features": (
                latest_complete
            ),

            "observation_count": len(
                observations
            ),

            "cache": {

                "available": True,

                "file": (
                    HISTORICAL_FEATURE_CACHE.name
                ),

                "generated_once": True,

                "netcdf_loaded_per_request": False,
            },

            "live_data": False,

            "note": (
                "Historical rainfall is used for "
                "feature engineering and validation. "
                "It is not treated as current rainfall."
            ),

            "timestamp": _utc_now(),
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# HISTORICAL ML SMOKE TEST
# ============================================================

@router.get("/historical/smoke-test")
def historical_ml_smoke_test() -> dict[str, Any]:
    """
    Verify that the trained NWP ML model
    can perform inference.
    """

    try:

        payload = (
            load_model_payload()
        )

        model = payload.get(
            "model"
        )

        if model is None:

            raise ValueError(
                "Trained model missing."
            )

        historical = (
            load_historical_cache()
        )

        observations = historical.get(
            "observations",
            [],
        )

        complete_rows = []

        for row in observations:

            if not isinstance(
                row,
                dict,
            ):

                continue

            if (
                row.get(
                    "recent_rainfall_mm"
                )
                is None
            ):

                continue

            if (
                row.get(
                    "rolling_3_day_rainfall_mm"
                )
                is None
            ):

                continue

            if (
                row.get(
                    "rolling_7_day_rainfall_mm"
                )
                is None
            ):

                continue

            complete_rows.append(
                row
            )

        if not complete_rows:

            raise HTTPException(
                status_code=404,
                detail=(
                    "No complete historical "
                    "feature row available."
                ),
            )

        latest = (
            complete_rows[-1]
        )

        model_input = [

            0.0,

            70.0,

            2.5,

            1010.0,

            float(
                latest[
                    "recent_rainfall_mm"
                ]
            ),

            float(
                latest[
                    "rolling_3_day_rainfall_mm"
                ]
            ),

            float(
                latest[
                    "rolling_7_day_rainfall_mm"
                ]
            ),
        ]

        prediction = model.predict(
            [model_input]
        )

        prediction_value = max(
            float(
                prediction[0]
            ),
            0.0,
        )

        return {

            "status": "success",

            "test": (
                "historical_ml_smoke_test"
            ),

            "model": type(
                model
            ).__name__,

            "model_file": (
                MODEL_PATH.name
            ),

            "feature_names": list(
                payload.get(
                    "feature_names",
                    FEATURE_NAMES,
                )
            ),

            "historical_row": latest,

            "model_input": {

                "nwp_precipitation_mm": (
                    model_input[0]
                ),

                "nwp_humidity": (
                    model_input[1]
                ),

                "nwp_wind_speed_ms": (
                    model_input[2]
                ),

                "nwp_pressure_hpa": (
                    model_input[3]
                ),

                "recent_rainfall_mm": (
                    model_input[4]
                ),

                "rolling_3_day_rainfall_mm": (
                    model_input[5]
                ),

                "rolling_7_day_rainfall_mm": (
                    model_input[6]
                ),
            },

            "predicted_rainfall_mm": (
                prediction_value
            ),

            "note": (
                "Smoke test only. This does not "
                "represent model validation performance."
            ),

            "timestamp": _utc_now(),
        }

    except HTTPException:

        raise

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Historical ML smoke test failed: "
                f"{exc}"
            ),
        ) from exc


# ============================================================
# ROOT
# ============================================================

@router.get("/")
def nwp_ml_root() -> dict[str, Any]:
    """
    NWP ML service information.
    """

    return {

        "service": (
            "VARSHAAI NWP Machine Learning Service"
        ),

        "status": "online",

        "model": (
            "HistGradientBoostingRegressor"
        ),

        "forecast_hours": 72,

        "features": list(
            FEATURE_NAMES
        ),

        "integrated_pipeline": (
            "NWP → ML → Cumulative Rainfall → "
            "SCS-CN → Flood Depth → Inundation → "
            "Risk → CAP"
        ),

        "endpoints": {

            "status": (
                "/api/nwp/ml/status"
            ),

            "postprocessed": (
                "/api/nwp/ml/postprocessed"
            ),

            "flood_forecast": (
                "/api/nwp/ml/flood-forecast"
            ),

            "historical_features": (
                "/api/nwp/ml/historical/features"
            ),

            "historical_smoke_test": (
                "/api/nwp/ml/historical/smoke-test"
            ),
        },

        "timestamp": _utc_now(),
    }