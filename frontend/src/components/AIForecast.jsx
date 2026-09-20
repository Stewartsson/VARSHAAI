import { useEffect, useMemo, useState } from 'react'

import {
  BrainCircuit,
  Radar,
  Satellite,
  CloudRain,
  Activity,
  Gauge,
  Wind,
  TrendingUp,
  ShieldCheck,
  Zap,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Droplets,
  Waves,
  Database,
  Map,
  RefreshCw,
  Clock,
} from 'lucide-react'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

import '../styles/AIForecast.css'


// ============================================================
// BACKEND
// ============================================================

const API_BASE_URL = 'http://127.0.0.1:8000'

const FLOOD_FORECAST_ENDPOINT =
  `${API_BASE_URL}/api/nwp/ml/flood-forecast`


// ============================================================
// HELPERS
// ============================================================

function formatNumber(value, digits = 2) {
  const number = Number(value)

  if (!Number.isFinite(number)) {
    return '—'
  }

  return number.toFixed(digits)
}


function formatTimestamp(timestamp) {
  if (!timestamp) {
    return '—'
  }

  try {
    const date = new Date(
      timestamp.endsWith('Z')
        ? timestamp
        : `${timestamp}Z`
    )

    if (Number.isNaN(date.getTime())) {
      return timestamp
    }

    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  } catch {
    return timestamp
  }
}


function formatShortTime(timestamp) {
  if (!timestamp) {
    return '—'
  }

  try {
    const date = new Date(
      timestamp.endsWith('Z')
        ? timestamp
        : `${timestamp}Z`
    )

    if (Number.isNaN(date.getTime())) {
      return timestamp
    }

    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  } catch {
    return timestamp
  }
}


function getRiskClass(level) {
  const normalized =
    String(level || 'GREEN').toUpperCase()

  if (normalized === 'RED') {
    return 'risk-red'
  }

  if (normalized === 'ORANGE') {
    return 'risk-orange'
  }

  if (normalized === 'YELLOW') {
    return 'risk-yellow'
  }

  return 'risk-green'
}


// ============================================================
// COMPONENT
// ============================================================

