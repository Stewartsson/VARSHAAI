# SMART INDIA HACKATHON 2026

# Problem Statement ID – SIH26071

# Problem Statement Title- 
  AI/ML-Based Integrated heavy rainfall Early Warning and Inundation Prediction System using Satellite, Radar, observational Weather and numerical weather prediction model data.

# Theme - Disaster Management

# PS Category - Software

# Team ID- 164865

# Team Name - IntelliX Titans 

# VARSHA AI

AI/ML-Based Integrated Heavy Rainfall Early Warning and Inundation Prediction System.

## Prototype architecture
- Frontend: React + Vite + Leaflet-ready dashboard
- Backend: FastAPI
- Prototype data: simulated meteorological/radar/satellite/NWP feeds
- Next integration: operational satellite, radar, observation and NWP adapters

## Run backend
```bash
cd backend
python -m venv .venv
# activate the environment
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```
## Live Website Link
```bash
https://varshaai-4js6.onrender.com/
```

# 🌧️ VARSHAAI

# AI/ML-Based Integrated Heavy Rainfall Early Warning and Inundation Prediction System

> **Observe. Predict. Simulate. Validate. Alert.**

VARSHAAI is an AI/ML-powered integrated disaster intelligence platform designed to provide early warning for heavy rainfall and predict rainfall-induced inundation using multi-source meteorological, satellite, radar, observational, numerical weather prediction and geospatial data.

The system integrates satellite observations, Doppler Weather Radar, Automatic Weather Stations (AWS), Automatic Rain Gauges (ARG), Numerical Weather Prediction (NWP), Digital Elevation Models (DEM), Land Use/Land Cover (LULC), drainage networks and historical observations.

VARSHAAI transforms heterogeneous environmental data into a common analysis framework and applies AI-based rainfall forecasting, NWP post-processing, rainfall-runoff analysis, inundation prediction, validation and risk-based alert generation.

The final output is presented through an interactive web-based disaster command center that allows users to understand rainfall conditions, forecast rainfall, flood risk, validation results and alerts from a single interface.

---

# 📌 SIH PROBLEM STATEMENT

**Problem Statement ID:** SIH26071

**Title:**

> AI/ML-Based Integrated Heavy Rainfall Early Warning and Inundation Prediction System using Satellite, Radar, Observational Weather and Numerical Weather Prediction Model Data

**Organization:** Ministry of Earth Sciences (MoES)

**Department:** India Meteorological Department (IMD)

**Category:** Software

**Theme:** Disaster Management

**Primary Demonstration Region:** Chennai District, Tamil Nadu, India

---

# 🚨 PROBLEM

Heavy rainfall events can rapidly create urban flooding, waterlogging, infrastructure damage, transportation disruption and risks to human life.

The major challenge is that weather and environmental information is distributed across different sources.

Satellite systems provide large-area observations.

Weather radar provides high-resolution precipitation information.

AWS and ARG stations provide ground-level measurements.

NWP systems provide future atmospheric conditions.

DEM, drainage and LULC datasets describe the physical environment.

However, these sources operate at different:

- Spatial resolutions
- Temporal resolutions
- Coordinate systems
- Data formats
- Measurement characteristics
- Quality levels

Therefore, simply collecting the data is not enough.

The real challenge is to create a unified system that can:

1. Collect multi-source data.
2. Clean and validate the data.
3. Harmonize spatial resolutions.
4. Harmonize temporal resolutions.
5. Forecast heavy rainfall.
6. Correct NWP forecast biases.
7. Predict rainfall-induced inundation.
8. Validate the predictions.
9. Generate meaningful alerts.
10. Present all information to disaster-management authorities.

VARSHAAI addresses this complete chain.

---

# 💡 SOLUTION

VARSHAAI follows an end-to-end disaster intelligence architecture.

The system follows the principle:

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
PREDICT
   ↓
SIMULATE
   ↓
VALIDATE
   ↓
ALERT
   ↓
ACTION
```

The prototype intentionally labels simulated values. Replace the adapter layer with verified data providers before operational use.
