import { useState } from 'react'
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Circle,
  Popup,
  Polygon,
  ZoomControl,
} from 'react-leaflet'
import { Radio, Layers, Satellite, Zap } from 'lucide-react'

import 'leaflet/dist/leaflet.css'
import '../styles/MapView.css'

function MapView({ mode = 'live', rainfall = 0.0 }) {
  /*
   * Prototype center:
   * Chennai Metropolitan Region (13.0827°N, 80.2707°E)
   */
  const center = [13.0827, 80.2707]
  const isSimulation = mode === 'simulation' || rainfall > 25.0
  const [activeLayer, setActiveLayer] = useState('radar') // 'radar' | 'satellite' | 'cyber'
  const [sweepActive, setSweepActive] = useState(true)

  const riskZones = isSimulation
    ? [
        {
          id: 1,
          position: [13.0827, 80.2707],
          name: 'Chennai Central (AWS-01)',
          rainfall: '168 mm',
          floodDepth: '0.74 m',
          risk: 'HIGH',
          stationType: 'DWR Doppler Primary',
        },
        {
          id: 2,
          position: [13.1200, 80.2500],
          name: 'North Zone (Madhavaram)',
          rainfall: '132 mm',
          floodDepth: '0.42 m',
          risk: 'MODERATE',
          stationType: 'Basin Rain Gauge',
        },
        {
          id: 3,
          position: [13.0100, 80.2200],
          name: 'South Zone (Guindy AWS)',
          rainfall: '104 mm',
          floodDepth: '0.28 m',
          risk: 'LOW',
          stationType: 'Urban Runoff Telemetry',
        },
        {
          id: 4,
          position: [12.9716, 80.2184],
          name: 'Velachery Lowland Sump',
          rainfall: '182 mm',
          floodDepth: '0.86 m',
          risk: 'HIGH',
          stationType: 'Hydrodynamic Inundation Node',
        },
        {
          id: 5,
          position: [13.0475, 80.2090],
          name: 'Koyambedu Drainage Hub',
          rainfall: '124 mm',
          floodDepth: '0.38 m',
          risk: 'MODERATE',
          stationType: 'Sluice Gate Telemetry',
        },
      ]
    : [
        {
          id: 1,
          position: [13.0827, 80.2707],
          name: 'Chennai Central (AWS-01)',
          rainfall: `${rainfall.toFixed(1)} mm`,
          floodDepth: '0.00 m',
          risk: rainfall > 5 ? 'MODERATE' : 'CLEAR',
          stationType: 'DWR Doppler Primary',
        },
        {
          id: 2,
          position: [13.1200, 80.2500],
          name: 'North Zone (Madhavaram)',
          rainfall: `${rainfall.toFixed(1)} mm`,
          floodDepth: '0.00 m',
          risk: 'CLEAR',
          stationType: 'Basin Rain Gauge',
        },
        {
          id: 3,
          position: [13.0100, 80.2200],
          name: 'South Zone (Guindy AWS)',
          rainfall: `${rainfall.toFixed(1)} mm`,
          floodDepth: '0.00 m',
          risk: 'CLEAR',
          stationType: 'Urban Runoff Telemetry',
        },
        {
          id: 4,
          position: [12.9716, 80.2184],
          name: 'Velachery Lowland Sump',
          rainfall: `${(rainfall * 1.1).toFixed(1)} mm`,
          floodDepth: '0.00 m',
          risk: 'CLEAR',
          stationType: 'Hydrodynamic Inundation Node',
        },
        {
          id: 5,
          position: [13.0475, 80.2090],
          name: 'Koyambedu Drainage Hub',
          rainfall: `${rainfall.toFixed(1)} mm`,
          floodDepth: '0.00 m',
          risk: 'CLEAR',
          stationType: 'Sluice Gate Telemetry',
        },
      ]

  const floodArea = [
    [13.1100, 80.2400],
    [13.1300, 80.2600],
    [13.1200, 80.3000],
    [13.0800, 80.3100],
    [13.0500, 80.2800],
    [13.0600, 80.2500],
  ]

  // Safe tile URLs with NO API KEY requirements
  const tileConfig = {
    radar: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; OpenStreetMap contributors | VARSHAAI Doppler Radar',
      tileClass: 'cosmic-radar-tiles',
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Esri, Maxar, Earthstar Geographics | High-Res Satellite',
      tileClass: 'satellite-tiles',
    },
    cyber: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; OpenStreetMap contributors | Cyber Vector Mode',
      tileClass: 'cyber-dark-tiles',
    },
  }

  const currentTile = tileConfig[activeLayer] || tileConfig.radar

  return (
    <div className="map-wrapper cosmic-map-theme">
      {/* Top Floating Control Bar */}
      <div className="map-glass-toolbar">
        <div className="map-brand-chip">
          <Radio size={14} className="radar-pulse-icon" />
          <span>DWR CHENNAI S-BAND RADAR</span>
          <span className="live-tag">LIVE NOWCAST</span>
        </div>

        <div className="map-layer-pills">
          <button
            type="button"
            className={`map-layer-pill ${activeLayer === 'radar' ? 'active' : ''}`}
            onClick={() => setActiveLayer('radar')}
          >
            <Zap size={12} />
            <span>Cosmic Radar</span>
          </button>
          <button
            type="button"
            className={`map-layer-pill ${activeLayer === 'satellite' ? 'active' : ''}`}
            onClick={() => setActiveLayer('satellite')}
          >
            <Satellite size={12} />
            <span>Satellite</span>
          </button>
          <button
            type="button"
            className={`map-layer-pill ${activeLayer === 'cyber' ? 'active' : ''}`}
            onClick={() => setActiveLayer('cyber')}
          >
            <Layers size={12} />
            <span>Cyber Dark</span>
          </button>
        </div>
      </div>

      {/* Radar Sweep Animated Simulation Overlay */}
      {sweepActive && activeLayer === 'radar' && (
        <div className="radar-sweep-overlay" aria-hidden="true">
          <div className="radar-sweep-beam"></div>
          <div className="radar-crosshair-h"></div>
          <div className="radar-crosshair-v"></div>
        </div>
      )}

      <MapContainer
        center={center}
        zoom={11}
        scrollWheelZoom={true}
        zoomControl={false}
        className={`varshaai-map ${currentTile.tileClass}`}
      >
        <ZoomControl position="bottomright" />

        {/* Dynamic Basemap Tile Layer */}
        <TileLayer
          key={activeLayer}
          attribution={currentTile.attribution}
          url={currentTile.url}
        />

        {/* Doppler Radar Range Rings centered on Chennai */}
        <Circle
          center={center}
          radius={10000}
          pathOptions={{
            color: 'rgba(167, 139, 250, 0.45)',
            weight: 1,
            dashArray: '4, 8',
            fillColor: 'rgba(124, 58, 237, 0.04)',
            fillOpacity: 0.1,
          }}
        />
        <Circle
          center={center}
          radius={25000}
          pathOptions={{
            color: 'rgba(139, 92, 246, 0.35)',
            weight: 1,
            dashArray: '6, 12',
            fillColor: 'transparent',
          }}
        />
        <Circle
          center={center}
          radius={45000}
          pathOptions={{
            color: 'rgba(99, 102, 241, 0.25)',
            weight: 1,
            dashArray: '8, 16',
            fillColor: 'transparent',
          }}
        />

        {/* Flood Prediction / Monitoring Area Polygon */}
        <Polygon
          positions={floodArea}
          pathOptions={{
            color: isSimulation ? '#f43f5e' : '#a855f7',
            fillColor: isSimulation ? '#f43f5e' : '#8b5cf6',
            fillOpacity: isSimulation ? 0.35 : 0.12,
            weight: 2,
            dashArray: isSimulation ? null : '5, 8',
          }}
        >
          <Popup>
            <div className="map-popup glass-popup">
              <div className="popup-badge">HYDRODYNAMIC DOMAIN</div>
              <strong>
                {isSimulation
                  ? 'Severe Inundation Corridor (Simulated Cloudburst)'
                  : 'Active CartoDEM Catchment Monitoring'}
              </strong>
              <div className="popup-stats">
                <div>
                  <span className="lbl">Status</span>
                  <span className={`val ${isSimulation ? 'danger' : 'safe'}`}>
                    {isSimulation ? 'CRITICAL INUNDATION' : 'NOMINAL DRAINAGE'}
                  </span>
                </div>
                <div>
                  <span className="lbl">Peak Water Depth</span>
                  <span className="val">{isSimulation ? '0.74 m' : '0.00 m'}</span>
                </div>
              </div>
            </div>
          </Popup>
        </Polygon>

        {/* High-Tech Telemetry Observation Nodes */}
        {riskZones.map((zone) => {
          const isHigh = zone.risk === 'HIGH'
          const isMod = zone.risk === 'MODERATE'
          const markerColor = isHigh ? '#f43f5e' : isMod ? '#f59e0b' : '#38bdf8'
          const markerGlow = isHigh
            ? 'rgba(244, 63, 94, 0.4)'
            : isMod
            ? 'rgba(245, 158, 11, 0.35)'
            : 'rgba(56, 189, 248, 0.35)'

          return (
            <CircleMarker
              key={zone.id}
              center={zone.position}
              radius={isHigh ? 11 : 9}
              pathOptions={{
                color: markerColor,
                fillColor: markerColor,
                fillOpacity: 0.85,
                weight: 3,
              }}
            >
              <Popup>
                <div className="map-popup glass-popup">
                  <div className="popup-header">
                    <span className="station-type">{zone.stationType}</span>
                    <span className={`risk-pill ${zone.risk.toLowerCase()}`}>
                      {zone.risk}
                    </span>
                  </div>
                  <strong>{zone.name}</strong>
                  <div className="popup-grid">
                    <div className="popup-stat-box">
                      <span className="stat-label">Precipitation</span>
                      <span className="stat-val">{zone.rainfall}</span>
                    </div>
                    <div className="popup-stat-box">
                      <span className="stat-label">Inundation</span>
                      <span className="stat-val">{zone.floodDepth}</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>

      {/* Modern Glass Bottom Legend */}
      <div className="map-legend glass-legend">
        <div className="legend-title">HYDRO-HAZARD RISK MATRIX</div>
        <div className="legend-items-row">
          <div className="legend-item">
            <span className="legend-dot low"></span>
            <span>Nominal / Clear</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot moderate"></span>
            <span>Advisory (Rain Alert)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot high"></span>
            <span>Severe Inundation</span>
          </div>
        </div>
      </div>

      {/* Floating Status Pill */}
      <div className="map-layer-status glass-status-pill">
        <span className="beacon-dot"></span>
        <span>
          {mode === 'simulation'
            ? 'SYNTHETIC SCENARIO: 180MM CLOUDBURST'
            : 'LIVE DWR RADAR FEED ACTIVE'}
        </span>
      </div>
    </div>
  )
}

export default MapView