function AIForecast() {

  // ==========================================================
  // STATE
  // ==========================================================

  const [forecast, setForecast] = useState(null)

  const [loading, setLoading] = useState(true)

  const [error, setError] = useState('')

  const [lastUpdated, setLastUpdated] = useState(null)


  // ==========================================================
  // FETCH REAL BACKEND FORECAST
  // ==========================================================

  const fetchForecast = async () => {

    setLoading(true)
    setError('')

    try {

      const response = await fetch(
        FLOOD_FORECAST_ENDPOINT,
        {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        }
      )

      if (!response.ok) {

        throw new Error(
          `Backend returned HTTP ${response.status}`
        )
      }

      const data = await response.json()

      if (
        !data ||
        data.status !== 'success'
      ) {

        throw new Error(
          'Backend returned an unsuccessful forecast response.'
        )
      }

      setForecast(data)

      setLastUpdated(
        data.timestamp || new Date().toISOString()
      )

    } catch (err) {

      console.error(
        'VARSHAAI flood forecast error:',
        err
      )

      setError(
        err?.message ||
        'Unable to connect to the VARSHAAI backend.'
      )

    } finally {

      setLoading(false)

    }
  }


  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {

    fetchForecast()

  }, [])


  // ==========================================================
  // RECORDS
  // ==========================================================

  const records = useMemo(() => {

    if (
      !forecast ||
      !Array.isArray(forecast.records)
    ) {
      return []
    }

    return forecast.records

  }, [forecast])


  // ==========================================================
  // CHART DATA
  // ==========================================================

  const chartData = useMemo(() => {

    return records.map(
      (record, index) => ({
        hour:
          record.forecast_hour ??
          index + 1,

        time:
          formatShortTime(
            record.timestamp_utc
          ),

        nwp:
          Number(
            record.nwp_precipitation_mm
          ) || 0,

        ml:
          Number(
            record.postprocessed_rainfall_mm
          ) || 0,

        cumulative:
          Number(
            record.cumulative_rainfall_mm
          ) || 0,

        runoff:
          Number(
            record.runoff_mm
          ) || 0,

        depth:
          Number(
            record.maximum_flood_depth_m
          ) || 0,

        risk:
          record.risk_level || 'GREEN',
      })
    )

  }, [records])


  // ==========================================================
  // SUMMARY
  // ==========================================================

  const summary =
    forecast?.summary || {}

  const finalRisk =
    forecast?.final_risk || {}

  const integration =
    forecast?.integration || {}

  const spatialGrid =
    forecast?.spatial_grid || {}

  const rainfallHistory =
    forecast?.rainfall_history || {}

  const model =
    forecast?.model || {}


  // ==========================================================
  // CURRENT / PEAK VALUES
  // ==========================================================

  const currentRecord =
    records.length > 0
      ? records[0]
      : null

  const peakRainfall =
    records.length > 0
      ? Math.max(
          ...records.map(
            (record) =>
              Number(
                record.postprocessed_rainfall_mm
              ) || 0
          )
        )
      : 0

  const peakFloodDepth =
    Number(
      summary.maximum_flood_depth_m
    ) || 0


  // ==========================================================
  // MODEL INPUTS
  // ==========================================================

  const inputs = [
    {
      name: 'NWP',
      value: 'Open-Meteo GFS',
      icon: CloudRain,
      status: true,
    },

    {
      name: 'ML POST-PROCESSOR',
      value: model.type ||
        'HistGradientBoostingRegressor',
      icon: BrainCircuit,
      status: true,
    },

    {
      name: 'HISTORICAL RAINFALL',
      value:
        rainfallHistory.source ||
        'Open-Meteo Historical Archive',
      icon: Database,
      status:
        rainfallHistory.history_available === true,
    },

    {
      name: 'SCS-CN',
      value: 'Runoff estimation',
      icon: Droplets,
      status:
        integration.scs_cn === true,
    },

    {
      name: 'DEM / LULC',
      value: 'Flood screening',
      icon: Map,
      status:
        integration.dem === true &&
        integration.lulc === true,
    },
  ]


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (
      <div className="ai-forecast-page">

        <div className="ai-page-header">

          <div>

            <div className="ai-breadcrumb">
              VARSHAAI / AI INTELLIGENCE / FORECAST
            </div>

            <div className="ai-title-row">

              <div className="ai-title-icon">
                <BrainCircuit size={30} />
              </div>

              <div>

                <h1>
                  AI Forecast
                </h1>

                <p>
                  Loading live NWP + ML flood forecast...
                </p>

              </div>

            </div>

          </div>

        </div>


        <section className="ai-status-banner">

          <div className="ai-status-main">

            <div className="ai-status-icon">
              <RefreshCw
                size={25}
                className="spin"
              />
            </div>

            <div>

              <span className="ai-overline">
                CONNECTING TO BACKEND
              </span>

              <h2>
                Fetching VARSHAAI forecast
              </h2>

              <p>
                Reading the live 72-hour NWP,
                ML post-processing and flood
                integration pipeline.
              </p>

            </div>

          </div>

        </section>

      </div>
    )
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error) {

    return (
      <div className="ai-forecast-page">

        <div className="ai-page-header">

          <div>

            <div className="ai-breadcrumb">
              VARSHAAI / AI INTELLIGENCE / FORECAST
            </div>

            <div className="ai-title-row">

              <div className="ai-title-icon">
                <BrainCircuit size={30} />
              </div>

              <div>

                <h1>
                  AI Forecast
                </h1>

                <p>
                  NWP + ML rainfall and flood prediction
                </p>

              </div>

            </div>

          </div>

        </div>


        <section className="ai-status-banner">

          <div className="ai-status-main">

            <div className="ai-status-icon">
              <AlertTriangle size={25} />
            </div>

            <div>

              <span className="ai-overline">
                BACKEND CONNECTION ERROR
              </span>

              <h2>
                Forecast unavailable
              </h2>

              <p>
                {error}
              </p>

              <button
                type="button"
                onClick={fetchForecast}
                style={{
                  marginTop: '14px',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: '1px solid #2d617a',
                  background: '#0b2636',
                  color: '#dceef6',
                  cursor: 'pointer',
                }}
              >
                <RefreshCw
                  size={15}
                  style={{
                    marginRight: '7px',
                    verticalAlign: 'middle',
                  }}
                />
                Retry
              </button>

            </div>

          </div>

        </section>

      </div>
    )
  }


  // ==========================================================
  // MAIN PAGE
  // ==========================================================

  return (
    <div className="ai-forecast-page">


      {/* ======================================================
          PAGE HEADER
          ====================================================== */}

      <div className="ai-page-header">

        <div>

          <div className="ai-breadcrumb">
            VARSHAAI / AI INTELLIGENCE / FORECAST
          </div>

          <div className="ai-title-row">

            <div className="ai-title-icon">
              <BrainCircuit size={30} />
            </div>

            <div>

              <h1>
                AI Forecast
              </h1>

              <p>
                72-hour NWP + ML rainfall
                and inundation prediction
              </p>

            </div>

          </div>

        </div>


        <div className="ai-engine-status">

          <span className="ai-status-dot"></span>

          LIVE NWP + ML ENGINE ONLINE

        </div>

      </div>


      {/* ======================================================
          CURRENT FORECAST STATUS
          ====================================================== */}

      <section className="ai-status-banner">

        <div className="ai-status-main">

          <div className="ai-status-icon">
            <Activity size={25} />
          </div>

          <div>

            <span className="ai-overline">
              CURRENT FORECAST
            </span>

            <h2>
              Chennai 72-hour rainfall and
              flood screening
            </h2>

            <p>
              Live GFS forecast is passed through
              the trained NWP post-processing model
              and then through the SCS-CN,
              DEM/LULC and inundation screening pipeline.
            </p>

          </div>

        </div>


        <div className="ai-status-metrics">

          <div>

            <span>
              CURRENT
            </span>

            <strong>
              {formatNumber(
                currentRecord?.postprocessed_rainfall_mm,
                2
              )}
            </strong>

            <small>
              mm/hr
            </small>

          </div>


          <div>

            <span>
              PEAK
            </span>

            <strong>
              {formatNumber(
                peakRainfall,
                2
              )}
            </strong>

            <small>
              mm/hr
            </small>

          </div>


          <div>

            <span>
              MAX DEPTH
            </span>

            <strong>
              {formatNumber(
                peakFloodDepth,
                3
              )}
            </strong>

            <small>
              m
            </small>

          </div>

        </div>

      </section>


      {/* ======================================================
          LIVE DATA STRIP
          ====================================================== */}

      <section className="why-models-panel">

        <div className="why-models-icon">
          <Zap size={24} />
        </div>

        <div className="why-models-content">

          <span>
            LIVE INTEGRATION
          </span>

          <h2>
            NWP → ML → Runoff → Flood Depth → Risk
          </h2>

          <p>
            The backend currently connects the
            72-hour NWP forecast to the trained
            HistGradientBoostingRegressor, cumulative
            rainfall calculation, SCS-CN runoff,
            prototype DEM/LULC screening, flood depth,
            inundation classification and CAP-oriented
            risk generation.
          </p>

        </div>


        <div className="why-models-result">

          <div>

            <strong>
              NWP
            </strong>

            <span>
              72 HR
            </span>

          </div>

          <ArrowRight size={18} />

          <div>

            <strong>
              ML
            </strong>

            <span>
              POST-PROCESS
            </span>

          </div>

          <ArrowRight size={18} />

          <div>

            <strong>
              FLOOD
            </strong>

            <span>
              RISK
            </span>

          </div>

        </div>

      </section>


      {/* ======================================================
          MODEL ARCHITECTURE
          ====================================================== */}

      <section className="model-architecture-section">

        <div className="section-heading">

          <div>

            <span className="ai-section-label">
              DUAL-MODEL ARCHITECTURE
            </span>

            <h2>
              Two Forecast Horizons
            </h2>

            <p>
              The current backend provides the
              3–72 hour NWP + ML pathway.
            </p>

          </div>

        </div>


        <div className="model-grid">


          {/* 0–3 HR */}

          <div className="model-card now-model">

            <div className="model-card-top">

              <div className="model-icon">
                <Radar size={25} />
              </div>

              <div className="model-live">
                <span></span>
                ARCHITECTURE READY
              </div>

            </div>


            <div className="model-window">
              0–3 HOURS
            </div>

            <h3>
              VARSHAAI-NOW
            </h3>

            <div className="model-method">
              ConvLSTM Nowcasting
            </div>

            <p>
              Intended to provide short-term
              precipitation nowcasting from
              radar and satellite sequences.
              The current project evidence
              identifies this architecture as
              ready, but it is not presented as
              a trained and validated live model.
            </p>


            <div className="model-inputs">

              <span>
                <Radar size={12} />
                DWR RADAR
              </span>

              <span>
                <Satellite size={12} />
                INSAT
              </span>

              <span>
                <Gauge size={12} />
                AWS / ARG
              </span>

            </div>


            <div className="model-stats">

              <div>

                <span>
                  STATUS
                </span>

                <strong>
                  READY
                </strong>

              </div>

              <div>

                <span>
                  HORIZON
                </span>

                <strong>
                  0–3 HR
                </strong>

              </div>

              <div>

                <span>
                  VALIDATION
                </span>

                <strong>
                  PENDING
                </strong>

              </div>

            </div>

          </div>


          {/* 3–72 HR */}

          <div className="model-card fcast-model">

            <div className="model-card-top">

              <div className="model-icon">
                <CloudRain size={25} />
              </div>

              <div className="model-live">
                <span></span>
                LIVE
              </div>

            </div>


            <div className="model-window">
              3–72 HOURS
            </div>

            <h3>
              VARSHAAI-FCAST
            </h3>

            <div className="model-method">
              NWP + ML Bias Correction
            </div>

            <p>
              Uses the live Open-Meteo GFS
              prototype adapter and the trained
              HistGradientBoostingRegressor
              for rainfall post-processing.
            </p>


            <div className="model-inputs">

              <span>
                <CloudRain size={12} />
                GFS
              </span>

              <span>
                <Wind size={12} />
                ATMOSPHERE
              </span>

              <span>
                <Gauge size={12} />
                HISTORY
              </span>

            </div>


            <div className="model-stats">

              <div>

                <span>
                  STATUS
                </span>

                <strong>
                  LIVE
                </strong>

              </div>

              <div>

                <span>
                  HORIZON
                </span>

                <strong>
                  72 HR
                </strong>

              </div>

              <div>

                <span>
                  RECORDS
                </span>

                <strong>
                  {records.length}
                </strong>

              </div>

            </div>

          </div>

        </div>

      </section>


      {/* ======================================================
          MODEL INPUTS
          ====================================================== */}

      <section className="ai-input-section">

        <div className="section-heading">

          <div>

            <span className="ai-section-label">
              LIVE MODEL PIPELINE
            </span>

            <h2>
              Data & Processing Components
            </h2>

          </div>

        </div>


        <div className="ai-input-grid">

          {inputs.map((input) => {

            const Icon = input.icon

            return (

              <div
                className="ai-input-card"
                key={input.name}
              >

                <div className="ai-input-icon">
                  <Icon size={19} />
                </div>

                <div>

                  <strong>
                    {input.name}
                  </strong>

                  <span>
                    {input.value}
                  </span>

                </div>

                {input.status ? (

                  <CheckCircle2
                    className="input-check"
                    size={15}
                  />

                ) : (

                  <AlertTriangle
                    size={15}
                  />

                )}

              </div>

            )

          })}

        </div>

      </section>


      {/* ======================================================
          72 HOUR RAINFALL CHART
          ====================================================== */}

      <section className="forecast-chart-panel">

        <div className="forecast-chart-header">

          <div>

            <span className="ai-section-label">
              LIVE NWP + ML FORECAST
            </span>

            <h2>
              Chennai — 72 Hour Rainfall Prediction
            </h2>

            <p>
              NWP precipitation compared with
              ML post-processed rainfall.
            </p>

          </div>


          <div className="chart-data-badge">

            {records.length}
            {' '}
            hourly points

          </div>

        </div>


        <div className="chart-source-strip">

          <span>
            SOURCE: OPEN-METEO GFS
          </span>

          <span>
            ML:
            {' '}
            {model.type ||
              'HistGradientBoostingRegressor'}
          </span>

          <span>
            HORIZON: 72 HR
          </span>

          <span>
            REGION: CHENNAI
          </span>

        </div>


        <div className="forecast-chart">

          {chartData.length > 0 ? (

            <ResponsiveContainer
              width="100%"
              height={330}
            >

              <LineChart
                data={chartData}
                margin={{
                  top: 15,
                  right: 20,
                  left: 5,
                  bottom: 10,
                }}
              >

                <CartesianGrid
                  stroke="#173648"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="time"
                  interval="preserveStartEnd"
                  tick={{
                    fill: '#62879c',
                    fontSize: 10,
                  }}
                  axisLine={{
                    stroke: '#24465a',
                  }}
                  tickLine={false}
                />

                <YAxis
                  tick={{
                    fill: '#62879c',
                    fontSize: 10,
                  }}
                  axisLine={{
                    stroke: '#24465a',
                  }}
                  tickLine={false}
                  label={{
                    value: 'Rainfall (mm/hr)',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#62879c',
                    fontSize: 10,
                  }}
                />

                <Tooltip
                  contentStyle={{
                    background: '#091d2b',
                    border: '1px solid #24506a',
                    borderRadius: '8px',
                    color: '#dceef6',
                  }}

                  formatter={(value, name) => {

                    if (
                      name ===
                      'ML Post-Processed'
                    ) {

                      return [
                        `${formatNumber(value)} mm/hr`,
                        name,
                      ]

                    }

                    return [
                      `${formatNumber(value)} mm/hr`,
                      name,
                    ]

                  }}

                  labelFormatter={(label) =>
                    `Time: ${label}`
                  }

                />


                <Line
                  type="monotone"
                  dataKey="nwp"
                  stroke="#9b9ee8"
                  strokeWidth={2}
                  dot={false}
                  name="NWP"
                />


                <Line
                  type="monotone"
                  dataKey="ml"
                  stroke="#43c9f1"
                  strokeWidth={3}
                  dot={false}
                  name="ML Post-Processed"
                />

              </LineChart>

            </ResponsiveContainer>

          ) : (

            <div
              style={{
                padding: '40px',
                textAlign: 'center',
              }}
            >
              No forecast records available.
            </div>

          )}

        </div>


        <div className="chart-legend">

          <span>
            <i className="legend-nwp"></i>
            NWP
          </span>

          <span>
            <i className="legend-nowcast"></i>
            ML Post-Processed
          </span>

        </div>

      </section>


      {/* ======================================================
          FLOOD INTEGRATION
          ====================================================== */}

      <section className="forecast-chart-panel">

        <div className="forecast-chart-header">

          <div>

            <span className="ai-section-label">
              FLOOD INTEGRATION
            </span>

            <h2>
              Rainfall → Runoff → Inundation
            </h2>

            <p>
              The ML rainfall forecast is passed
              through the deterministic prototype
              flood screening pipeline.
            </p>

          </div>

        </div>


        <div className="chart-source-strip">

          <span>
            SCS-CN: {integration.scs_cn ? 'ON' : 'OFF'}
          </span>

          <span>
            DEM: {integration.dem ? 'ON' : 'OFF'}
          </span>

          <span>
            LULC: {integration.lulc ? 'ON' : 'OFF'}
          </span>

          <span>
            INUNDATION:
            {' '}
            {integration.inundation
              ? 'ON'
              : 'OFF'}
          </span>

        </div>


        <div
          style={{
            display: 'grid',
            gridTemplateColumns:
              'repeat(auto-fit,minmax(180px,1fr))',
            gap: '14px',
            padding: '20px 0',
          }}
        >

          <div className="ai-input-card">

            <div className="ai-input-icon">
              <CloudRain size={19} />
            </div>

            <div>

              <strong>
                TOTAL FORECAST
              </strong>

              <span>
                {formatNumber(
                  summary.total_forecast_rainfall_mm,
                  2
                )}
                {' '}
                mm
              </span>

            </div>

          </div>


          <div className="ai-input-card">

            <div className="ai-input-icon">
              <Droplets size={19} />
            </div>

            <div>

              <strong>
                MAX RUNOFF
              </strong>

              <span>
                {formatNumber(
                  Math.max(
                    ...records.map(
                      (r) =>
                        Number(r.runoff_mm) || 0
                    )
                  ),
                  2
                )}
                {' '}
                mm
              </span>

            </div>

          </div>


          <div className="ai-input-card">

            <div className="ai-input-icon">
              <Waves size={19} />
            </div>

            <div>

              <strong>
                MAX FLOOD DEPTH
              </strong>

              <span>
                {formatNumber(
                  summary.maximum_flood_depth_m,
                  3
                )}
                {' '}
                m
              </span>

            </div>

          </div>


          <div className="ai-input-card">

            <div className="ai-input-icon">
              <Map size={19} />
            </div>

            <div>

              <strong>
                FLOODED FRACTION
              </strong>

              <span>
                {formatNumber(
                  (
                    Number(
                      summary.maximum_flooded_fraction
                    ) || 0
                  ) * 100,
                  1
                )}
                %
              </span>

            </div>

          </div>

        </div>

      </section>


      {/* ======================================================
          FORECAST WINDOWS
          ====================================================== */}

      <section className="forecast-window-section">

        <div className="section-heading">

          <div>

            <span className="ai-section-label">
              FORECAST WINDOWS
            </span>

            <h2>
              Operational Prediction Timeline
            </h2>

          </div>

        </div>


        <div className="forecast-window-grid">


          <div className="forecast-window-card">

            <div className="forecast-window-top">

              <div className="window-icon">
                <Radar size={21} />
              </div>

              <span className="window-status">
                ARCHITECTURE READY
              </span>

            </div>


            <span className="window-label">
              NOWCASTING
            </span>

            <h3>
              VARSHAAI-NOW
            </h3>

            <div className="window-method">
              ConvLSTM
            </div>

            <p>
              0–3 hour nowcasting architecture
              using radar and satellite sequences.
              Training and validation remain
              separate from the current live
              NWP pathway.
            </p>


            <div className="window-metrics">

              <div>

                <span>
                  WINDOW
                </span>

                <strong>
                  0–3 HR
                </strong>

              </div>

              <div>

                <span>
                  STATUS
                </span>

                <strong>
                  READY
                </strong>

              </div>

              <div>

                <span>
                  VALIDATION
                </span>

                <strong>
                  PENDING
                </strong>

              </div>

            </div>

          </div>


          <div className="forecast-window-card">

            <div className="forecast-window-top">

              <div className="window-icon">
                <CloudRain size={21} />
              </div>

              <span className="window-status">
                LIVE
              </span>

            </div>


            <span className="window-label">
              EXTENDED FORECAST
            </span>

            <h3>
              VARSHAAI-FCAST
            </h3>

            <div className="window-method">
              NWP + ML
            </div>

            <p>
              Live 72-hour GFS forecast passed
              through the trained rainfall
              post-processing model.
            </p>


            <div className="window-metrics">

              <div>

                <span>
                  WINDOW
                </span>

                <strong>
                  3–72 HR
                </strong>

              </div>

              <div>

                <span>
                  RECORDS
                </span>

                <strong>
                  {records.length}
                </strong>

              </div>

              <div>

                <span>
                  MODEL
                </span>

                <strong>
                  ML
                </strong>

              </div>

            </div>

          </div>

        </div>

      </section>


      {/* ======================================================
          FINAL RISK
          ====================================================== */}

      <section className="ai-output-panel">

        <div className="ai-output-icon">

          {String(
            finalRisk.alert_level || 'GREEN'
          ).toUpperCase() === 'RED' ? (

            <AlertTriangle size={25} />

          ) : (

            <ShieldCheck size={25} />

          )}

        </div>


        <div className="ai-output-content">

          <span>
            FINAL FLOOD RISK
          </span>

          <h2>
            {finalRisk.risk_label ||
              'Flood risk assessment available'}
          </h2>

          <p>
            Maximum predicted depth:
            {' '}
            {formatNumber(
              finalRisk.maximum_depth_m,
              3
            )}
            {' '}
            m.
            {' '}
            Flooded fraction:
            {' '}
            {formatNumber(
              (
                Number(
                  finalRisk.flooded_fraction
                ) || 0
              ) * 100,
              1
            )}
            %.
          </p>

        </div>


        <div
          className={`risk-badge ${
            getRiskClass(
              finalRisk.alert_level
            )
          }`}
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            fontWeight: 700,
            textAlign: 'center',
          }}
        >

          {finalRisk.alert_level ||
            'GREEN'}

        </div>

      </section>


      {/* ======================================================
          PIPELINE
          ====================================================== */}

      <section className="ai-output-panel">

        <div className="ai-output-icon">
          <TrendingUp size={25} />
        </div>


        <div className="ai-output-content">

          <span>
            AI OUTPUT PIPELINE
          </span>

          <h2>
            Rainfall → Flood Depth → Risk → CAP
          </h2>

          <p>
            The current backend integration
            produces a flood screening result
            and CAP-oriented alert payload from
            the NWP + ML forecast.
          </p>

        </div>


        <div className="ai-output-flow">

          <div>

            <strong>
              RAINFALL
            </strong>

            <span>
              ML
            </span>

          </div>

          <ArrowRight size={17} />

          <div>

            <strong>
              RUNOFF
            </strong>

            <span>
              SCS-CN
            </span>

          </div>

          <ArrowRight size={17} />

          <div>

            <strong>
              FLOOD
            </strong>

            <span>
              DEPTH
            </span>

          </div>

          <ArrowRight size={17} />

          <div>

            <strong>
              ALERT
            </strong>

            <span>
              CAP
            </span>

          </div>

        </div>

      </section>


      {/* ======================================================
          STATUS / METADATA
          ====================================================== */}

      <section className="forecast-chart-panel">

        <div className="forecast-chart-header">

          <div>

            <span className="ai-section-label">
              SYSTEM STATUS
            </span>

            <h2>
              VARSHAAI Forecast Metadata
            </h2>

          </div>

        </div>


        <div className="ai-input-grid">

          <div className="ai-input-card">

            <div className="ai-input-icon">
              <Gauge size={19} />
            </div>

            <div>

              <strong>
                MODEL
              </strong>

              <span>
                {model.type ||
                  'HistGradientBoostingRegressor'}
              </span>

            </div>

          </div>


          <div className="ai-input-card">

            <div className="ai-input-icon">
              <CloudRain size={19} />
            </div>

            <div>

              <strong>
                FORECAST
              </strong>

              <span>
                {forecast.forecast_hours || 72}
                {' '}
                hours
              </span>

            </div>

          </div>


          <div className="ai-input-card">

            <div className="ai-input-icon">
              <Map size={19} />
            </div>

            <div>

              <strong>
                GRID
              </strong>

              <span>
                {spatialGrid.rows || 0}
                {' × '}
                {spatialGrid.columns || 0}
                {' '}
                prototype grid
              </span>

            </div>

          </div>


          <div className="ai-input-card">

            <div className="ai-input-icon">
              <Clock size={19} />
            </div>

            <div>

              <strong>
                LAST UPDATED
              </strong>

              <span>
                {formatTimestamp(lastUpdated)}
              </span>

            </div>

          </div>

        </div>

      </section>


      {/* ======================================================
          VALIDATION NOTE
          ====================================================== */}

      <div className="ai-footer-note">

        <ShieldCheck size={14} />

        Current NWP ML inference is live-data-gated.
        The ConvLSTM pathway is an architecture/training
        framework and should not be presented as a trained
        validated live nowcasting model.

      </div>

    </div>
  )
}


export default AIForecast