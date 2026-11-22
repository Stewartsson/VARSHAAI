import { useState, useEffect, useMemo } from 'react'
import { apiFetch } from '../api'
import { MapContainer, TileLayer, Marker, Popup, Circle, Polygon } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import {
  Radio,
  MapPin,
  Waves,
  CloudRain,
  Thermometer,
  Wind,
  Gauge,
  Droplet,
  ShieldCheck,
  ShieldAlert,
  Activity,
  CheckCircle2,
  RefreshCw,
  Navigation,
  Compass,
  AlertTriangle,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import '../styles/CityHub.css'

// Fix Leaflet default marker icons in Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Custom Radar Center Marker
const radarCenterIcon = new L.DivIcon({
  className: 'radar-marker-pulse',
  html: '<div class="radar-dot"></div><div class="radar-wave"></div>',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
})

// Custom Hotspot Marker
const hotspotIcon = new L.DivIcon({
  className: 'hotspot-marker',
  html: '<div class="hotspot-pin"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

function CityHub() {
  const [cities, setCities] = useState([])
  const [selectedCityId, setSelectedCityId] = useState('chennai')
  const [cityDetail, setCityDetail] = useState(null)
  const [loadingList, setLoadingList] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  // Load summary list of all 5 cities
  async function loadCities() {
    try {
      setError('')
      const response = await apiFetch(`/api/cities?t=${Date.now()}`)
      if (!response.ok) throw new Error(`Cities API returned HTTP ${response.status}`)
      const data = await response.json()
      setCities(data.cities || [])
    } catch (err) {
      setError(err.message || 'Failed to load cities.')
    } finally {
      setLoadingList(false)
    }
  }

  // Load in-depth detail for selected city
  async function loadCityDetail(cityId) {
    try {
      setLoadingDetail(true)
      const response = await apiFetch(`/api/cities/${cityId}?t=${Date.now()}`)
      if (!response.ok) throw new Error(`City detail returned HTTP ${response.status}`)
      const data = await response.json()
      setCityDetail(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingDetail(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadCities()
    loadCityDetail('chennai')
  }, [])

  function handleSelectCity(id) {
    setSelectedCityId(id)
    loadCityDetail(id)
  }

  const selectedMeta = cityDetail?.city
  const weather = cityDetail?.current_weather
  const risk = cityDetail?.risk || {}
  const radar = cityDetail?.radar || {}
  const hotspots = cityDetail?.hotspots || []
  const basins = cityDetail?.drainage_basins || []
  const timeline = cityDetail?.timeline_48h || []

  const chartData = useMemo(() => {
    return timeline.slice(0, 24).map((item) => {
      const d = new Date(item.time_iso)
      const timeStr = d.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata',
      })
      return {
        time: timeStr,
        rainfall: item.precipitation_mm,
        temperature: item.temperature_c,
      }
    })
  }, [timeline])

  const riskClass =
    risk.level === 'RED'
      ? 'risk-red'
      : risk.level === 'ORANGE'
        ? 'risk-orange'
        : risk.level === 'YELLOW'
          ? 'risk-yellow'
          : 'risk-green'

  return (
    <div className="city-hub-page">
      {/* HEADER */}
      <div className="city-hub-header">
        <div>
          <div className="city-hub-breadcrumb">
            VARSHAAI / MULTI-CITY RADAR / NATIONAL GRID
          </div>
          <div className="city-hub-title-row">
            <div className="city-hub-icon">
              <Radio size={28} />
            </div>
            <div>
              <h1>National Urban Flood Grid</h1>
              <p>
                Multi-metro Doppler Weather Radar (DWR) integration, live atmospheric telemetry, and hydrodynamic flash-flood nowcasting.
              </p>
            </div>
          </div>
        </div>

        <button
          className="city-hub-refresh"
          disabled={refreshing}
          onClick={() => {
            setRefreshing(true)
            loadCities()
            loadCityDetail(selectedCityId)
          }}
        >
          <RefreshCw size={15} className={refreshing ? 'spin' : ''} />
          {refreshing ? 'Refreshing...' : 'Refresh All Metros'}
        </button>
      </div>

      {error && (
        <div className="city-hub-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* METRO SELECTOR CARDS (5 CITIES) */}
      <section className="city-selector-section">
        <div className="section-title-strip">
          <Compass size={16} />
          <span>SELECT METROPOLITAN RADAR STATION</span>
        </div>

        <div className="city-cards-grid">
          {cities.map((c) => {
            const isSelected = c.id === selectedCityId
            const cRisk = c.risk || {}
            const cWeather = c.current_weather || {}
            return (
              <div
                key={c.id}
                className={`city-card ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectCity(c.id)}
              >
                <div className="city-card-header">
                  <div>
                    <h3>{c.name}</h3>
                    <span>{c.state}</span>
                  </div>
                  <span className={`city-risk-pill ${cRisk.level?.toLowerCase() || 'green'}`}>
                    {cRisk.level || 'GREEN'}
                  </span>
                </div>

                <div className="city-card-weather">
                  <div className="city-weather-stat">
                    <CloudRain size={16} />
                    <span>{cWeather.precipitation_mm ?? 0} mm/hr</span>
                  </div>
                  <div className="city-weather-stat">
                    <Thermometer size={16} />
                    <span>{cWeather.temperature_c ?? '--'}°C</span>
                  </div>
                </div>

                <div className="city-card-radar">
                  <div className="radar-status-dot"></div>
                  <span className="radar-station-name">{c.radar_name}</span>
                </div>

                <div className="city-card-footer">
                  <small>{c.hotspot_count} critical flood hotspots</small>
                  <ChevronRight size={15} className="city-arrow" />
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* SELECTED CITY DETAIL DASHBOARD */}
      {selectedMeta && (
        <div className="city-detail-view">
          {/* CITY BANNER */}
          <div className={`city-hero-banner ${riskClass}`}>
            <div className="hero-details">
              <div className="hero-kicker">
                <Navigation size={15} />
                <span>ACTIVE URBAN BASIN • {selectedMeta.name.toUpperCase()}</span>
              </div>
              <h2>{selectedMeta.name} Disaster Intelligence</h2>
              <p>
                Radar Station: <strong>{radar.name}</strong> • Elevation: <strong>{selectedMeta.terrain_elevation_m}m AMSL</strong> • Coordinates: <strong>{selectedMeta.lat}°N, {selectedMeta.lon}°E</strong>
              </p>
            </div>

            <div className="hero-risk-box">
              <span>OPERATIONAL STATUS</span>
              <strong className={riskClass}>{risk.level} ALERT</strong>
              <small>{risk.label}</small>
            </div>
          </div>

          {/* TELEMETRY STRIP */}
          {weather && (
            <div className="city-telemetry-strip">
              <div className="city-telemetry-box">
                <CloudRain size={18} className="telemetry-icon-blue" />
                <div>
                  <span>PRECIPITATION</span>
                  <strong>{weather.precipitation_mm ?? 0} mm/hr</strong>
                  <small>{weather.precipitation_mm === 0 ? 'Dry / Clear' : 'Active Rainfall'}</small>
                </div>
              </div>

              <div className="city-telemetry-box">
                <Thermometer size={18} className="telemetry-icon-amber" />
                <div>
                  <span>TEMPERATURE</span>
                  <strong>{weather.temperature_c ?? '--'} °C</strong>
                  <small>Surface Ambient</small>
                </div>
              </div>

              <div className="city-telemetry-box">
                <Droplet size={18} className="telemetry-icon-emerald" />
                <div>
                  <span>HUMIDITY</span>
                  <strong>{weather.humidity_percent ?? '--'}%</strong>
                  <small>Atmospheric</small>
                </div>
              </div>

              <div className="city-telemetry-box">
                <Wind size={18} className="telemetry-icon-purple" />
                <div>
                  <span>WIND SPEED</span>
                  <strong>{weather.wind_speed_kmh ?? '--'} km/h</strong>
                  <small>Surface Velocity</small>
                </div>
              </div>

              <div className="city-telemetry-box">
                <Gauge size={18} className="telemetry-icon-pink" />
                <div>
                  <span>BAROMETER</span>
                  <strong>{weather.pressure_hpa ?? '--'} hPa</strong>
                  <small>Surface Pressure</small>
                </div>
              </div>
            </div>
          )}

          {/* MAP & RADAR SPECIFICATION SPLIT */}
          <div className="city-map-split">
            {/* INTERACTIVE CITY MAP */}
            <div className="city-map-card">
              <div className="map-card-header">
                <div>
                  <MapPin size={17} />
                  <span>{selectedMeta.name.toUpperCase()} HYDROLOGICAL & RADAR MAP</span>
                </div>
                <div className="map-legend-pills">
                  <span className="legend-radar">● Radar Scan (250km)</span>
                  <span className="legend-hotspot">▲ Critical Hotspot</span>
                </div>
              </div>

              <div className="leaflet-map-wrapper">
                <MapContainer
                  key={`${selectedMeta.lat}-${selectedMeta.lon}`}
                  center={[selectedMeta.lat, selectedMeta.lon]}
                  zoom={11}
                  scrollWheelZoom={false}
                  className="city-leaflet-container"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  />

                  {/* Doppler Radar Scan Coverage Circle */}
                  <Circle
                    center={[selectedMeta.lat, selectedMeta.lon]}
                    radius={25000} // 25km immediate urban surveillance
                    pathOptions={{
                      color: '#0284c7',
                      fillColor: '#38bdf8',
                      fillOpacity: 0.08,
                      weight: 1.5,
                      dashArray: '4, 6',
                    }}
                  />

                  {/* Radar Station Center */}
                  <Marker
                    position={[selectedMeta.lat, selectedMeta.lon]}
                    icon={radarCenterIcon}
                  >
                    <Popup>
                      <div className="map-popup-card">
                        <h4>{radar.name}</h4>
                        <p>Operating Band: {radar.band}</p>
                        <p>Status: {radar.status}</p>
                      </div>
                    </Popup>
                  </Marker>

                  {/* Hotspot Markers */}
                  {hotspots.map((h, idx) => (
                    <Marker key={idx} position={[h.lat, h.lon]} icon={hotspotIcon}>
                      <Popup>
                        <div className="map-popup-card">
                          <h4>{h.name}</h4>
                          <p>Hazard: {h.type}</p>
                          <p>Risk Profile: <strong>{h.risk}</strong></p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>
            </div>

            {/* RADAR TECHNICAL SPECS & DRAINAGE BASINS */}
            <div className="city-sidebar-specs">
              {/* RADAR SPEC CARD */}
              <div className="specs-card">
                <div className="specs-card-title">
                  <Radio size={16} />
                  <span>DOPPLER WEATHER RADAR SPECS</span>
                </div>
                <div className="specs-list">
                  <div className="spec-item">
                    <span>STATION ID</span>
                    <strong>{radar.station_code || 'IMD_DWR'}</strong>
                  </div>
                  <div className="spec-item">
                    <span>OPERATING BAND</span>
                    <strong>{radar.band}</strong>
                  </div>
                  <div className="spec-item">
                    <span>SURVEILLANCE RADIUS</span>
                    <strong>{radar.range_km} km Doppler Mode</strong>
                  </div>
                  <div className="spec-item">
                    <span>SCAN CYCLE</span>
                    <strong>{radar.scan_interval_min} minutes</strong>
                  </div>
                  <div className="spec-item">
                    <span>AGENCY</span>
                    <strong>{radar.provider}</strong>
                  </div>
                  <div className="spec-item">
                    <span>QC GROUND CLUTTER FILTER</span>
                    <strong className="text-emerald">Active (dBZ &gt; 65 Filtered)</strong>
                  </div>
                </div>
              </div>

              {/* DRAINAGE BASINS CARD */}
              <div className="specs-card">
                <div className="specs-card-title">
                  <Waves size={16} />
                  <span>URBAN DRAINAGE & RIVER BASINS</span>
                </div>
                <div className="basins-tags">
                  {basins.map((basin, i) => (
                    <span key={i} className="basin-tag">
                      {basin}
                    </span>
                  ))}
                </div>
              </div>

              {/* CRITICAL HOTSPOTS LIST */}
              <div className="specs-card">
                <div className="specs-card-title">
                  <AlertTriangle size={16} />
                  <span>MONITORED FLOOD HOTSPOTS</span>
                </div>
                <div className="hotspots-list">
                  {hotspots.map((h, i) => (
                    <div key={i} className="hotspot-item">
                      <div>
                        <strong>{h.name}</strong>
                        <small>{h.type}</small>
                      </div>
                      <span className={`hotspot-risk-badge ${h.risk.toLowerCase()}`}>
                        {h.risk}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 24-HOUR FORECAST CHART */}
          <section className="city-forecast-chart-card">
            <div className="chart-card-header">
              <div>
                <Sparkles size={16} />
                <span>24-HOUR PRECIPITATION TIMELINE • {selectedMeta.name.toUpperCase()}</span>
              </div>
              <small>Open-Meteo GFS Forecast Coupled</small>
            </div>

            <div className="city-chart-wrap">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#17384a" />
                  <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={{ stroke: '#17384a' }} minTickGap={20} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} width={45} label={{ value: 'mm/hr', angle: -90, position: 'insideLeft', fill: '#4d8db7', fontSize: 9 }} />
                  <Tooltip
                    contentStyle={{ background: '#091c28', border: '1px solid #1f4b61', borderRadius: '8px', color: '#e2e8f0', fontSize: '11px' }}
                    formatter={(val) => [`${Number(val).toFixed(2)} mm/hr`, 'Precipitation']}
                  />
                  <Line type="monotone" dataKey="rainfall" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 3, fill: '#38bdf8' }} activeDot={{ r: 6 }} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

export default CityHub
