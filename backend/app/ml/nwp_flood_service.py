"""
VARSHAAI - NWP to Flood Integration Service

Purpose:
    Connect the working NWP ML rainfall forecast to the
    existing SCS-CN + DEM/LULC flood screening pipeline.

Current prototype limitation:
    The current NWP service provides a Chennai point forecast,
    while the flood model requires a 2-D spatial rainfall raster.

Therefore this module uses a clearly labelled prototype
spatial bridge:

    NWP point rainfall
            ↓
    accumulated rainfall
            ↓
    broadcast over prototype Chennai grid
            ↓
    SCS-CN
            ↓
    DEM + LULC
            ↓
    flood depth
            ↓
    inundation
            ↓
    operational risk
            ↓
    CAP-oriented alert

IMPORTANT:
    This is a prototype integration.
    It is NOT a claim of spatially resolved NWP rainfall.

When real gridded NWP data becomes available, replace only
the rainfall-grid construction function.
The flood pipeline itself does not need to change.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.alerts.cap_generator import CAPGenerator
from app.alerts.risk_classifier import FloodRiskClassifier
from app.flood.flood_pipeline import RainGuardFloodPipeline
from app.ml.nwp_ml_service import generate_postprocessed_forecast


# ============================================================
# LOCATION
# ============================================================

AREA_NAME = "Chennai"

CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2707


# ============================================================
# PROTOTYPE GRID
# ============================================================

GRID_ROWS = 4
GRID_COLS = 4


# ============================================================
# PROTOTYPE DEM
#
# This is the same deterministic demonstration terrain
# used by the existing flood pipeline test.
#
# Units: metres
# ============================================================

PROTOTYPE_DEM = np.array(
    [
        [18.0, 16.0, 14.0, 12.0],
        [17.0, 13.0, 10.0, 9.0],
        [15.0, 11.0, 8.0, 6.0],
        [14.0, 9.0, 5.0, 3.0],
    ],
    dtype=np.float32,
)


# ============================================================
# PROTOTYPE LULC
#
# Classes used by CurveNumberMapper:
#
# 1 = Water
# 2 = Forest
# 3 = Vegetation
# 4 = Agriculture
# 5 = Barren
# 6 = Built-up
# 7 = Wetland
# ============================================================

PROTOTYPE_LULC = np.array(
    [
        [2, 3, 4, 6],
        [3, 4, 6, 6],
        [2, 6, 6, 5],
        [3, 6, 5, 7],
    ],
    dtype=np.int16,
)


# ============================================================
# ENGINES
# ============================================================

flood_pipeline = RainGuardFloodPipeline()

risk_classifier = FloodRiskClassifier()

cap_generator = CAPGenerator()


# ============================================================
# JSON SAFETY
# ============================================================

def _json_safe(value: Any) -> Any:
    """
    Convert NumPy values and dataclasses into JSON-safe values.
    """

    if value is None:
        return None

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict

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
        if not np.isfinite(value):
            return None

    return value


# ============================================================
# NWP RECORD EXTRACTION
# ============================================================

def _extract_forecast_records(
    forecast_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Extract NWP postprocessed rainfall records.
    """

    records = forecast_payload.get(
        "records",
        [],
    )

    if not isinstance(records, list):
        raise ValueError(
            "NWP forecast payload does not contain "
            "a valid records list."
        )

    cleaned = []

    for record in records:

        if not isinstance(record, dict):
            continue

        timestamp = record.get(
            "timestamp_utc"
        )

        rainfall = record.get(
            "postprocessed_rainfall_mm"
        )

        if timestamp is None:
            continue

        try:
            rainfall = float(rainfall)

        except (
            TypeError,
            ValueError,
        ):
            continue

        if not np.isfinite(rainfall):
            continue

        rainfall = max(
            rainfall,
            0.0,
        )

        cleaned.append(
            {
                "timestamp_utc": str(
                    timestamp
                ),
                "postprocessed_rainfall_mm": rainfall,
            }
        )

    if not cleaned:
        raise ValueError(
            "No valid postprocessed rainfall records "
            "were returned by the NWP model."
        )

    return cleaned


# ============================================================
# RAINFALL ACCUMULATION
# ============================================================

def _rolling_accumulation(
    records: list[dict[str, Any]],
    window_hours: int = 3,
) -> list[dict[str, Any]]:
    """
    Calculate rolling accumulated rainfall.

    Example:
        window_hours = 3

    At each forecast time:
        accumulated rainfall =
        current hour + previous 2 forecast hours

    This is used as the rainfall forcing for the
    screening-level flood model.
    """

    if window_hours <= 0:
        raise ValueError(
            "window_hours must be positive."
        )

    values = [
        float(
            record[
                "postprocessed_rainfall_mm"
            ]
        )
        for record in records
    ]

    output = []

    for index, record in enumerate(records):

        start = max(
            0,
            index - window_hours + 1,
        )

        rainfall_window = values[
            start:index + 1
        ]

        accumulated = float(
            sum(rainfall_window)
        )

        output.append(
            {
                "timestamp_utc": record[
                    "timestamp_utc"
                ],
                "hourly_rainfall_mm": float(
                    record[
                        "postprocessed_rainfall_mm"
                    ]
                ),
                "accumulated_rainfall_mm": accumulated,
                "window_hours": window_hours,
            }
        )

    return output


