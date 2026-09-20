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
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  async function loadRisk() {
    setError('')
    try {
      const response = await fetch(`/api/flood/risk?t=${Date.now()}`)
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

  useEffect(() => {
    loadRisk()
  }, [])

  const risk = riskData?.risk || {}
  const inundation = riskData?.inundation || {}
  const cap = riskData?.cap_payload || {}
  const level = getLevel(risk)
  const code = getRiskCode(risk)
  const className = levelClass(level)

  const maxDepth = num(risk?.maximum_depth_m)
  const floodedFraction = num(risk?.flooded_fraction)
  const confidence = num(risk?.confidence)

  const alertTitle = cap?.headline || `${level}: Flood Risk for Chennai`
  const event = cap?.event || 'Heavy Rainfall / Flood Inundation'
  const severity = cap?.severity || (level === 'RED' ? 'Extreme' : level === 'ORANGE' ? 'Severe' : 'Moderate')
  const urgency = cap?.urgency || 'Expected'
  const certainty = cap?.certainty || 'Likely'

  const capXml = riskData?.cap_xml || ''

  const statusText = useMemo(() => {
    if (generated) return 'CAP ALERT GENERATED'
    if (loading) return 'LOADING RISK'
    return 'READY FOR REVIEW'
  }, [generated, loading])

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

  return (
    <div className="alert-center-page">
      <div className="alert-page-header">
        <div>
          <div className="alert-breadcrumb">
            VARSHAAI / DECISION SUPPORT / ALERT CENTER
          </div>

          <div className="alert-title-row">
            <div className={`alert-title-icon ${className}`}>
              <Siren size={30} />
            </div>

            <div>
              <h1>Alert Center</h1>
              <p>
                Flood-risk classification and CAP-oriented emergency alert
                generation for Chennai District.
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
              loadRisk()
            }}
          >
            <RefreshCw size={15} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-error">
          <AlertTriangle size={18} />
          <div>
            <strong>Risk engine connection issue</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      <section className={`alert-hero ${className}`}>
        <div className="hero-left">
          <div className="hero-kicker">
            <ShieldAlert size={17} />
            CURRENT FLOOD RISK
          </div>

          <h2>{level} ALERT</h2>
          <p>{alertTitle}</p>

          <div className="hero-location">
            <MapPinned size={15} />
            {CHENNAI}
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
            <small>CAP payload prepared from the current risk assessment.</small>
          )}
        </div>
      </section>

      <section className="alert-metrics">
        <div className="alert-metric">
          <div className="metric-icon"><Droplets size={20} /></div>
          <span>MAX FLOOD DEPTH</span>
          <strong>{maxDepth.toFixed(2)} m</strong>
          <small>Modelled inundation depth</small>
        </div>

        <div className="alert-metric">
          <div className="metric-icon"><Waves size={20} /></div>
          <span>FLOODED FRACTION</span>
          <strong>{(floodedFraction * 100).toFixed(1)}%</strong>
          <small>Modelled grid fraction</small>
        </div>

        <div className="alert-metric">
          <div className="metric-icon"><Clock3 size={20} /></div>
          <span>URGENCY</span>
          <strong>{urgency}</strong>
          <small>CAP classification</small>
        </div>

        <div className="alert-metric">
          <div className="metric-icon"><Radio size={20} /></div>
          <span>CERTAINTY</span>
          <strong>{certainty}</strong>
          <small>Risk-engine output</small>
        </div>
      </section>

      <section className="decision-section">
        <div className="section-heading">
          <div>
            <span>01 • RISK CLASSIFICATION</span>
            <h2>Chennai Risk Assessment</h2>
            <p>
              The flood-depth result is passed into the risk engine before any
              alert payload is prepared.
            </p>
          </div>
        </div>

        <div className="risk-levels">
          {[
            ['GREEN', 'Normal / monitor', 1],
            ['YELLOW', 'Be prepared', 2],
            ['ORANGE', 'Flood warning', 3],
            ['RED', 'Severe flood risk', 4],
          ].map(([name, description, riskCode]) => (
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

      <section className="cap-section">
        <div className="section-heading">
          <div>
            <span>02 • CAP-COMPATIBLE OUTPUT</span>
            <h2>Emergency Alert Payload</h2>
            <p>
              The backend produces both structured alert fields and CAP XML.
              This page presents the current generated payload for review.
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
              <span>EVENT</span>
              <strong>{event}</strong>
            </div>

            <div className="cap-field">
              <span>AREA</span>
              <strong>{cap?.area || 'Chennai'}</strong>
            </div>

            <div className="cap-field">
              <span>SEVERITY</span>
              <strong>{severity}</strong>
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
              <strong>{cap?.status || 'Actual'}</strong>
            </div>

            <div className="cap-field wide">
              <span>INSTRUCTION</span>
              <strong>
                {cap?.instruction ||
                  'Follow official emergency guidance and local authority instructions.'}
              </strong>
            </div>
          </div>

          <div className="cap-preview">
            <div className="cap-preview-head">
              <FileWarning size={17} />
              CAP 1.2 XML PREVIEW
            </div>

            <pre>
              {capXml
                ? capXml
                : 'CAP XML will appear here when the backend risk payload is available.'}
            </pre>
          </div>
        </div>
      </section>

      <section className="pipeline-section">
        <div className="section-heading">
          <div>
            <span>03 • ALERT PIPELINE</span>
            <h2>From Forecast to Public Warning</h2>
            <p>
              VARSHAAI converts predicted rainfall and inundation into an
              explainable decision-support chain.
            </p>
          </div>
        </div>

        <div className="alert-pipeline">
          <div className="alert-node">
            <div><Waves size={21} /></div>
            <span>FORECAST</span>
            <strong>Rainfall prediction</strong>
          </div>

          <ArrowRight className="pipeline-arrow" />

          <div className="alert-node">
            <div><Droplets size={21} /></div>
            <span>INUNDATION</span>
            <strong>Flood depth grid</strong>
          </div>

          <ArrowRight className="pipeline-arrow" />

          <div className="alert-node">
            <div><ShieldAlert size={21} /></div>
            <span>RISK ENGINE</span>
            <strong>{level} classification</strong>
          </div>

          <ArrowRight className="pipeline-arrow" />

          <div className="alert-node final">
            <div><Siren size={21} /></div>
            <span>CAP ALERT</span>
            <strong>Emergency output</strong>
          </div>
        </div>
      </section>

      <section className="alert-history">
        <div>
          <span>ALERT HISTORY</span>
          <h3>Current prototype event</h3>
          <p>
            {cap?.identifier || 'Awaiting generated alert identifier'} •{' '}
            {cap?.event || 'Heavy Rainfall / Flood Inundation'} • Chennai
          </p>
        </div>

        <div className="history-right">
          <CheckCircle2 size={17} />
          <strong>{generated ? 'GENERATED' : 'READY'}</strong>
          <small>
            {lastUpdated
              ? `Risk checked ${lastUpdated.toLocaleTimeString('en-IN')}`
              : 'Risk check pending'}
          </small>
        </div>
      </section>

      <div className="alert-notice">
        <AlertTriangle size={18} />
        <div>
          <strong>Operational safety notice</strong>
          <span>
            This is a decision-support prototype. The current flood endpoint
            uses a deterministic demonstration grid; generated alerts must not
            be treated as official IMD warnings until operational data,
            validation and authority approval are integrated.
          </span>
        </div>
      </div>
    </div>
  )
}

export default AlertCenter
