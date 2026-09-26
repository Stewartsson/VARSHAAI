import { apiFetch } from '../api';
import { useEffect, useState } from 'react'

import {
  CloudRain,
  Waves,
  AlertTriangle,
  Clock3,
  Satellite,
  RadioTower,
  CloudSun,
  Globe2,
  Activity,
  RefreshCw,
} from 'lucide-react'

import MapView from './MapView'

import '../styles/CommandCenter.css'


function CommandCenter() {
  const [dashboard, setDashboard] = useState(null)
  const [sources, setSources] = useState(null)
  const [models, setModels] = useState(null)
  const [flood, setFlood] = useState(null)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [runningPipeline, setRunningPipeline] = useState(false)
  const [pipelineResult, setPipelineResult] = useState(null)
  const [error, setError] = useState('')


  // =====================================================
  // LOAD ALL BACKEND DATA
  // =====================================================

  async function loadData() {
    try {
      setError('')

      const dashboardResponse = await apiFetch('/api/dashboard')
      const sourcesResponse = await apiFetch('/api/sources')
      const modelsResponse = await apiFetch('/api/models')
      const floodResponse = await apiFetch('/api/flood/demo')

      if (!dashboardResponse.ok) {
        throw new Error(
          `Dashboard API error: ${dashboardResponse.status}`,
        )
      }

      if (!sourcesResponse.ok) {
        throw new Error(
          `Sources API error: ${sourcesResponse.status}`,
        )
      }

      if (!modelsResponse.ok) {
        throw new Error(
          `Models API error: ${modelsResponse.status}`,
        )
      }

      if (!floodResponse.ok) {
        throw new Error(
          `Flood API error: ${floodResponse.status}`,
        )
      }

      const dashboardData =
        await dashboardResponse.json()

      const sourcesData =
        await sourcesResponse.json()

      const modelsData =
        await modelsResponse.json()

      const floodData =
        await floodResponse.json()

      setDashboard(dashboardData)
      setSources(sourcesData)
      setModels(modelsData)
      setFlood(floodData)

    } catch (err) {
      console.error(
        'VARSHAAI API ERROR:',
        err,
      )

      setError(
        err instanceof Error
          ? err.message
          : 'Backend connection failed',
      )

    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }


  // =====================================================
  // INITIAL LOAD
  // =====================================================

  useEffect(() => {
    loadData()
  }, [])


  // =====================================================
  // REFRESH
  // =====================================================

  async function handleRefresh() {
    setRefreshing(true)
    await loadData()
  }

  async function runPipeline() {
    try {
      setRunningPipeline(true)
      setError('')
      const response = await apiFetch('/api/pipeline/run')
      if (!response.ok) {
        throw new Error(`Pipeline API error: ${response.status}`)
      }
      const data = await response.json()
      setPipelineResult(data)
      // We can also reload the main dashboard data if needed
      await loadData()
    } catch (err) {
      console.error('Pipeline error:', err)
      setError(err instanceof Error ? err.message : 'Pipeline execution failed')
    } finally {
      setRunningPipeline(false)
    }
  }

  // =====================================================
  // SAFE DATA EXTRACTION
  // =====================================================

  const location =
    dashboard?.location || {}

  const weather =
    dashboard?.weather || {}

  const current =
    weather?.current || weather || {}


  // =====================================================
  // WEATHER
  // =====================================================

  const rainfall =
    Number(
      current?.precipitation ??
      current?.rainfall ??
      current?.rainfall_mm ??
      0,
    )

  const temperature =
    Number(
      current?.temperature_2m ??
      current?.temperature ??
      current?.temperature_c ??
      0,
    )

  const humidity =
    Number(
      current?.relative_humidity_2m ??
      current?.humidity ??
      0,
    )

  const wind =
    Number(
      current?.wind_speed_10m ??
      current?.wind_speed ??
      0,
    )


  // =====================================================
  // FLOOD DATA
  // =====================================================

  const risk =
    flood?.risk || {}

  const maximumDepth =
    Number(
      risk?.maximum_depth_m ?? 0,
    )

  const meanDepth =
    Number(
      risk?.mean_flood_depth_m ?? 0,
    )

  const floodedFraction =
    Number(
      risk?.flooded_fraction ?? 0,
    )

  const confidence =
    Number(
      risk?.confidence ?? 0,
    )

  const floodedPixels =
    Number(
      risk?.flooded_pixels ?? 0,
    )

  const totalPixels =
    Number(
      risk?.total_valid_pixels ?? 0,
    )

  const alertLevel =
    risk?.alert_level || 'UNKNOWN'

  const riskLabel =
    risk?.risk_label || 'Flood risk unavailable'


  // =====================================================
  // SOURCE STATUS
  // =====================================================

  const sourceList =
    sources?.sources || {}

  const satelliteStatus =
    sourceList?.satellite?.status || 'PENDING'

  const radarStatus =
    sourceList?.radar?.status || 'PENDING'

  const awsStatus =
    sourceList?.aws?.status || 'PENDING'

  const argStatus =
    sourceList?.arg?.status || 'PENDING'

  const nwpStatus =
    sourceList?.nwp?.status || 'PENDING'


  // =====================================================
  // MODEL STATUS
  // =====================================================

  const nowcasting =
    models?.nowcasting || {}

  const nwpModel =
    models?.nwp_postprocessing || {}


  // =====================================================
  // HELPERS
  // =====================================================

  function formatNumber(value, decimals = 1) {
    if (!Number.isFinite(value)) {
      return '--'
    }

    return value.toFixed(decimals)
  }


  function formatPercent(value) {
    if (!Number.isFinite(value)) {
      return '--'
    }

    return `${(value * 100).toFixed(1)}%`
  }


  function getRiskClass() {
    if (alertLevel === 'GREEN') {
      return 'risk-green'
    }

    if (alertLevel === 'YELLOW') {
      return 'risk-yellow'
    }

    if (alertLevel === 'ORANGE') {
      return 'risk-orange'
    }

    if (alertLevel === 'RED') {
      return 'risk-red'
    }

    return ''
  }


  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <div className="command-center">

        <div className="command-header">

          <div>
            <div className="command-breadcrumb">
              VARSHAAI / INTELLIGENCE PLATFORM
            </div>

            <h1>Command Center</h1>

            <p>
              Real-time heavy rainfall and inundation intelligence
            </p>
          </div>

          <div className="command-live">
            <span className="live-dot" />
            CONNECTING
          </div>

        </div>

        <div className="loading-panel">
          <RefreshCw
            size={24}
            className="spinning"
          />

          Connecting to VARSHAAI backend...
        </div>

      </div>
    )
  }


  // =====================================================
  // MAIN PAGE
  // =====================================================

  return (
    <div className="command-center">


      {/* =================================================
          HEADER
      ================================================= */}

      <div className="command-header">

        <div>

          <div className="command-breadcrumb">
            VARSHAAI / INTELLIGENCE PLATFORM
          </div>

          <h1>
            Command Center
          </h1>

          <p>
            Real-time heavy rainfall and inundation intelligence
          </p>

        </div>


        <div className="command-live">

          <span className="live-dot" />

          BACKEND CONNECTED

        </div>

      </div>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (
        <div className="error-banner">

          <AlertTriangle size={18} />

          <span>
            Backend connection error: {error}
          </span>

        </div>
      )}


      {/* =================================================
          KPI CARDS
      ================================================= */}

      <div className="kpi-grid">


        {/* CURRENT RAINFALL */}

        <div className="kpi-card">

          <div className="kpi-top">

            <span className="kpi-label">
              CURRENT RAINFALL
            </span>

            <div className="kpi-icon">
              <CloudRain size={22} />
            </div>

          </div>

          <div className="kpi-value">

            {formatNumber(rainfall)}

            <span>
              mm
            </span>

          </div>

          <div className="kpi-footer">
            Open-Meteo live prototype
          </div>

        </div>


        {/* FLOOD DEPTH */}

        <div className="kpi-card">

          <div className="kpi-top">

            <span className="kpi-label">
              PREDICTED FLOOD DEPTH
            </span>

            <div className="kpi-icon">
              <Waves size={22} />
            </div>

          </div>

          <div className="kpi-value">

            {formatNumber(maximumDepth, 2)}

            <span>
              m
            </span>

          </div>

          <div className="kpi-footer">
            SCS-CN + DEM screening
          </div>

        </div>


        {/* RISK */}

        <div
          className={`kpi-card ${getRiskClass()}`}
        >

          <div className="kpi-top">

            <span className="kpi-label">
              INUNDATION RISK
            </span>

            <div className="kpi-icon">
              <AlertTriangle size={22} />
            </div>

          </div>

          <div className="risk-value">
            {alertLevel}
          </div>

          <div className="risk-indicator">

            <span className="risk-dot" />

            {riskLabel}

          </div>

        </div>


        {/* NOWCASTING */}

        <div className="kpi-card">

          <div className="kpi-top">

            <span className="kpi-label">
              NOWCASTING HORIZON
            </span>

            <div className="kpi-icon">
              <Clock3 size={22} />
            </div>

          </div>

          <div className="kpi-value">

            0–3

            <span>
              hr
            </span>

          </div>

          <div className="kpi-footer">
            VARSHAAI-NOW ConvLSTM
          </div>

        </div>

      </div>


      {/* =================================================
          MAP + INTELLIGENCE
      ================================================= */}

      <div className="command-main-grid">


        {/* MAP */}

        <section className="map-panel">

          <div className="panel-header">

            <div>

              <h2>
                Situational Awareness Map
              </h2>

              <p>
                Rainfall, inundation and observation layers
              </p>

            </div>

            <div className="map-live-status">

              <Activity size={14} />

              LIVE

            </div>

          </div>


          <div className="map-container">

            <MapView />

            <div className="map-live-layer">

              <span className="live-dot" />

              LIVE PREDICTION LAYER

            </div>

          </div>

        </section>


        {/* SYSTEM INTELLIGENCE */}

        <section className="information-panel">

          <div className="panel-header">

            <div>

              <h2>
                System Intelligence
              </h2>

              <p>
                Current prediction status
              </p>

            </div>

          </div>


          {/* REGION */}

          <div className="location-box">

            <div className="location-title">
              MONITORED REGION
            </div>

            <div className="location-name">

              {location?.name || 'Chennai'}

            </div>

            <div className="location-detail">

              {location?.state || 'Tamil Nadu'}, India

            </div>

          </div>


          {/* WEATHER */}

          <div className="forecast-summary">

            <div className="summary-title">
              CURRENT WEATHER
            </div>


            <div className="forecast-row">

              <span>
                Rainfall
              </span>

              <strong>
                {formatNumber(rainfall)} mm
              </strong>

            </div>


            <div className="forecast-row">

              <span>
                Temperature
              </span>

              <strong>

                {temperature
                  ? `${formatNumber(temperature)}°C`
                  : '--'}

              </strong>

            </div>


            <div className="forecast-row">

              <span>
                Humidity
              </span>

              <strong>

                {humidity
                  ? `${formatNumber(humidity, 0)}%`
                  : '--'}

              </strong>

            </div>


            <div className="forecast-row">

              <span>
                Wind
              </span>

              <strong>

                {wind
                  ? `${formatNumber(wind)} km/h`
                  : '--'}

              </strong>

            </div>

          </div>


          {/* FLOOD ASSESSMENT */}

          <div className="forecast-summary">

            <div className="summary-title">
              FLOOD ASSESSMENT
            </div>


            <div className="forecast-row">

              <span>
                Maximum depth
              </span>

              <strong>
                {formatNumber(maximumDepth, 2)} m
              </strong>

            </div>


            <div className="forecast-row">

              <span>
                Mean depth
              </span>

              <strong>
                {formatNumber(meanDepth, 2)} m
              </strong>

            </div>


            <div className="forecast-row">

              <span>
                Flooded area
              </span>

              <strong>
                {formatPercent(floodedFraction)}
              </strong>

            </div>


            <div className="forecast-row">

              <span>
                Confidence
              </span>

              <strong>
                {formatPercent(confidence)}
              </strong>

            </div>

          </div>


          {/* MODEL STATUS */}

          <div className="ai-status-box">

            <div className="summary-title">
              AI MODEL STATUS
            </div>


            <div className="model-status">

              <div>

                <div className="model-name">
                  VARSHAAI-NOW
                </div>

                <div className="model-description">

                  {nowcasting?.model || 'ConvLSTM'}
                  {' • '}
                  {nowcasting?.horizon || '0–3 hours'}

                </div>

              </div>

              <span className="model-ready">
                READY
              </span>

            </div>


            <div className="model-status">

              <div>

                <div className="model-name">
                  VARSHAAI-FCAST
                </div>

                <div className="model-description">

                  {nwpModel?.model ||
                    'Gradient Boosting'}

                  {' • '}

                  {nwpModel?.horizon ||
                    '3–72 hours'}

                </div>

              </div>

              <span className="model-ready">
                READY
              </span>

            </div>

          </div>


          {/* FLOOD GRID */}

          <div className="grid-summary">

            <Globe2 size={20} />

            <div>

              <div className="summary-title">
                FLOOD GRID
              </div>

              <strong>
                {floodedPixels} / {totalPixels} pixels flooded
              </strong>

              <p>
                Terrain-aware inundation screening
              </p>

            </div>

          </div>

        </section>

      </div>


      {/* =================================================
          MULTI-SOURCE PIPELINE
      ================================================= */}

      <section className="data-source-panel">

        <div className="data-source-header">

          <div>

            <h2>
              Multi-Source Data Pipeline
            </h2>

            <p>
              Integrated meteorological observations
            </p>

          </div>


          <button
            className="refresh-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >

            <RefreshCw
              size={14}
              className={
                refreshing
                  ? 'spinning'
                  : ''
              }
            />

            {refreshing
              ? 'Refreshing'
              : 'Refresh'}

          </button>

          <button
            className="refresh-button pipeline-button"
            onClick={runPipeline}
            disabled={runningPipeline}
            style={{ marginLeft: '10px', backgroundColor: 'var(--red)', color: 'white' }}
          >
            <Activity
              size={14}
              className={runningPipeline ? 'spinning' : ''}
            />
            {runningPipeline ? 'Running AI Engine...' : 'Run SIH Pipeline'}
          </button>

        </div>
        
        {pipelineResult && (
          <div style={{ padding: '16px', backgroundColor: 'rgba(0,0,0,0.2)', marginBottom: '20px', borderRadius: '8px', borderLeft: '4px solid var(--red)' }}>
            <h3 style={{ margin: '0 0 10px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} color="var(--red)" />
              End-to-End Pipeline Completed
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <strong>Pipeline Execution Steps:</strong>
                <ul style={{ paddingLeft: '20px', margin: '8px 0', fontSize: '0.9em', color: 'var(--text-muted)' }}>
                  {pipelineResult.pipeline_steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
                <div style={{ marginTop: '10px', fontSize: '0.8em', color: pipelineResult.latency_budget_met ? 'var(--green)' : 'var(--red)' }}>
                  <strong>Total Latency: {pipelineResult.latency_profile.total_pipeline_ms} ms</strong>
                  <br />(Budget &lt; 5 mins: {pipelineResult.latency_budget_met ? 'PASS' : 'FAIL'})
                </div>
              </div>
              <div>
                <strong>Block-Level Risk Granularity:</strong>
                <div style={{ marginTop: '8px', fontSize: '0.9em', color: 'var(--text-muted)' }}>
                  {Object.entries(pipelineResult.results.block_assessments).map(([block, assessment]) => (
                    <div key={block} style={{ marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{block}</span>
                      <span>
                        <strong style={{color: 'white', marginRight: '8px'}}>{assessment.max_depth_m.toFixed(2)}m</strong>
                        <span style={{ 
                          color: assessment.risk_level === 'RED' ? 'var(--red)' : 
                                 assessment.risk_level === 'ORANGE' ? 'orange' : 
                                 assessment.risk_level === 'YELLOW' ? 'yellow' : 'var(--green)',
                          fontWeight: 'bold'
                        }}>
                          {assessment.risk_level}
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div style={{ marginTop: '16px', fontSize: '0.8em' }}>
              <strong>Generated CAP 1.2 XML:</strong>
              <pre style={{ backgroundColor: '#000', padding: '10px', borderRadius: '4px', marginTop: '8px', overflowX: 'auto' }}>
                {pipelineResult.cap_xml_snippet}
              </pre>
            </div>
          </div>
        )}

        <div className="source-grid">


          {/* SATELLITE */}

          <div className="source-card">

            <div className="source-icon">
              <Satellite size={20} />
            </div>

            <div className="source-content">

              <strong>
                INSAT-3D / 3DR
              </strong>

              <span>
                Satellite
              </span>

              <small>
                ~4 km • 30 min
              </small>

            </div>

            <div className="source-status">

              <span />

              {satelliteStatus}

            </div>

          </div>


          {/* RADAR */}

          <div className="source-card">

            <div className="source-icon">
              <RadioTower size={20} />
            </div>

            <div className="source-content">

              <strong>
                DWR RADAR
              </strong>

              <span>
                Reflectivity
              </span>

              <small>
                ~1 km • 10 min
              </small>

            </div>

            <div className="source-status">

              <span />

              {radarStatus}

            </div>

          </div>


          {/* AWS */}

          <div className="source-card">

            <div className="source-icon">
              <CloudSun size={20} />
            </div>

            <div className="source-content">

              <strong>
                AWS
              </strong>

              <span>
                Weather stations
              </span>

              <small>
                Point • 10 min
              </small>

            </div>

            <div className="source-status">

              <span />

              {awsStatus}

            </div>

          </div>


          {/* ARG */}

          <div className="source-card">

            <div className="source-icon">
              <CloudRain size={20} />
            </div>

            <div className="source-content">

              <strong>
                ARG
              </strong>

              <span>
                Rain gauges
              </span>

              <small>
                Point • 10 min
              </small>

            </div>

            <div className="source-status">

              <span />

              {argStatus}

            </div>

          </div>


          {/* NWP */}

          <div className="source-card">

            <div className="source-icon">
              <Globe2 size={20} />
            </div>

            <div className="source-content">

              <strong>
                NWP
              </strong>

              <span>
                WRF / GFS / IMD
              </span>

              <small>
                ~12 km • 3–6 hr
              </small>

            </div>

            <div className="source-status">

              <span />

              {nwpStatus}

            </div>

          </div>

        </div>

      </section>


      {/* =================================================
          HARMONIZATION
      ================================================= */}

      <section className="harmonization-panel">

        <div className="harmonization-title">
          DATA HARMONIZATION
        </div>


        <div className="harmonization-flow">


          <div className="harmonization-source">

            Satellite

            <small>
              ~4 km / 30 min
            </small>

          </div>


          <div className="flow-arrow">
            →
          </div>


          <div className="harmonization-source">

            Radar

            <small>
              ~1 km / 10 min
            </small>

          </div>


          <div className="flow-arrow">
            →
          </div>


          <div className="harmonization-source">

            AWS / ARG

            <small>
              Point / 10 min
            </small>

          </div>


          <div className="flow-arrow">
            →
          </div>


          <div className="harmonization-source">

            NWP

            <small>
              ~12 km / 3–6 hr
            </small>

          </div>


          <div className="flow-arrow">
            →
          </div>


          <div className="common-grid">

            <strong>
              COMMON GRID
            </strong>

            <small>
              4 km • 30 min
            </small>

          </div>

        </div>

      </section>


      {/* =================================================
          PROTOTYPE NOTICE
      ================================================= */}

      <div className="prototype-notice">

        <AlertTriangle size={18} />

        <div>

          <strong>
            Prototype data notice
          </strong>

          <p>
            Weather currently uses the live Open-Meteo
            prototype. Satellite, DWR radar, AWS, ARG and
            NWP operational feeds remain pending approved
            access. Flood values are generated by the
            current SCS-CN + DEM/LULC screening pipeline.
          </p>

        </div>

      </div>

    </div>
  )
}


export default CommandCenter
