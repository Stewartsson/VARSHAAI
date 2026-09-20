import { apiFetch } from '../api';
import { useEffect, useState } from 'react'

import {
  Satellite,
  Radar,
  CloudRain,
  Gauge,
  Activity,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  Clock3,
  Layers3,
} from 'lucide-react'

import '../styles/DataIntelligence.css'

const FETCH_TIMEOUT = 8000

function DataIntelligence({ onSourceSelect }) {
  const [sourceStatus, setSourceStatus] = useState({
    satellite: null,
    radar: null,
    observations: null,
    nwp: null,
  })

  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [error, setError] = useState('')

  // ============================================================
  // SAFE API FETCH
  // ============================================================

  const fetchJson = async (url) => {
    const controller = new AbortController()

    const timeout = setTimeout(() => {
      controller.abort()
    }, FETCH_TIMEOUT)

    try {
      const response = await apiFetch(url, {
        signal: controller.signal,
        cache: 'no-store',
      })

      if (!response.ok) {
        throw new Error(
          `${url} returned HTTP ${response.status}`,
        )
      }

      return await response.json()
    } finally {
      clearTimeout(timeout)
    }
  }

  // ============================================================
  // FETCH EACH SOURCE INDEPENDENTLY
  // ============================================================

  const fetchSourceStatus = async () => {
    setLoading(true)
    setError('')

    const endpoints = {
      satellite: '/api/satellite/hem/status',
      radar: '/api/radar/status',
      observations: '/api/observations/status',
      nwp: '/api/nwp/status',
    }

    const results = await Promise.allSettled(
      Object.entries(endpoints).map(
        async ([key, url]) => {
          const data = await fetchJson(url)

          return {
            key,
            data,
          }
        },
      ),
    )

    const nextStatus = {
      satellite: null,
      radar: null,
      observations: null,
      nwp: null,
    }

    const failures = []

    results.forEach((result, index) => {
      const key = Object.keys(endpoints)[index]

      if (result.status === 'fulfilled') {
        nextStatus[key] = result.value.data
      } else {
        failures.push(key)
      }
    })

    setSourceStatus(nextStatus)
    setLastUpdated(new Date())

    if (failures.length > 0) {
      setError(
        `${failures.join(', ').toUpperCase()} status could not be read.`
      )
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchSourceStatus()

    const interval = setInterval(
      fetchSourceStatus,
      5 * 60 * 1000,
    )

    return () => clearInterval(interval)
  }, [])

  // ============================================================
  // STATUS HELPERS
  // ============================================================

  const getStatus = (type) => {
    const source = sourceStatus[type]

    if (!source) {
      return {
        label: 'OFFLINE',
        className: 'unavailable',
      }
    }

    if (
      source.status === 'connected' ||
      source.status === 'available' ||
      source.status === 'success'
    ) {
      return {
        label: 'CONNECTED',
        className: 'connected',
      }
    }

    if (
      source.status === 'access_pending' ||
      source.status === 'pending'
    ) {
      return {
        label: 'ACCESS PENDING',
        className: 'pending',
      }
    }

    return {
      label: String(source.status).toUpperCase(),
      className: 'unavailable',
    }
  }

  const satelliteStatus = getStatus('satellite')
  const radarStatus = getStatus('radar')
  const observationsStatus = getStatus('observations')
  const nwpStatus = getStatus('nwp')

  // ============================================================
  // SOURCE CARDS
  // ============================================================

  const sources = [
    {
      id: 'satellite',
      name: 'INSAT-3DR',
      subtitle: 'Hydro Estimator Precipitation',
      description:
        'Real MOSDAC INSAT-3DR HEM precipitation observations used for rainfall monitoring and satellite-based QPE.',
      resolution: '≈4 km',
      temporal: '30 min',
      icon: Satellite,
      status: satelliteStatus,
      sourceLabel: 'MOSDAC / ISRO',
    },

    {
      id: 'radar',
      name: 'DWR RADAR',
      subtitle: 'Weather Radar Reflectivity',
      description:
        'Official Chennai Doppler Weather Radar imagery is connected for precipitation structure and movement monitoring.',
      resolution: '≈1 km',
      temporal: '10 min',
      icon: Radar,
      status: radarStatus,
      sourceLabel: 'IMD Chennai',
    },

    {
      id: 'aws',
      name: 'AWS NETWORK',
      subtitle: 'Automatic Weather Stations',
      description:
        'Ground observations provide rainfall and meteorological measurements for quality control, validation and data fusion.',
      resolution: 'Point',
      temporal: '10 min',
      icon: Gauge,
      status: observationsStatus,
      sourceLabel: 'IMD AWS',
    },

    {
      id: 'arg',
      name: 'ARG NETWORK',
      subtitle: 'Automatic Rain Gauges',
      description:
        'Automatic rain-gauge observations provide point rainfall measurements for validation and multi-source rainfall estimation.',
      resolution: 'Point',
      temporal: '10 min',
      icon: CloudRain,
      status: observationsStatus,
      sourceLabel: 'IMD ARG',
    },

    {
      id: 'nwp',
      name: 'NWP MODELS',
      subtitle: 'Numerical Weather Prediction',
      description:
        'NOAA GFS forecast fields are connected through the current prototype adapter for 3–72 hour atmospheric prediction.',
      resolution: '≈12 km',
      temporal: 'Hourly forecast',
      icon: Activity,
      status: nwpStatus,
      sourceLabel: 'NOAA GFS',
    },
  ]

  // ============================================================
  // COUNTS
  // ============================================================

  const coreStatuses = [
    satelliteStatus,
    radarStatus,
    nwpStatus,
  ]

  const connectedCount = coreStatuses.filter(
    (item) => item.className === 'connected',
  ).length

  const pendingCount = [
    observationsStatus,
  ].filter(
    (item) => item.className === 'pending',
  ).length

  // ============================================================
  // TIME
  // ============================================================

  const formatTime = (value) => {
    if (!value) return '—'

    return value.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  // ============================================================
  // STATUS ICON
  // ============================================================

  const StatusIcon = ({ status }) => {
    if (status.className === 'connected') {
      return <CheckCircle2 size={13} />
    }

    if (status.className === 'pending') {
      return <AlertTriangle size={13} />
    }

    return null
  }

  return (
    <div className="data-intelligence-page">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <div className="data-page-header">

        <div className="data-header-copy">

          <div className="data-breadcrumb">
            VARSHAAI / DATA ENGINE / INGESTION
          </div>

          <h1>
            Data Intelligence
          </h1>

          <p>
            Multi-source weather data ingestion, quality control,
            harmonization and observation management.
          </p>

        </div>

        <button
          className="refresh-button"
          onClick={fetchSourceStatus}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? 'spin' : ''}
          />

          {loading
            ? 'Checking Sources...'
            : 'Refresh Sources'}
        </button>

      </div>

      {/* ======================================================
          LIVE DATA BANNER
          ====================================================== */}

      <div className="real-data-banner">

        <div className="real-data-left">

          <div className="real-data-dot" />

          <div className="real-data-text">

            <strong>
              REAL MULTI-SOURCE DATA PIPELINE
            </strong>

            <span>
              INSAT-3DR + Chennai DWR + GFS connected
              {pendingCount > 0
                ? ' • AWS / ARG access pending'
                : ''}
            </span>

          </div>

        </div>

        <div className="real-data-right">

          <CheckCircle2 size={17} />

          <strong>
            {connectedCount}/3 CORE FEEDS LIVE
          </strong>

        </div>

      </div>

      {/* ======================================================
          ERROR
          ====================================================== */}

      {error && (
        <div className="data-error-banner">

          <AlertTriangle size={17} />

          <div>
            <strong>
              Source status notice
            </strong>

            <span>
              {error}
            </span>
          </div>

        </div>
      )}

      {/* ======================================================
          SOURCE SECTION
          ====================================================== */}

      <section className="source-section">

        <div className="section-heading">

          <div>

            <span className="section-label">
              INGESTION LAYER
            </span>

            <h2>
              Multi-Source Meteorological Inputs
            </h2>

            <p>
              Each source is monitored independently before
              quality control, regridding and temporal alignment.
            </p>

          </div>

          {lastUpdated && (
            <div className="last-updated">
              <Clock3 size={14} />
              Updated {formatTime(lastUpdated)}
            </div>
          )}

        </div>

        <div className="source-grid">

          {sources.map((source) => {

            const Icon = source.icon

            return (
              <button
                key={source.id}
                type="button"
                className={`source-card ${
                  source.status.className ===
                  'connected'
                    ? 'source-card-connected'
                    : ''
                }`}
                onClick={() =>
                  onSourceSelect(source.id)
                }
              >

                {/* CARD TOP */}

                <div className="source-card-top">

                  <div className="source-icon">
                    <Icon size={21} />
                  </div>

                  <span
                    className={`source-status ${source.status.className}`}
                  >
                    <StatusIcon
                      status={source.status}
                    />

                    {source.status.label}
                  </span>

                </div>

                {/* CARD CONTENT */}

                <div className="source-content">

                  <h3>
                    {source.name}
                  </h3>

                  <span className="source-subtitle">
                    {source.subtitle}
                  </span>

                  <p>
                    {source.description}
                  </p>

                </div>

                {/* METRICS */}

                <div className="source-meta">

                  <div>
                    <span>
                      RESOLUTION
                    </span>

                    <strong>
                      {source.resolution}
                    </strong>
                  </div>

                  <div>
                    <span>
                      TEMPORAL
                    </span>

                    <strong>
                      {source.temporal}
                    </strong>
                  </div>

                </div>

                {/* FOOTER */}

                <div className="source-footer">

                  <span>
                    View source details
                  </span>

                  <ArrowRight size={16} />

                </div>

              </button>
            )
          })}

        </div>

      </section>

      {/* ======================================================
          HARMONIZATION
          ====================================================== */}

      <section className="harmonization-section">

        <div className="section-heading">

          <div>

            <span className="section-label">
              DATA HARMONIZATION
            </span>

            <h2>
              Common Spatial &amp; Temporal Framework
            </h2>

            <p>
              Heterogeneous observations are quality-controlled
              and aligned before entering the AI pipeline.
            </p>

          </div>

        </div>

        <div className="harmonization-flow">

          <div className="harmonization-card">

            <div className="harmonization-icon">
              <Satellite size={19} />
            </div>

            <span>
              SATELLITE
            </span>

            <strong>
              ≈4 km
            </strong>

            <small>
              30 min
            </small>

          </div>

          <div className="harmonization-arrow">
            <ArrowRight size={17} />
          </div>

          <div className="harmonization-card">

            <div className="harmonization-icon">
              <Radar size={19} />
            </div>

            <span>
              RADAR
            </span>

            <strong>
              ≈1 km
            </strong>

            <small>
              10 min
            </small>

          </div>

          <div className="harmonization-arrow">
            <ArrowRight size={17} />
          </div>

          <div className="harmonization-card">

            <div className="harmonization-icon">
              <Gauge size={19} />
            </div>

            <span>
              AWS / ARG
            </span>

            <strong>
              POINT
            </strong>

            <small>
              10 min
            </small>

          </div>

          <div className="harmonization-arrow">
            <ArrowRight size={17} />
          </div>

          <div className="harmonization-card">

            <div className="harmonization-icon">
              <CloudRain size={19} />
            </div>

            <span>
              NWP / GFS
            </span>

            <strong>
              ≈12 km
            </strong>

            <small>
              Hourly forecast
            </small>

          </div>

        </div>

        <div className="common-grid-panel">

          <div className="common-grid-icon">
            <Layers3 size={22} />
          </div>

          <div className="common-grid-content">

            <span className="common-grid-label">
              VARSHAAI HARMONIZATION TARGET
            </span>

            <h3>
              Common grid + common time axis
            </h3>

            <p>
              Radar, satellite, station and NWP data are
              normalized through quality control, spatial
              regridding and temporal alignment before model
              ingestion.
            </p>

          </div>

          <div className="common-grid-status">

            <CheckCircle2 size={16} />

            <span>
              PIPELINE READY
            </span>

          </div>

        </div>

      </section>

      {/* ======================================================
          QUALITY CONTROL
          ====================================================== */}

      <section className="quality-section">

        <div className="section-heading">

          <div>

            <span className="section-label">
              PREPROCESSING
            </span>

            <h2>
              Meteorological Data Quality Control
            </h2>

            <p>
              Source-specific QC prevents unreliable observations
              from entering the prediction models.
            </p>

          </div>

        </div>

        <div className="quality-grid">

          <div className="quality-card">

            <div className="quality-icon">
              <Database size={19} />
            </div>

            <div>
              <strong>
                Missing Data Handling
              </strong>

              <span>
                Missing observations are flagged and preserved;
                synthetic values are not inserted into the live
                data stream.
              </span>
            </div>

          </div>

          <div className="quality-card">

            <div className="quality-icon">
              <Radar size={19} />
            </div>

            <div>
              <strong>
                Radar QC
              </strong>

              <span>
                Ground-clutter and beam-blockage quality-control
                stages are prepared before quantitative radar
                rainfall processing.
              </span>
            </div>

          </div>

          <div className="quality-card">

            <div className="quality-icon">
              <Layers3 size={19} />
            </div>

            <div>
              <strong>
                Spatial Regridding
              </strong>

              <span>
                Bilinear, IDW or kriging-based interpolation can
                bring heterogeneous source grids into the common
                analysis framework.
              </span>
            </div>

          </div>

          <div className="quality-card">

            <div className="quality-icon">
              <Clock3 size={19} />
            </div>

            <div>
              <strong>
                Temporal Alignment
              </strong>

              <span>
                Source timestamps are reconciled onto a common
                analysis timeline without fabricating missing
                observations.
              </span>
            </div>

          </div>

        </div>

      </section>

      {/* ======================================================
          CONNECTIVITY
          ====================================================== */}

      <section className="connection-summary">

        <div className="connection-summary-header">

          <div>

            <span className="section-label">
              CURRENT SYSTEM STATUS
            </span>

            <h2>
              Source Connectivity
            </h2>

          </div>

          <Activity size={20} />

        </div>

        <div className="connection-list">

          <div className="connection-row">

            <div className="connection-source">
              <Satellite size={17} />
              <span>
                INSAT-3DR
              </span>
            </div>

            <strong
              className={`connection-status ${satelliteStatus.className}`}
            >
              {satelliteStatus.label}
            </strong>

          </div>

          <div className="connection-row">

            <div className="connection-source">
              <Radar size={17} />
              <span>
                Chennai DWR
              </span>
            </div>

            <strong
              className={`connection-status ${radarStatus.className}`}
            >
              {radarStatus.label}
            </strong>

          </div>

          <div className="connection-row">

            <div className="connection-source">
              <CloudRain size={17} />
              <span>
                NOAA GFS / NWP
              </span>
            </div>

            <strong
              className={`connection-status ${nwpStatus.className}`}
            >
              {nwpStatus.label}
            </strong>

          </div>

          <div className="connection-row">

            <div className="connection-source">
              <Gauge size={17} />
              <span>
                IMD AWS / ARG
              </span>
            </div>

            <strong
              className={`connection-status ${observationsStatus.className}`}
            >
              {observationsStatus.label}
            </strong>

          </div>

        </div>

      </section>

      {/* ======================================================
          PROTOTYPE NOTE
          ====================================================== */}

      <div className="prototype-note">

        <div className="prototype-icon">
          <AlertTriangle size={16} />
        </div>

        <div>

          <strong>
            Prototype / Integration Status
          </strong>

          <span>
            INSAT-3DR HEM, Chennai DWR imagery and NOAA GFS
            connectivity are operational in the current prototype.
            IMD AWS/ARG access remains gated by source
            authentication. Quantitative radar rainfall-grid
            processing will be enabled when the appropriate
            reflectivity grid feed is available.
          </span>

        </div>

      </div>

    </div>
  )
}

export default DataIntelligence
