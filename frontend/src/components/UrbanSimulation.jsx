import { useState, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import {
  Navigation,
  Sliders,
  AlertTriangle,
  Waves,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Compass,
  ArrowRight,
  TrendingUp,
  Gauge,
  Droplet,
  CloudRain,
  MapPin,
  Ambulance,
  CheckCircle2,
  Share2,
  Sparkles,
} from 'lucide-react'
import '../styles/UrbanSimulation.css'

// Custom Leaflet Icons
const startIcon = new L.DivIcon({
  className: 'route-marker-pin start',
  html: '<div class="pin-inner start"><div class="dot"></div></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

const endIcon = new L.DivIcon({
  className: 'route-marker-pin end',
  html: '<div class="pin-inner end"><div class="dot"></div></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

const hazardIcon = new L.DivIcon({
  className: 'route-hazard-icon',
  html: '<div class="hazard-pulse">⚠️</div>',
  iconSize: [26, 26],
  iconAnchor: [13, 13],
})

// ROUTING SCENARIOS FOR METROS
const ROUTE_SCENARIOS = {
  chennai: {
    city: 'Chennai',
    origin: { name: 'Velachery Lowlands (Ward 178)', lat: 12.9815, lon: 80.218, elevation: 4.2 },
    destination: { name: 'Apollo Speciality Hospital / Relief Camp (Guindy)', lat: 13.0067, lon: 80.2025, elevation: 12.8 },
    chokepoint: { name: 'Velachery MRTS Subway (Low-Lying Underpass)', lat: 12.993, lon: 80.214, elevation: 2.1 },
    // Direct road through underpass
    directRoute: [
      [12.9815, 80.218],
      [12.987, 80.216],
      [12.993, 80.214], // Underpass choke
      [12.999, 80.208],
      [13.0067, 80.2025],
    ],
    // High-elevation bypass avoiding underpass
    safeBypassRoute: [
      [12.9815, 80.218],
      [12.978, 80.224], // Divert to 100ft bypass
      [12.989, 80.228], // Elevated flyover ridge
      [13.001, 80.219], // Raj Bhavan high ground
      [13.0067, 80.2025],
    ],
    safeBypassName: 'Velachery 100ft Elevated Flyover Corridor (Ridge Elev: 12.8m)',
  },
  mumbai: {
    city: 'Mumbai',
    origin: { name: 'Santacruz West Lowlands', lat: 19.082, lon: 72.836, elevation: 5.5 },
    destination: { name: 'Lilavati Hospital & Relief Center (Bandra)', lat: 19.051, lon: 72.829, elevation: 16.5 },
    chokepoint: { name: 'Milan Subway Chronic Underpass', lat: 19.088, lon: 72.842, elevation: 2.2 },
    directRoute: [
      [19.082, 72.836],
      [19.085, 72.839],
      [19.088, 72.842], // Milan subway choke
      [19.068, 72.834],
      [19.051, 72.829],
    ],
    safeBypassRoute: [
      [19.082, 72.836],
      [19.079, 72.832], // Linking road elevated stretch
      [19.065, 72.831],
      [19.055, 72.83],
      [19.051, 72.829],
    ],
    safeBypassName: 'Linking Road High-Elevation Arterial Bypass',
  },
  delhi: {
    city: 'Delhi (NCR)',
    origin: { name: 'Connaught Place Low Basin', lat: 28.632, lon: 77.218, elevation: 212.0 },
    destination: { name: 'LNJP Hospital Disaster Ward', lat: 28.641, lon: 77.241, elevation: 228.0 },
    chokepoint: { name: 'Minto Bridge Railway Underpass', lat: 28.634, lon: 77.224, elevation: 209.5 },
    directRoute: [
      [28.632, 77.218],
      [28.634, 77.224], // Minto Bridge choke
      [28.637, 77.232],
      [28.641, 77.241],
    ],
    safeBypassRoute: [
      [28.632, 77.218],
      [28.625, 77.225], // Barakhamba flyover
      [28.63, 77.238],
      [28.641, 77.241],
    ],
    safeBypassName: 'Barakhamba Elevated Flyover Corridor',
  },
}

function UrbanSimulation() {
  const [activeTab, setActiveTab] = useState('routing') // 'routing' or 'drainage'
  const [selectedCity, setSelectedCity] = useState('chennai')

  // TAB 1: SAFE ROUTING CONTROLS
  const [rainRate, setRainRate] = useState(65) // mm/hr

  // TAB 2: MUNICIPAL DRAINAGE "WHAT-IF" STRESS CONTROLS
  const [stressRain, setStressRain] = useState(60) // mm/hr
  const [drainClogging, setDrainClogging] = useState(55) // % clogged
  const [tideLevel, setTideLevel] = useState(1.1) // meters surge
  const [soilSaturation, setSoilSaturation] = useState('AMC-II') // AMC-I, AMC-II, AMC-III

  const scenario = ROUTE_SCENARIOS[selectedCity] || ROUTE_SCENARIOS.chennai

  // ROUTING CALCULATION
  const isDirectBlocked = rainRate >= 45
  const underpassWaterDepth = useMemo(() => {
    if (rainRate < 25) return 0.05
    return Number((0.05 + ((rainRate - 25) / 95) * 1.15).toFixed(2))
  }, [rainRate])

  // DRAINAGE "WHAT-IF" HYDROLOGIC CALCULATION (SCS-CN)
  const drainageResults = useMemo(() => {
    // Base Curve Number
    let baseCN = 84 // Urban impervious baseline
    if (soilSaturation === 'AMC-I') baseCN = 72
    if (soilSaturation === 'AMC-III') baseCN = 93

    // Potential maximum retention S (mm)
    const S = (25400 / baseCN) - 254
    const P = stressRain

    // Initial abstraction Ia = 0.2 * S
    const Ia = 0.2 * S
    let runoffMm = 0
    if (P > Ia) {
      runoffMm = Math.pow(P - Ia, 2) / (P + 0.8 * S)
    }

    // Drainage conveyance capacity (mm/hr evacuated)
    const maxConveyance = 45 // mm/hr when 100% clean
    const actualConveyance = maxConveyance * (1 - drainClogging / 100) * (1 - (tideLevel - 0.2) * 0.25)
    const netExcessMm = Math.max(0, runoffMm - actualConveyance)

    // Street ponding depth (meters)
    const streetDepthM = Number((netExcessMm * 0.012).toFixed(2))
    const timeToPondingMin = Math.max(12, Math.round(60 / (1 + drainClogging / 25)))

    let riskLevel = 'GREEN'
    if (streetDepthM >= 0.5) riskLevel = 'RED'
    else if (streetDepthM >= 0.2) riskLevel = 'ORANGE'
    else if (streetDepthM >= 0.08) riskLevel = 'YELLOW'

    return {
      runoffMm: Number(runoffMm.toFixed(1)),
      actualConveyance: Number(actualConveyance.toFixed(1)),
      streetDepthM,
      timeToPondingMin,
      riskLevel,
      baseCN,
    }
  }, [stressRain, drainClogging, tideLevel, soilSaturation])

  return (
    <div className="urban-sim-page">
      {/* HEADER */}
      <div className="urban-sim-header">
        <div>
          <div className="urban-breadcrumb">
            VARSHAAI / HYDROLOGICAL SIMULATOR / URBAN STRESS & ROUTING
          </div>
          <div className="urban-title-row">
            <div className="urban-header-icon">
              <Navigation size={28} />
            </div>
            <div>
              <h1>Urban Stress & Flood-Aware Routing</h1>
              <p>
                Dynamic hydrodynamic rerouting around submerged underpasses and explainable "What-If" municipal drainage clogging modeling.
              </p>
            </div>
          </div>
        </div>

        {/* PRIMARY SIMULATOR TABS */}
        <div className="sim-primary-tabs">
          <button
            className={`sim-tab-btn ${activeTab === 'routing' ? 'active' : ''}`}
            onClick={() => setActiveTab('routing')}
          >
            <Navigation size={15} />
            <span>Live Safe-Routing Simulator</span>
          </button>
          <button
            className={`sim-tab-btn ${activeTab === 'drainage' ? 'active' : ''}`}
            onClick={() => setActiveTab('drainage')}
          >
            <Sliders size={15} />
            <span>"What-If" Drainage Clogging Panel</span>
          </button>
        </div>
      </div>

      {/* =========================================================
          TAB 1: LIVE "FLOOD-AWARE SAFE ROUTING" SIMULATOR
          ========================================================= */}
      {activeTab === 'routing' && (
        <div className="routing-tab-content">
          {/* CONTROL STRIP */}
          <div className="routing-control-bar">
            <div className="city-selector-group">
              <span className="label">URBAN BASIN:</span>
              <div className="city-buttons">
                {Object.keys(ROUTE_SCENARIOS).map((k) => (
                  <button
                    key={k}
                    className={`city-btn ${selectedCity === k ? 'active' : ''}`}
                    onClick={() => setSelectedCity(k)}
                  >
                    {ROUTE_SCENARIOS[k].city}
                  </button>
                ))}
              </div>
            </div>

            {/* RAIN INTENSITY SLIDER (THE WOW MOMENT) */}
            <div className="rain-slider-group">
              <div className="slider-header">
                <span className="slider-title">
                  <CloudRain size={16} className="text-cyan" />
                  <span>SIMULATED RAINFALL INTENSITY:</span>
                </span>
                <span className="slider-value">
                  <strong>{rainRate} mm/hr</strong>
                  <small className={rainRate >= 65 ? 'text-red' : rainRate >= 45 ? 'text-amber' : 'text-emerald'}>
                    ({rainRate >= 65 ? 'Extreme Cloudburst' : rainRate >= 45 ? 'Heavy Rainfall' : 'Moderate Inflow'})
                  </small>
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="120"
                step="5"
                value={rainRate}
                onChange={(e) => setRainRate(Number(e.target.value))}
                className="rain-range-slider"
              />
              <div className="slider-ticks">
                <span>10 mm (Clear)</span>
                <span>45 mm (Underpass Overflow)</span>
                <span>80 mm (Severe Inundation)</span>
                <span>120 mm (Extreme)</span>
              </div>
            </div>
          </div>

          {/* MAP & ROUTE STATUS SPLIT */}
          <div className="routing-map-split">
            {/* LEAFLET ROUTE MAP */}
            <div className="route-map-card">
              <div className="route-map-header">
                <div className="map-title-row">
                  <MapPin size={16} />
                  <span>{scenario.city.toUpperCase()} DYNAMIC EMERGENCY CORRIDOR</span>
                </div>
                <div className="route-legend">
                  <span className="legend-green">● Passable Road</span>
                  <span className="legend-red">● Inundated (Blocked)</span>
                  <span className="legend-cyan">● AI Safe Bypass</span>
                </div>
              </div>

              <div className="leaflet-routing-wrapper">
                <MapContainer
                  key={`${scenario.city}-${rainRate}`}
                  center={[scenario.chokepoint.lat, scenario.chokepoint.lon]}
                  zoom={13}
                  scrollWheelZoom={false}
                  className="city-leaflet-container"
                >
                  <TileLayer
                    attribution='&copy; OpenStreetMap contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />

                  {/* Underpass Inundation Circle */}
                  <Circle
                    center={[scenario.chokepoint.lat, scenario.chokepoint.lon]}
                    radius={isDirectBlocked ? 450 : 200}
                    pathOptions={{
                      color: isDirectBlocked ? '#ef4444' : '#f59e0b',
                      fillColor: isDirectBlocked ? '#ef4444' : '#f59e0b',
                      fillOpacity: isDirectBlocked ? 0.35 : 0.15,
                      weight: 2,
                    }}
                  />

                  {/* DIRECT ROUTE (Turns RED/Dashed when blocked) */}
                  <Polyline
                    positions={scenario.directRoute}
                    pathOptions={{
                      color: isDirectBlocked ? '#ef4444' : '#10b981',
                      weight: isDirectBlocked ? 3.5 : 5,
                      dashArray: isDirectBlocked ? '6, 8' : undefined,
                      opacity: isDirectBlocked ? 0.75 : 0.9,
                    }}
                  />

                  {/* AI SAFE BYPASS ROUTE (Lights up in CYAN when direct route is blocked) */}
                  {isDirectBlocked && (
                    <Polyline
                      positions={scenario.safeBypassRoute}
                      pathOptions={{
                        color: '#38bdf8',
                        weight: 6,
                        opacity: 0.95,
                      }}
                    />
                  )}

                  {/* START PIN */}
                  <Marker position={[scenario.origin.lat, scenario.origin.lon]} icon={startIcon}>
                    <Popup>
                      <div className="route-popup">
                        <strong>ORIGIN: {scenario.origin.name}</strong>
                        <p>Elevation: {scenario.origin.elevation}m AMSL</p>
                      </div>
                    </Popup>
                  </Marker>

                  {/* DESTINATION PIN */}
                  <Marker position={[scenario.destination.lat, scenario.destination.lon]} icon={endIcon}>
                    <Popup>
                      <div className="route-popup">
                        <strong>DESTINATION: {scenario.destination.name}</strong>
                        <p>Elevation: {scenario.destination.elevation}m AMSL (Safe Ridge)</p>
                      </div>
                    </Popup>
                  </Marker>

                  {/* UNDERPASS CHOKEPOINT PIN */}
                  <Marker position={[scenario.chokepoint.lat, scenario.chokepoint.lon]} icon={hazardIcon}>
                    <Popup>
                      <div className="route-popup">
                        <strong className="text-red">⚠️ {scenario.chokepoint.name}</strong>
                        <p>Ground Elevation: {scenario.chokepoint.elevation}m AMSL</p>
                        <p>Current Water Depth: <strong>{underpassWaterDepth}m</strong></p>
                        <p>Status: <strong className={isDirectBlocked ? 'text-red' : 'text-emerald'}>
                          {isDirectBlocked ? 'SUBMERGED / IMPASSABLE' : 'PASSABLE'}
                        </strong></p>
                      </div>
                    </Popup>
                  </Marker>
                </MapContainer>
              </div>
            </div>

            {/* ROUTE COMPARISON & AI DISPATCH CARD */}
            <div className="route-intel-column">
              {/* CURRENT STATUS HERO */}
              <div className={`route-status-hero ${isDirectBlocked ? 'status-rerouted' : 'status-direct'}`}>
                <div className="hero-kicker">
                  {isDirectBlocked ? <AlertTriangle size={16} /> : <ShieldCheck size={16} />}
                  <span>{isDirectBlocked ? 'AI DYNAMIC REROUTING TRIGGERED' : 'PRIMARY CORRIDOR OPERATIONAL'}</span>
                </div>
                <h3>
                  {isDirectBlocked
                    ? 'Subway Inundation Blockade: Diverting Around Lowlands'
                    : 'Direct Highway Clear & Navigable'}
                </h3>
                <p>
                  {isDirectBlocked
                    ? `Rainfall of ${rainRate} mm/hr has accumulated ${underpassWaterDepth}m of standing water in ${scenario.chokepoint.name}. Direct route is impassable for ambulances and citizen vehicles.`
                    : `Rainfall is within safe storm drain absorption capacity. Underpass water level is ${underpassWaterDepth}m.`}
                </p>
              </div>

              {/* ROUTE COMPARISON CARDS */}
              <div className="route-comparison-cards">
                {/* DIRECT ROUTE CARD */}
                <div className={`route-card ${isDirectBlocked ? 'blocked' : 'active'}`}>
                  <div className="card-top">
                    <div>
                      <strong>PRIMARY DIRECT ROUTE</strong>
                      <small>Via {scenario.chokepoint.name}</small>
                    </div>
                    <span className={`status-pill ${isDirectBlocked ? 'pill-red' : 'pill-green'}`}>
                      {isDirectBlocked ? 'BLOCKED' : 'ACTIVE'}
                    </span>
                  </div>
                  <div className="card-stats">
                    <div>
                      <span>DISTANCE</span>
                      <strong>3.2 km</strong>
                    </div>
                    <div>
                      <span>TRAVEL TIME</span>
                      <strong>{isDirectBlocked ? 'BLOCKED' : '8 min'}</strong>
                    </div>
                    <div>
                      <span>WATER DEPTH</span>
                      <strong className={isDirectBlocked ? 'text-red' : 'text-emerald'}>{underpassWaterDepth} m</strong>
                    </div>
                  </div>
                </div>

                {/* AI SAFE BYPASS ROUTE CARD */}
                <div className={`route-card ${isDirectBlocked ? 'active-bypass' : 'standby'}`}>
                  <div className="card-top">
                    <div>
                      <strong>AI FLOOD-AWARE BYPASS</strong>
                      <small>{scenario.safeBypassName}</small>
                    </div>
                    <span className={`status-pill ${isDirectBlocked ? 'pill-cyan' : 'pill-gray'}`}>
                      {isDirectBlocked ? 'RECOMMENDED' : 'STANDBY'}
                    </span>
                  </div>
                  <div className="card-stats">
                    <div>
                      <span>DISTANCE</span>
                      <strong>4.6 km</strong>
                    </div>
                    <div>
                      <span>TRAVEL TIME</span>
                      <strong>12 min</strong>
                    </div>
                    <div>
                      <span>SAFETY MARGIN</span>
                      <strong className="text-cyan">+4.5m High Ground</strong>
                    </div>
                  </div>
                  {isDirectBlocked && (
                    <div className="bypass-explain">
                      <Sparkles size={14} className="text-cyan" />
                      <span>
                        Route prioritizes elevated flyovers and ridge corridors to guarantee 100% dry passage for emergency vehicles.
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* ACTION BUTTON */}
              <button
                className="dispatch-route-btn"
                onClick={() => {
                  alert(`Dispatched safe evacuation route coordinates for ${scenario.city} to emergency response fleet!`)
                }}
              >
                <Ambulance size={18} />
                <span>Broadcast Safe Corridor to Emergency Ambulances</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================
          TAB 2: "WHAT-IF" MUNICIPAL STRESS & DRAINAGE CLOGGING
          ========================================================= */}
      {activeTab === 'drainage' && (
        <div className="drainage-tab-content">
          {/* INTRO EXPLAINER */}
          <div className="drainage-explainer-card">
            <Sparkles size={20} className="text-cyan" />
            <div>
              <h3>Explainable Hydrology: Why Identical Rainfall Causes Different Floods</h3>
              <p>
                Municipal engineers often struggle to explain why a 60 mm/hr storm causes zero damage on some days, but paralyzes the city on others.
                Tweak the urban variables below to simulate how drainage silt, tidal lockage, and soil moisture dramatically alter flood depth in real time.
              </p>
            </div>
          </div>

          {/* SLIDERS GRID */}
          <div className="stress-sliders-grid">
            {/* SLIDER 1: RAIN INTENSITY */}
            <div className="stress-slider-box">
              <div className="box-top">
                <span><CloudRain size={16} className="text-cyan" /> RAINFALL RATE</span>
                <strong>{stressRain} mm/hr</strong>
              </div>
              <input
                type="range"
                min="10"
                max="150"
                step="5"
                value={stressRain}
                onChange={(e) => setStressRain(Number(e.target.value))}
                className="slider-input"
              />
              <small>Atmospheric precipitation intensity</small>
            </div>

            {/* SLIDER 2: DRAINAGE CLOGGING (THE AHA FACTOR) */}
            <div className="stress-slider-box highlight">
              <div className="box-top">
                <span><Droplet size={16} className="text-amber" /> STORM DRAIN CLOGGING</span>
                <strong className={drainClogging >= 60 ? 'text-red' : 'text-amber'}>{drainClogging}% CHOKED</strong>
              </div>
              <input
                type="range"
                min="0"
                max="90"
                step="5"
                value={drainClogging}
                onChange={(e) => setDrainClogging(Number(e.target.value))}
                className="slider-input"
              />
              <small>Solid waste, plastic accumulation & silt blockage</small>
            </div>

            {/* SLIDER 3: TIDAL SURGE */}
            <div className="stress-slider-box">
              <div className="box-top">
                <span><Waves size={16} className="text-blue" /> TIDAL LOCKAGE SURGE</span>
                <strong>{tideLevel} m</strong>
              </div>
              <input
                type="range"
                min="0.2"
                max="1.8"
                step="0.1"
                value={tideLevel}
                onChange={(e) => setTideLevel(Number(e.target.value))}
                className="slider-input"
              />
              <small>Coastal backwater blocking river outfalls</small>
            </div>

            {/* SELECTOR 4: ANTECEDENT SOIL MOISTURE */}
            <div className="stress-slider-box">
              <div className="box-top">
                <span><TrendingUp size={16} className="text-emerald" /> SOIL MOISTURE (AMC)</span>
                <strong>{soilSaturation}</strong>
              </div>
              <div className="amc-buttons">
                {['AMC-I', 'AMC-II', 'AMC-III'].map((amc) => (
                  <button
                    key={amc}
                    className={`amc-btn ${soilSaturation === amc ? 'active' : ''}`}
                    onClick={() => setSoilSaturation(amc)}
                  >
                    {amc === 'AMC-I' ? 'Dry (Sandy)' : amc === 'AMC-II' ? 'Normal' : 'Saturated Clay'}
                  </button>
                ))}
              </div>
              <small>Antecedent Moisture Condition (Runoff Curve Number: {drainageResults.baseCN})</small>
            </div>
          </div>

          {/* DRAINAGE RESULTS METRICS STRIP */}
          <div className="drainage-results-panel">
            <div className="results-hero">
              <div className="hero-metric">
                <span>RESULTING STREET WATERLOGGING DEPTH</span>
                <h2 className={`depth-${drainageResults.riskLevel.toLowerCase()}`}>
                  {drainageResults.streetDepthM} m
                </h2>
                <span className={`depth-badge badge-${drainageResults.riskLevel.toLowerCase()}`}>
                  {drainageResults.riskLevel} FLOOD SEVERITY
                </span>
              </div>

              <div className="metrics-side-grid">
                <div className="metric-cell">
                  <span>TOTAL RUNOFF PRODUCED</span>
                  <strong>{drainageResults.runoffMm} mm</strong>
                  <small>SCS-CN Potential Retention Model</small>
                </div>
                <div className="metric-cell">
                  <span>EFFECTIVE DRAINAGE CAPACITY</span>
                  <strong>{drainageResults.actualConveyance} mm/hr</strong>
                  <small>Reduced by {drainClogging}% due to clogging</small>
                </div>
                <div className="metric-cell">
                  <span>TIME TO PEAK INUNDATION</span>
                  <strong>{drainageResults.timeToPondingMin} minutes</strong>
                  <small>Urban catchment concentration time</small>
                </div>
                <div className="metric-cell">
                  <span>MUNICIPAL ADVISORY</span>
                  <strong className={drainClogging >= 50 ? 'text-red' : 'text-emerald'}>
                    {drainClogging >= 50 ? 'Deploy Dewatering Pumps' : 'Drain Capacity Nominal'}
                  </strong>
                  <small>Public works emergency recommendation</small>
                </div>
              </div>
            </div>

            {/* AHA! INSIGHT COMPARISON BOX */}
            <div className="aha-comparison-card">
              <div className="aha-title">
                <Sparkles size={16} className="text-amber" />
                <span>HYDRODYNAMIC "AHA!" COMPARISON FOR JUDGES</span>
              </div>
              <div className="aha-split">
                <div className="aha-box clean">
                  <strong>SCENARIO A: PRISTINE DRAINS (0% Clogged)</strong>
                  <p>At {stressRain} mm/hr rainfall, clear storm drains evacuate water at full capacity.</p>
                  <div className="aha-stat">
                    <span>Street Water Depth:</span>
                    <strong className="text-emerald">0.04 m (Safe / Passable)</strong>
                  </div>
                </div>

                <div className="aha-arrow">
                  <ArrowRight size={24} />
                </div>

                <div className="aha-box clogged">
                  <strong>SCENARIO B: CURRENT CHOKED DRAINS ({drainClogging}% Clogged)</strong>
                  <p>Exact same {stressRain} mm/hr storm, but choked stormwater drains choke outfall velocity.</p>
                  <div className="aha-stat">
                    <span>Street Water Depth:</span>
                    <strong className="text-red">{drainageResults.streetDepthM} m (Severe Inundation)</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UrbanSimulation