# ============================================================
# NWP POINT → FLOOD RAINFALL GRID
# ============================================================

def _build_spatial_rainfall_grid(
    rainfall_mm: float,
) -> np.ndarray:
    """
    Prototype spatial bridge.

    The current NWP forecast is a Chennai point forecast.
    The flood model requires a 2-D raster.

    Until real gridded NWP data is connected, the same
    accumulated rainfall value is broadcast across the
    prototype 4x4 flood-model grid.

    This function is intentionally isolated so that it can
    later be replaced by:

        gridded_nwp_rainfall -> 2D raster

    without changing the flood pipeline.
    """

    rainfall = float(
        rainfall_mm
    )

    if not np.isfinite(rainfall):
        raise ValueError(
            "Rainfall value must be finite."
        )

    rainfall = max(
        rainfall,
        0.0,
    )

    return np.full(
        (
            GRID_ROWS,
            GRID_COLS,
        ),
        rainfall,
        dtype=np.float32,
    )


# ============================================================
# SINGLE FLOOD SCENARIO
# ============================================================

def _run_flood_scenario(
    timestamp_utc: str,
    hourly_rainfall_mm: float,
    accumulated_rainfall_mm: float,
    window_hours: int,
) -> dict[str, Any]:
    """
    Run one NWP rainfall time step through the
    complete flood pipeline.
    """

    rainfall_grid = (
        _build_spatial_rainfall_grid(
            accumulated_rainfall_mm
        )
    )

    result = flood_pipeline.run(
        rainfall_mm=rainfall_grid,
        lulc=PROTOTYPE_LULC,
        dem=PROTOTYPE_DEM,
    )

    flood_depth_m = np.asarray(
        result["flood_depth_m"],
        dtype=np.float32,
    )

    flood_extent = np.asarray(
        result["flood_extent"]
    )

    risk_grid = np.asarray(
        result["risk_class"]
    )

    # --------------------------------------------------------
    # Operational risk classifier
    # --------------------------------------------------------

    assessment = (
        risk_classifier.classify(
            flood_depth_m
        )
    )

    cap_payload = (
        risk_classifier.build_alert_payload(
            assessment=assessment,
            area_name=AREA_NAME,
            valid_from=timestamp_utc,
            valid_until=timestamp_utc,
        )
    )

    cap_xml = (
        cap_generator.generate_from_assessment(
            assessment=assessment,
            area_name=AREA_NAME,
        )
    )

    summary = result.get(
        "summary",
        {},
    )

    return {
        "timestamp_utc": timestamp_utc,

        "rainfall": {
            "hourly_rainfall_mm": float(
                hourly_rainfall_mm
            ),
            "accumulated_rainfall_mm": float(
                accumulated_rainfall_mm
            ),
            "accumulation_window_hours": int(
                window_hours
            ),
        },

        "flood": {
            "maximum_depth_m": float(
                np.nanmax(
                    flood_depth_m
                )
            ),
            "mean_depth_m": float(
                np.nanmean(
                    flood_depth_m
                )
            ),
            "flooded_pixels": int(
                np.sum(
                    flood_extent == 1
                )
            ),
            "total_pixels": int(
                flood_extent.size
            ),
            "flooded_fraction": float(
                np.mean(
                    flood_extent == 1
                )
            ),
        },

        "risk": _json_safe(
            assessment
        ),

        "flood_model": {
            "curve_number": _json_safe(
                result[
                    "curve_number"
                ]
            ),
            "runoff_mm": _json_safe(
                result[
                    "runoff_mm"
                ]
            ),
            "flood_depth_m": _json_safe(
                flood_depth_m
            ),
            "flood_extent": _json_safe(
                flood_extent
            ),
            "risk_class": _json_safe(
                risk_grid
            ),
            "risk_labels": _json_safe(
                result.get(
                    "risk_labels",
                    {},
                )
            ),
            "summary": _json_safe(
                summary
            ),
        },

        "cap_payload": _json_safe(
            cap_payload
        ),

        "cap_xml": cap_xml,
    }


# ============================================================
# COMPLETE NWP → FLOOD FORECAST
# ============================================================

