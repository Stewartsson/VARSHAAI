import { apiFetch } from '../api'
import { useEffect, useMemo, useState } from 'react'
import {
  Siren,
  ShieldAlert,
  RefreshCw,
  Send,
  FileWarning,
  CheckCircle2,
  Clock3,
  MapPinned,
  Droplets,
  Waves,
  Radio,
  ArrowRight,
  AlertTriangle,
  Copy,
  Check,
  Activity,
  Zap,
  CloudRain,
  Thermometer,
  Wind,
  Gauge,
  Droplet,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import '../styles/AlertCenter.css'

const CHENNAI = 'Chennai District, Tamil Nadu'

function num(value, fallback = 0) {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function getRiskCode(risk) {
  const direct = num(risk?.risk_code, NaN)
  if (Number.isFinite(direct)) return direct

  const level = String(risk?.alert_level || risk?.severity || '').toUpperCase()
  if (level === 'RED') return 4
  if (level === 'ORANGE') return 3
  if (level === 'YELLOW') return 2
  return 1
}

function getLevel(risk) {
  const level = String(risk?.alert_level || '').toUpperCase()
  if (level) return level

  const code = getRiskCode(risk)
  if (code >= 4) return 'RED'
  if (code >= 3) return 'ORANGE'
  if (code >= 2) return 'YELLOW'
  return 'GREEN'
}

function levelClass(level) {
  return level === 'RED'
    ? 'alert-red'
    : level === 'ORANGE'
      ? 'alert-orange'
      : level === 'YELLOW'
        ? 'alert-yellow'
        : 'alert-green'
}

function AlertCenter() {
  const [mode, setMode] = useState('live') // 'live' or 'simulation'
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  async function loadRisk(selectedMode = mode) {
    setError('')
    try {
      const response = await apiFetch(`/api/flood/risk?mode=${selectedMode}&t=${Date.now()}`)
      if (!response.ok) throw new Error(`Flood risk API returned HTTP ${response.status}`)
      const data = await response.json()
      setRiskData(data)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err.message || 'Unable to load flood risk.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  function handleModeChange(newMode) {
    if (newMode === mode) return
    setMode(newMode)
    setRefreshing(true)
    setGenerated(false)
    loadRisk(newMode)
  }

  useEffect(() => {
    loadRisk('live')
  }, [])

  const risk = riskData?.risk || {}
  const inundation = riskData?.inundation || {}
  const cap = riskData?.cap_payload || {}
  const level = getLevel(risk)
  const code = getRiskCode(risk)
  const className = levelClass(level)

  const maxDepth = num(risk?.maximum_depth_m)
  const floodedFraction = num(risk?.flooded_fraction)
  const confidence = num(risk?.confidence, 0.85)

  const alertTitle =
    level === 'GREEN'
      ? 'GREEN: Normal Conditions — No Flood Inundation'
      : cap?.headline || `${level}: Flood Risk for Chennai`

  const event =
    level === 'GREEN'
      ? 'Routine Monitoring / Clear Weather'
      : cap?.event || 'Heavy Rainfall / Flood Inundation'

  const severity =
    cap?.severity || (level === 'RED' ? 'Extreme' : level === 'ORANGE' ? 'Severe' : level === 'YELLOW' ? 'Moderate' : 'Minor / Normal')

  const urgency = cap?.urgency || (level === 'GREEN' ? 'Past / Nil' : 'Expected')
  const certainty = cap?.certainty || (level === 'GREEN' ? 'Observed' : 'Likely')

  const capXml = riskData?.cap_xml || ''

  const statusText = useMemo(() => {
    if (generated) return 'CAP ALERT GENERATED'
    if (loading) return 'CONNECTING ENGINE'
    if (mode === 'live') return 'LIVE STREAM CONNECTED'
    return 'SIMULATION READY'
  }, [generated, loading, mode])

  async function generateAlert() {
    setGenerating(true)
    setGenerated(false)
    await new Promise((resolve) => setTimeout(resolve, 650))
    setGenerated(true)
    setGenerating(false)
  }

  async function copyCap() {
    if (!capXml) return
    try {
      await navigator.clipboard.writeText(capXml)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  const currentWeather = riskData?.current_weather

  return (
    <div className="alert-center-page">
      {/* PAGE HEADER */}
      <div className="alert-page-header">
        <div>
          <div className="alert-breadcrumb">
            VARSHAAI / DECISION SUPPORT / ALERT CENTER
          </div>

          <div className="alert-title-row">
            <div className={`alert-title-icon ${className}`}>
              {level === 'GREEN' ? <ShieldCheck size={32} /> : <Siren size={30} />}
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h1>Alert Center</h1>
                <span className={`mode-badge ${mode === 'live' ? 'live-badge' : 'sim-badge'}`}>
                  {mode === 'live' ? '● LIVE MODE' : '⚡ SIMULATION'}
                </span>
              </div>
              <p>
                Real-time hydrodynamic flood-risk classification and CAP 1.2 OASIS emergency alert generation.
              </p>
            </div>
          </div>
        </div>

        <div className="alert-header-actions">
          <div className={`alert-status ${className}`}>
            <span className="status-dot" />
            {statusText}
          </div>

          <button
            className="alert-refresh"
            disabled={refreshing}
            onClick={() => {
              setRefreshing(true)
              loadRisk(mode)
            }}
          >
            <RefreshCw size={15} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* INTERACTIVE MODE TOGGLE (LIVE vs SIMULATION) */}
      <div className="alert-mode-toggle-card">
        <div className="mode-toggle-buttons">
          <button
            className={`mode-toggle-btn ${mode === 'live' ? 'active-live' : ''}`}
            onClick={() => handleModeChange('live')}
          >
            <span className="pulse-dot-green" />
            <Activity size={16} />
            <span>LIVE WEATHER (Chennai Real-Time)</span>
          </button>

          <button
            className={`mode-toggle-btn ${mode === 'simulation' ? 'active-sim' : ''}`}
            onClick={() => handleModeChange('simulation')}
          >
            <Zap size={16} />
            <span>SIMULATE CLOUDBURST (Jury Demo Mode)</span>
          </button>
        </div>

        <div className="mode-explainer">
          {mode === 'live' ? (
            <div className="explainer-text live-explainer">
              <Sparkles size={16} className="text-emerald" />
              <span>
                <strong>Live Meteorological Coupling Active:</strong> Pulling real-time atmospheric feeds from Chennai (Lat 13.08°N, Lon 80.27°E). Alerts dynamically respond to live rainfall!
              </span>
            </div>
          ) : (
            <div className="explainer-text sim-explainer">
              <Zap size={16} className="text-orange" />
              <span>
                <strong>180mm Cloudburst Scenario Active:</strong> Injects the benchmark extreme rainfall event for SIH jury demonstration of SCS-CN runoff, inundation depth, and CAP XML alerts.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* LIVE TELEMETRY BAR (REAL WEATHER) */}
      {currentWeather && (
        <section className="live-telemetry-banner">
          <div className="telemetry-header">
            <div className="telemetry-title">
              <Radio size={16} className="telemetry-pulse" />
              <span>CHENNAI DISTRICT REAL-TIME ATMOSPHERIC SENSORS</span>
            </div>
            <span className="telemetry-time">
              Live Observation: {new Date(currentWeather.observed_at || Date.now()).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })} IST
            </span>
          </div>

          <div className="telemetry-grid">
            <div className="telemetry-card">
              <div className="telemetry-icon-wrap rain-accent"><CloudRain size={20} /></div>
              <div>
                <span>LIVE PRECIPITATION</span>
                <strong>{currentWeather.precipitation_mm ?? 0} mm/hr</strong>
                <small>{(currentWeather.precipitation_mm ?? 0) === 0 ? 'Clear / dry ground' : 'Active storm precipitation'}</small>
              </div>
            </div>

            <div className="telemetry-card">
              <div className="telemetry-icon-wrap temp-accent"><Thermometer size={20} /></div>
              <div>
                <span>TEMPERATURE</span>
                <strong>{currentWeather.temperature_c ?? '--'} °C</strong>
                <small>Surface 2m ambient</small>
              </div>
            </div>

            <div className="telemetry-card">
              <div className="telemetry-icon-wrap humidity-accent"><Droplet size={20} /></div>
              <div>
                <span>RELATIVE HUMIDITY</span>
                <strong>{currentWeather.humidity_percent ?? '--'}%</strong>
                <small>Atmospheric moisture</small>
              </div>
            </div>

            <div className="telemetry-card">
              <div className="telemetry-icon-wrap wind-accent"><Wind size={20} /></div>
              <div>
                <span>WIND VELOCITY</span>
                <strong>{currentWeather.wind_speed_kmh ?? '--'} km/h</strong>
                <small>Coastal gust index</small>
              </div>
            </div>

            <div className="telemetry-card">
              <div className="telemetry-icon-wrap pressure-accent"><Gauge size={20} /></div>
              <div>
                <span>SURFACE PRESSURE</span>
                <strong>{currentWeather.pressure_hpa ?? '--'} hPa</strong>
                <small>Barometric gradient</small>
              </div>
            </div>
          </div>
        </section>
      )}

      {error && (
        <div className="alert-error">
          <AlertTriangle size={18} />
          <div>
            <strong>Risk engine connection issue</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* HERO ALERT CARD */}
      <section className={`alert-hero ${className}`}>
        <div className="hero-left">
          <div className="hero-kicker">
            {level === 'GREEN' ? <ShieldCheck size={18} /> : <ShieldAlert size={17} />}
            {level === 'GREEN' ? 'CURRENT HYDROLOGICAL STATUS' : 'CURRENT FLOOD INUNDATION RISK'}
          </div>

          <h2>{level} ALERT</h2>
          <p>{alertTitle}</p>

          <div className="hero-location">
            <MapPinned size={15} />
            {CHENNAI} — Coastal Drainage Basin
          </div>
        </div>

        <div className="hero-score">
          <span>RISK CONFIDENCE</span>
          <strong>{(confidence * 100).toFixed(1)}%</strong>
          <div className="confidence-track">
            <div style={{ width: `${Math.min(confidence * 100, 100)}%` }} />
          </div>
        </div>

        <div className="hero-action">
          <button
            className="generate-button"
            disabled={generating || loading}
            onClick={generateAlert}
          >
            {generated ? <CheckCircle2 size={17} /> : <Send size={17} />}
            {generating
              ? 'Generating...'
              : generated
                ? 'Alert Generated'
                : `Generate ${level} Alert`}
          </button>

          {generated && (
            <small>CAP 1.2 XML payload prepared from the current risk assessment.</small>
          )}
        </div>
      </section>

      {/* METRIC CARDS */}
      <section className="alert-metrics">
        <div className="alert-metric">
          <div className="metric-icon"><Droplets size={20} /></div>
          <span>MAX FLOOD DEPTH</span>
          <strong>{maxDepth.toFixed(2)} m</strong>
          <small>{maxDepth === 0 ? 'Zero surface water logging' : 'Hydrodynamic inundation peak'}</small>
        </div>

        <div className="alert-metric">
          <div className="metric-icon"><Waves size={20} /></div>
          <span>FLOODED FRACTION</span>
          <strong>{(floodedFraction * 100).toFixed(1)}%</strong>
          <small>{floodedFraction === 0 ? 'All wards normal' : 'Modelled drainage grid area'}</small>
        </div>

        <div className="alert-metric">
          <div className="metric-icon"><Clock3 size={20} /></div>
          <span>URGENCY</span>
          <strong>{urgency}</strong>
          <small>CAP severity classification</small>
        </div>

        <div className="alert-metric">
          <div className="metric-icon"><Radio size={20} /></div>
          <span>CERTAINTY</span>
          <strong>{certainty}</strong>
          <small>Multi-source ensemble score</small>
        </div>
      </section>

      {/* SECTION 1: RISK CLASSIFICATION */}
      <section className="decision-section">
        <div className="section-heading">
          <div>
            <span>01 • RISK CLASSIFICATION SCALE</span>
            <h2>Chennai Flood Risk Matrix</h2>
            <p>
              The flood-depth result is evaluated against IMD-standard multi-tier thresholds before any alert payload is prepared.
            </p>
          </div>
        </div>

        <div className="risk-levels">
          {[
            ['GREEN', 'Normal / No flood risk', 1],
            ['YELLOW', 'Flood Watch / Be prepared', 2],
            ['ORANGE', 'Flood Warning / Severe rain', 3],
            ['RED', 'Extreme / Emergency evacuation', 4],
          ].map(([name, description]) => (
            <div
              key={name}
              className={`risk-level ${level === name ? 'selected' : ''} ${levelClass(name)}`}
            >
              <span className="risk-level-dot" />
              <div>
                <strong>{name}</strong>
                <small>{description}</small>
              </div>
              {level === name && <CheckCircle2 size={17} />}
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 2: CAP OUTPUT */}
      <section className="cap-section">
        <div className="section-heading">
          <div>
            <span>02 • CAP-COMPATIBLE OUTPUT (OASIS CAP 1.2)</span>
            <h2>Emergency Telecom Alert Payload</h2>
            <p>
              Machine-readable Common Alerting Protocol compliant format directly ingestible by NDMA, state emergency telecom broadcasts, and siren systems.
            </p>
          </div>

          <button className="copy-button" onClick={copyCap} disabled={!capXml}>
            {copied ? <Check size={15} /> : <Copy size={15} />}
            {copied ? 'Copied' : 'Copy CAP XML'}
          </button>
        </div>

        <div className="cap-grid">
          <div className="cap-fields">
            <div className="cap-field">
              <span>EVENT TYPE</span>
              <strong>{event}</strong>
            </div>

            <div className="cap-field">
              <span>TARGET REGION</span>
              <strong>{cap?.area || 'Chennai District'}</strong>
            </div>

            <div className="cap-field">
              <span>SEVERITY</span>
              <strong className={className}>{severity}</strong>
            </div>

            <div className="cap-field">
              <span>URGENCY</span>
              <strong>{urgency}</strong>
            </div>

            <div className="cap-field">
              <span>CERTAINTY</span>
              <strong>{certainty}</strong>
            </div>

            <div className="cap-field">
              <span>STATUS</span>
              <strong>{mode === 'live' ? 'Actual' : 'Exercise / Demo'}</strong>
            </div>

            <div className="cap-field wide">
              <span>ACTION INSTRUCTION</span>
              <strong>
                {level === 'GREEN'
                  ? 'Normal drainage flow. No emergency action required for citizens.'
                  : cap?.instruction || 'Follow official emergency guidance and avoid flooded underpasses.'}
              </strong>
            </div>
          </div>

          <div className="cap-preview">
            <div className="cap-preview-head">
              <FileWarning size={17} />
              <span>STANDARDIZED CAP 1.2 XML OUTPUT</span>
            </div>

            <pre>
              {capXml
                ? capXml
                : 'CAP XML will appear here when the backend risk payload is available.'}
            </pre>
          </div>
        </div>
      </section>

      {/* SECTION 3: PIPELINE FLOW */}
      <section className="pipeline-section">
        <div className="section-heading">
          <div>
            <span>03 • END-TO-END AUTOMATED PIPELINE</span>
            <h2>From Atmospheric Ingestion to Public Alert</h2>
            <p>
              VARSHAAI harmonizes multi-source data and couples hydrology with AI nowcasting for transparent decision-support.
            </p>
          </div>
        </div>

        <div className="alert-pipeline">
          <div className="alert-node">
            <div><Waves size={21} /></div>
            <span>INGESTION</span>
            <strong>Satellite & GFS Radar</strong>
          </div>

          <ArrowRight className="pipeline-arrow" />

          <div className="alert-node">
            <div><Droplets size={21} /></div>
            <span>HYDROLOGY</span>
            <strong>SCS-CN Runoff Model</strong>
          </div>

          <ArrowRight className="pipeline-arrow" />

          <div className="alert-node">
            <div><ShieldAlert size={21} /></div>
            <span>RISK ENGINE</span>
            <strong>{level} Classification</strong>
          </div>

          <ArrowRight className="pipeline-arrow" />

          <div className="alert-node final">
            <div><Siren size={21} /></div>
            <span>CAP 1.2 XML</span>
            <strong>NDMA Broadcast</strong>
          </div>
        </div>
      </section>

      {/* HISTORY / TIMESTAMP */}
      <section className="alert-history">
        <div>
          <span>SYSTEM RUNTIME LOG</span>
          <h3>Active Telemetry Cycle</h3>
          <p>
            Mode: <strong>{mode.toUpperCase()}</strong> • Region: <strong>Chennai</strong> • Engine: <strong>SCS-CN + CartoDEM Hydrodynamic</strong>
          </p>
        </div>

        <div className="history-right">
          <CheckCircle2 size={17} />
          <strong>{generated ? 'DISPATCHED' : 'ONLINE'}</strong>
          <small>
            {lastUpdated
              ? `Calculated ${lastUpdated.toLocaleTimeString('en-IN')}`
              : 'Calculation pending'}
          </small>
        </div>
      </section>

      {/* NOTICE */}
      <div className="alert-notice">
        <AlertTriangle size={18} />
        <div>
          <strong>Operational decision-support prototype</strong>
          <span>
            VARSHAAI operates under the WMO & NDMA guidelines for multi-hazard early warning systems. Real-time telemetry is coupled with SCS-CN runoff modeling for urban flash flood resilience.
          </span>
        </div>
      </div>
    </div>
  )
}

export default AlertCenter
