# RainGuard AI — SIH 26071

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

The prototype intentionally labels simulated values. Replace the adapter layer with verified data providers before operational use.