def generate_nwp_flood_forecast(
    window_hours: int = 3,
) -> dict[str, Any]:
    """
    Run the complete:

        NWP ML → Rainfall accumulation
               → Flood model
               → Risk classification
               → CAP

    pipeline.
    """

    if window_hours <= 0:
        raise ValueError(
            "window_hours must be positive."
        )

    # --------------------------------------------------------
    # STEP 1
    # NWP ML forecast
    # --------------------------------------------------------

    nwp_payload = (
        generate_postprocessed_forecast()
    )

    records = (
        _extract_forecast_records(
            nwp_payload
        )
    )

    # --------------------------------------------------------
    # STEP 2
    # Rainfall accumulation
    # --------------------------------------------------------

    accumulated_records = (
        _rolling_accumulation(
            records,
            window_hours=window_hours,
        )
    )

    # --------------------------------------------------------
    # STEP 3
    # Flood modelling
    # --------------------------------------------------------

    flood_records = []

    for item in accumulated_records:

        scenario = _run_flood_scenario(
            timestamp_utc=item[
                "timestamp_utc"
            ],
            hourly_rainfall_mm=item[
                "hourly_rainfall_mm"
            ],
            accumulated_rainfall_mm=item[
                "accumulated_rainfall_mm"
            ],
            window_hours=window_hours,
        )

        flood_records.append(
            scenario
        )

    # --------------------------------------------------------
    # STEP 4
    # Find maximum forecast risk scenario
    # --------------------------------------------------------

    if not flood_records:
        raise ValueError(
            "No flood forecast scenarios were generated."
        )

    maximum_risk_record = max(
        flood_records,
        key=lambda item: (
            int(
                item["risk"]["alert_code"]
            ),
            float(
                item["flood"]["maximum_depth_m"]
            ),
            float(
                item["flood"]["flooded_fraction"]
            ),
        ),
    )

    return {
        "status": "success",

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "location": {
            "name": AREA_NAME,
            "latitude": CHENNAI_LAT,
            "longitude": CHENNAI_LON,
        },

        "forecast": {
            "hours": len(records),
            "accumulation_window_hours": window_hours,
        },

        "models": {
            "nwp": (
                "HistGradientBoostingRegressor"
            ),
            "runoff": "SCS-CN",
            "terrain": "DEM screening",
            "land_use": "LULC-based Curve Number",
            "flood_depth": (
                "Terrain-aware screening model"
            ),
            "risk": (
                "FloodRiskClassifier"
            ),
        },

        "spatial_bridge": {
            "mode": "prototype-point-to-grid",
            "grid_shape": [
                GRID_ROWS,
                GRID_COLS,
            ],
            "grid_resolution_km": 4.0,
            "warning": (
                "Current NWP forecast is a Chennai "
                "point forecast. Rainfall is broadcast "
                "across the prototype flood grid. "
                "Replace this bridge with genuine "
                "gridded NWP rainfall when available."
            ),
        },

        "records": _json_safe(
            flood_records
        ),

        "maximum_risk_scenario": _json_safe(
            maximum_risk_record
        ),
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("VARSHAAI NWP → FLOOD INTEGRATION TEST")
    print("=" * 70)

    print()
    print("Step 1: Fetching NWP ML forecast...")

    result = (
        generate_nwp_flood_forecast(
            window_hours=3
        )
    )

    print("NWP forecast received.")

    print()
    print(
        "Forecast hours:",
        result[
            "forecast"
        ][
            "hours"
        ],
    )

    print()
    print("Step 2: Running flood pipeline...")

    print(
        "Grid:",
        result[
            "spatial_bridge"
        ][
            "grid_shape"
        ],
    )

    print("Flood scenarios generated.")

    maximum = result[
        "maximum_risk_scenario"
    ]

    print()
    print("Maximum forecast scenario")
    print("-------------------------")

    print(
        "Timestamp:",
        maximum[
            "timestamp_utc"
        ],
    )

    print(
        "Hourly rainfall:",
        round(
            maximum[
                "rainfall"
            ][
                "hourly_rainfall_mm"
            ],
            3,
        ),
        "mm",
    )

    print(
        "Accumulated rainfall:",
        round(
            maximum[
                "rainfall"
            ][
                "accumulated_rainfall_mm"
            ],
            3,
        ),
        "mm",
    )

    print(
        "Maximum flood depth:",
        round(
            maximum[
                "flood"
            ][
                "maximum_depth_m"
            ],
            3,
        ),
        "m",
    )

    print(
        "Flooded fraction:",
        round(
            maximum[
                "flood"
            ][
                "flooded_fraction"
            ]
            * 100.0,
            2,
        ),
        "%",
    )

    print(
        "Risk:",
        maximum[
            "risk"
        ][
            "alert_level"
        ],
    )

    print(
        "Confidence:",
        round(
            maximum[
                "risk"
            ][
                "confidence"
            ],
            3,
        ),
    )

    print()
    print("=" * 70)
    print("STATUS: NWP → FLOOD INTEGRATION TEST PASSED")
    print("=" * 70)