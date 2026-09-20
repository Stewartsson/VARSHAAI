import { useEffect, useMemo, useState } from 'react'
import {
  Waves,
  Map,
  Droplets,
  Mountain,
  TreePine,
  Activity,
  ShieldAlert,
  RefreshCw,
  Database,
  ArrowDown,
  CheckCircle2,
  AlertTriangle,
  MapPinned,
  Layers3,
} from 'lucide-react'
import { MapContainer, TileLayer, Circle, Popup, Rectangle } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import '../styles/Inundation.css'

const ENDPOINTS = {
  demo: '/api/flood/demo',
  risk: '/api/flood/risk',
}

const CHENNAI = [13.0827, 80.2707]

const RISK_INFO = {
  0: { label: 'No Flood', className: 'risk-none' },
  1: { label: 'Low', className: 'risk-green' },
  2: { label: 'Moderate', className: 'risk-yellow' },
  3: { label: 'High', className: 'risk-orange' },
  4: { label: 'Severe', className: 'risk-red' },
}

function safeNumber(value, fallback = 0) {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function flattenGrid(grid) {
  if (!Array.isArray(grid)) return []
  return grid.flatMap((row) => (Array.isArray(row) ? row : []))
}

function getRiskLevel(risk) {
  return String(
    risk?.alert_level ??
      risk?.risk_level ??
      risk?.severity ??
      risk?.risk_code ??
      'GREEN',
  ).toUpperCase()
}

function Inundation() {
  const [floodData, setFloodData] = useState(null)
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  async function fetchJson(url) {
    const response = await fetch(`${url}?t=${Date.now()}`)
    if (!response.ok) {
      throw new Error(`${url} returned HTTP ${response.status}`)
    }
    return response.json()
  }

  async function loadData() {
    setError('')
    try {
      const [demo, risk] = await Promise.all([
        fetchJson(ENDPOINTS.demo),
        fetchJson(ENDPOINTS.risk),
      ])
      setFloodData(demo)
      setRiskData(risk)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err.message || 'Unable to load inundation data.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const depthGrid = floodData?.flood_depth_m || []
  const runoffGrid = floodData?.runoff_mm || []
  const cnGrid = floodData?.curve_number || []
  const riskGrid = floodData?.inundation?.risk_class || []

  const flatDepth = flattenGrid(depthGrid).map(Number).filter(Number.isFinite)
  const flatRunoff = flattenGrid(runoffGrid).map(Number).filter(Number.isFinite)
  const flatCN = flattenGrid(cnGrid).map(Number).filter(Number.isFinite)

  const maximumDepth = safeNumber(
    riskData?.risk?.maximum_depth_m ??
      floodData?.risk?.maximum_depth_m ??
      (flatDepth.length ? Math.max(...flatDepth) : 0),
  )

  const meanDepth = safeNumber(
    riskData?.risk?.mean_flood_depth_m ??
      floodData?.risk?.mean_flood_depth_m ??
      (flatDepth.length
        ? flatDepth.reduce((a, b) => a + b, 0) / flatDepth.length
        : 0),
  )

  const floodedFraction = safeNumber(
    riskData?.risk?.flooded_fraction ??
      floodData?.risk?.flooded_fraction ??
      0,
  )

  const confidence = safeNumber(
    riskData?.risk?.confidence ??
      floodData?.risk?.confidence ??
      0,
  )

  const riskLevel = getRiskLevel(
    riskData?.risk || floodData?.risk || {},
  )

  const riskLabel =
    riskData?.risk?.risk_label ||
    floodData?.risk?.risk_label ||
    (RISK_INFO[safeNumber(riskData?.risk?.risk_code)]?.label ?? 'Flood Risk')

  const totalCells = flatDepth.length
  const floodedCells = flatDepth.filter((value) => value >= 0.01).length

  const mapCells = useMemo(() => {
    if (!Array.isArray(depthGrid) || depthGrid.length === 0) return []

    const rows = depthGrid.length
    const cols = Array.isArray(depthGrid[0]) ? depthGrid[0].length : 0
    if (!cols) return []

    const latStep = 0.018
    const lonStep = 0.022
    const startLat = CHENNAI[0] + (rows * latStep) / 2
    const startLon = CHENNAI[1] - (cols * lonStep) / 2

    const cells = []

    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const depth = safeNumber(depthGrid[r]?.[c])
        const riskCode = safeNumber(riskGrid?.[r]?.[c], depth >= 0.6 ? 4 : depth >= 0.3 ? 3 : depth >= 0.15 ? 2 : depth >= 0.01 ? 1 : 0)

        const south = startLat - (r + 1) * latStep
        const north = startLat - r * latStep
        const west = startLon + c * lonStep
        const east = startLon + (c + 1) * lonStep

        cells.push({
          key: `${r}-${c}`,
          bounds: [[south, west], [north, east]],
          depth,
          riskCode,
        })
      }
    }

    return cells
  }, [depthGrid, riskGrid])

  const riskClass =
    riskLevel === 'RED'
      ? 'risk-red'
      : riskLevel === 'ORANGE'
        ? 'risk-orange'
        : riskLevel === 'YELLOW'
          ? 'risk-yellow'
          : 'risk-green'

  return (
    <div className="inundation-page">
      <div className="inundation-header">
        <div>
          <div className="inundation-breadcrumb">
            VARSHAAI / FLOOD INTELLIGENCE / INUNDATION
          </div>

          <div className="inundation-title-row">
            <div className="inundation-title-icon">
              <Waves size={30} />
            </div>

            <div>
              <h1>Inundation Prediction</h1>
              <p>
                Chennai flood-depth and inundation screening using rainfall,
                runoff, DEM and LULC intelligence.
              </p>
            </div>
          </div>
        </div>

        <div className="inundation-actions">
          <div className={`risk-pill ${riskClass}`}>
            <ShieldAlert size={15} />
            {riskLevel || 'CHECKING'}
          </div>

          <button
            className="inundation-refresh"
            onClick={() => {
              setRefreshing(true)
              loadData()
            }}
            disabled={refreshing}
          >
            <RefreshCw size={15} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="inundation-error">
          <AlertTriangle size={18} />
          <div>
            <strong>Flood model data could not be loaded</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      <section className="inundation-status">
        <div className="status-icon">
          <Activity size={24} />
        </div>
        <div className="status-copy">
          <span>FLOOD MODEL PIPELINE</span>
          <h2>Rainfall → Runoff → Flood Depth → Risk</h2>
          <p>
            Chennai District • SCS-CN runoff screening • DEM/LULC terrain
            adjustment • risk classification
          </p>
        </div>

        <div className="status-metrics">
          <div>
            <span>MODEL STATUS</span>
            <strong>{loading ? 'LOADING' : 'ONLINE'}</strong>
          </div>
          <div>
            <span>GRID</span>
            <strong>
              {floodData?.grid
                ? `${floodData.grid.rows} × ${floodData.grid.columns}`
                : '--'}
            </strong>
          </div>
          <div>
            <span>REGION</span>
            <strong>CHENNAI</strong>
          </div>
        </div>
      </section>

      <section className="metric-grid">
        <div className="metric-card depth-card">
          <div className="metric-card-icon"><Droplets size={21} /></div>
          <span>MAXIMUM FLOOD DEPTH</span>
          <strong>{maximumDepth.toFixed(2)} m</strong>
          <small>Modelled maximum depth</small>
        </div>

        <div className="metric-card">
          <div className="metric-card-icon"><Waves size={21} /></div>
          <span>MEAN FLOOD DEPTH</span>
          <strong>{meanDepth.toFixed(3)} m</strong>
          <small>Across modelled grid</small>
        </div>

        <div className="metric-card">
          <div className="metric-card-icon"><MapPinned size={21} /></div>
          <span>FLOODED FRACTION</span>
          <strong>{(floodedFraction * 100).toFixed(1)}%</strong>
          <small>{floodedCells} of {totalCells} grid cells</small>
        </div>

        <div className="metric-card">
          <div className="metric-card-icon"><ShieldAlert size={21} /></div>
          <span>RISK CLASS</span>
          <strong className={riskClass}>{riskLabel}</strong>
          <small>Confidence {(confidence * 100).toFixed(1)}%</small>
        </div>
      </section>

      <section className="map-section">
        <div className="panel-heading">
          <div>
            <span className="section-label">01 • SPATIAL INUNDATION</span>
            <h2>Chennai Flood Risk Map</h2>
            <p>
              Modelled flood cells are overlaid around the Chennai monitoring
              centre. The current API response is a clearly labelled prototype
              flood grid.
            </p>
          </div>

          <div className="source-chip">
            <Database size={15} />
            {floodData?.demo ? 'DEMO MODEL GRID' : 'LIVE MODEL'}
          </div>
        </div>

        <div className="map-layout">
          <div className="leaflet-wrapper">
            <MapContainer
              center={CHENNAI}
              zoom={11}
              scrollWheelZoom
              className="chennai-map"
            >
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              <Circle
                center={CHENNAI}
                radius={3500}
                pathOptions={{
                  color: '#49c8f1',
                  fillColor: '#49c8f1',
                  fillOpacity: 0.08,
                  weight: 1.5,
                }}
              >
                <Popup>
                  <strong>Chennai District</strong>
                  <br />
                  VARSHAAI inundation assessment centre
                </Popup>
              </Circle>

              {mapCells.map((cell) => {
                const info = RISK_INFO[cell.riskCode] || RISK_INFO[0]
                return (
                  <Rectangle
                    key={cell.key}
                    bounds={cell.bounds}
                    pathOptions={{
                      color:
                        cell.riskCode === 4
                          ? '#ef5b6d'
                          : cell.riskCode === 3
                            ? '#f59e62'
                            : cell.riskCode === 2
                              ? '#f1cf62'
                              : cell.riskCode === 1
                                ? '#57d49a'
                                : '#5c7484',
                      fillOpacity: cell.riskCode === 0 ? 0.03 : 0.35,
                      weight: 1,
                    }}
                  >
                    <Popup>
                      <strong>{info.label} flood cell</strong>
                      <br />
                      Flood depth: {cell.depth.toFixed(3)} m
                    </Popup>
                  </Rectangle>
                )
              })}
            </MapContainer>
          </div>

          <div className="map-side-panel">
            <div className="map-side-title">
              <Layers3 size={17} />
              RISK LEGEND
            </div>

            {[1, 2, 3, 4].map((code) => (
              <div className="legend-row" key={code}>
                <span className={`legend-dot ${RISK_INFO[code].className}`} />
                <div>
                  <strong>{RISK_INFO[code].label}</strong>
                  <small>
                    {code === 1 && '≥ 0.01 m'}
                    {code === 2 && '≥ 0.15 m'}
                    {code === 3 && '≥ 0.30 m'}
                    {code === 4 && '≥ 0.60 m'}
                  </small>
                </div>
              </div>
            ))}

            <div className="map-note">
              <Map size={17} />
              <p>
                Map cells visualize the flood-depth grid returned by the
                backend. Exact geographic flood extents require production DEM,
                drainage and georeferenced model grids.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="processing-section">
        <div className="panel-heading">
          <div>
            <span className="section-label">02 • HYDROLOGICAL PROCESSING</span>
            <h2>How VARSHAAI Estimates Inundation</h2>
            <p>Transparent decision pipeline for the SIH disaster-management workflow.</p>
          </div>
        </div>

        <div className="pipeline">
          <div className="pipeline-node">
            <div><Droplets size={23} /></div>
            <span>RAINFALL</span>
            <strong>
              {flatRunoff.length ? `${Math.max(...flatRunoff).toFixed(1)} mm runoff input` : 'Rainfall input'}
            </strong>
          </div>

          <ArrowDown className="pipeline-arrow" />

          <div className="pipeline-node">
            <div><Waves size={23} /></div>
            <span>SCS-CN</span>
            <strong>Runoff estimation</strong>
          </div>

          <ArrowDown className="pipeline-arrow" />

          <div className="pipeline-node">
            <div><Mountain size={23} /></div>
            <span>DEM</span>
            <strong>Terrain-adjusted depth</strong>
          </div>

          <ArrowDown className="pipeline-arrow" />

          <div className="pipeline-node">
            <div><TreePine size={23} /></div>
            <span>LULC</span>
            <strong>
              {flatCN.length ? `CN ${Math.min(...flatCN)}–${Math.max(...flatCN)}` : 'Land-cover factor'}
            </strong>
          </div>

          <ArrowDown className="pipeline-arrow" />

          <div className="pipeline-node final">
            <div><ShieldAlert size={23} /></div>
            <span>RISK ENGINE</span>
            <strong>{riskLevel}</strong>
          </div>
        </div>
      </section>

      <section className="technical-grid">
        <div className="technical-card">
          <div className="technical-icon"><Mountain size={20} /></div>
          <div>
            <span>DEM / TERRAIN</span>
            <h3>Elevation-aware screening</h3>
            <p>
              The backend flood-depth calculation applies terrain adjustment
              to runoff so lower-lying cells can receive greater inundation
              depth.
            </p>
          </div>
          <CheckCircle2 size={18} className="check-icon" />
        </div>

        <div className="technical-card">
          <div className="technical-icon"><TreePine size={20} /></div>
          <div>
            <span>LULC → CURVE NUMBER</span>
            <h3>SCS-CN hydrology</h3>
            <p>
              Land-use/land-cover classes are mapped to curve numbers before
              runoff is calculated from rainfall excess.
            </p>
          </div>
          <CheckCircle2 size={18} className="check-icon" />
        </div>

        <div className="technical-card">
          <div className="technical-icon"><Activity size={20} /></div>
          <div>
            <span>DECISION OUTPUT</span>
            <h3>Flood risk classification</h3>
            <p>
              Flood depth is converted into risk classes that feed the alert
              and CAP-oriented decision-support pipeline.
            </p>
          </div>
          <CheckCircle2 size={18} className="check-icon" />
        </div>
      </section>

      <div className="prototype-notice">
        <AlertTriangle size={18} />
        <div>
          <strong>Prototype data integrity notice</strong>
          <span>
            The current backend flood endpoint explicitly labels its 4 × 4
            rainfall/DEM/LULC grid as deterministic demonstration data.
            Production deployment requires georeferenced DEM, LULC, drainage
            and operational forecast grids.
          </span>
        </div>
        <span className="updated">
          {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString('en-IN')}` : 'Waiting'}
        </span>
      </div>
    </div>
  )
}

export default Inundation
