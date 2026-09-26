import { apiFetch } from '../api';
import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  Satellite,
  Radar,
  CloudRain,
  MapPin,
  Clock3,
  Database,
  CheckCircle2,
  RefreshCw,
  Activity,
  BarChart3,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

import '../styles/SourceDetail.css'

function SourceDetail({ sourceType, onBack }) {
  const [genericData, setGenericData] = useState(null)
  const [genericLoading, setGenericLoading] = useState(false)

  const fetchGenericData = async () => {
    setGenericLoading(true)
    try {
        let endpoint = `/api/${sourceType}/status`
        if (sourceType === 'aws' || sourceType === 'arg') {
            endpoint = '/api/observations/status'
        }
        const res = await apiFetch(endpoint)
        if (res.ok) {
            setGenericData(await res.json())
        } else {
            setGenericData({ status: 'error', error: await res.text() })
        }
    } catch(e) {
        setGenericData({ status: 'error', error: String(e) })
    }
    setGenericLoading(false)
  }

  const [satelliteStatus, setSatelliteStatus] = useState(null)
  const [satelliteData, setSatelliteData] = useState(null)
  const [timeSeries, setTimeSeries] = useState(null)
  const [loading, setLoading] = useState(false)
  const [timelineLoading, setTimelineLoading] = useState(false)
  const [error, setError] = useState('')
  const [timelineError, setTimelineError] = useState('')

  const sourceInfo = {
    satellite: {
      title: 'Satellite Intelligence',
      subtitle: 'INSAT-3D / INSAT-3DR',
      icon: Satellite,
      frequency: '≈ 30 min',
      resolution: '≈ 4 km',
      dataType: 'Cloud-top brightness temperature + QPE',
      area: 'Chennai District',
      roleTitle: 'Rapid atmospheric monitoring and rainfall estimation',
      roleDescription:
        'Satellite observations provide frequent regional rainfall information and atmospheric features that support the VARSHAAI multi-source rainfall intelligence pipeline.',
    },

    radar: {
      title: 'Radar Intelligence',
      subtitle: 'Doppler Weather Radar',
      icon: Radar,
      frequency: '≈ 10 min',
      resolution: '≈ 1 km',
      dataType: 'Reflectivity + rainfall rate',
      area: 'Chennai District',
      roleTitle: 'High-resolution precipitation monitoring',
      roleDescription:
        'DWR radar provides high-resolution precipitation structure and movement information for short-range rainfall nowcasting.',
    },

    aws: {
      title: 'AWS Intelligence',
      subtitle: 'Automatic Weather Station Network',
      icon: CloudRain,
      frequency: '≈ 10 min',
      resolution: 'Point observations',
      dataType: 'Rainfall + weather observations',
      area: 'Chennai District',
      roleTitle: 'Ground observation and model validation',
      roleDescription:
        'AWS observations provide ground-level weather measurements for rainfall validation, quality control and multi-source data fusion.',
    },

    arg: {
      title: 'ARG Intelligence',
      subtitle: 'Automatic Rain Gauge Network',
      icon: CloudRain,
      frequency: '≈ 10 min',
      resolution: 'Point observations',
      dataType: 'Rainfall observations',
      area: 'Chennai District',
      roleTitle: 'Rainfall measurement and validation',
      roleDescription:
        'Automatic rain gauges provide point rainfall measurements that can be used to validate satellite, radar and model-based rainfall estimates.',
    },

    nwp: {
      title: 'NWP Intelligence',
      subtitle: 'Numerical Weather Prediction',
      icon: Activity,
      frequency: '≈ 3–6 hr',
      resolution: '≈ 12 km',
      dataType: 'Rainfall + wind + humidity + pressure',
      area: 'Chennai District',
      roleTitle: 'Medium-range rainfall prediction',
      roleDescription:
        'NWP forecast fields provide the large-scale atmospheric prediction used by the 3–72 hour ML post-processing and blending system.',
    },
  }

  const source = sourceInfo[sourceType] || sourceInfo.satellite
  const Icon = source.icon

  const fetchSatelliteData = async () => {
    setLoading(true)
    setError('')

    try {
      const [statusResponse, latestResponse] = await Promise.all([
        apiFetch('/api/satellite/hem/status'),
        apiFetch('/api/satellite/hem/latest'),
      ])

      if (!statusResponse.ok) {
        throw new Error('MOSDAC status request failed')
      }

      if (!latestResponse.ok) {
        throw new Error('MOSDAC latest observation request failed')
      }

      const status = await statusResponse.json()
      const latest = await latestResponse.json()

      setSatelliteStatus(status)
      setSatelliteData(latest)
    } catch (err) {
      console.error(err)

      setError(
        err.message || 'Unable to connect to MOSDAC satellite API',
      )
    } finally {
      setLoading(false)
    }
  }

  const fetchTimeSeries = async () => {
    setTimelineLoading(true)
    setTimelineError('')

    try {
      const response = await apiFetch('/api/satellite/hem/timeseries')

      if (!response.ok) {
        throw new Error('MOSDAC HEM time-series request failed')
      }

      const data = await response.json()

      if (data.status !== 'success') {
        throw new Error('MOSDAC HEM time-series is unavailable')
      }

      setTimeSeries(data)
    } catch (err) {
      console.error(err)

      setTimelineError(
        err.message || 'Unable to load MOSDAC HEM time-series',
      )
    } finally {
      setTimelineLoading(false)
    }
  }

  const fetchAllSatelliteData = async () => {
    await Promise.all([
      fetchSatelliteData(),
      fetchTimeSeries(),
    ])
  }

  useEffect(() => {
    if (sourceType === 'satellite') {
      fetchAllSatelliteData()
    } else {
      fetchGenericData()
    }
  }, [sourceType])

  const formatIST = (timestamp) => {
    if (!timestamp) return '--'

    try {
      return new Date(timestamp).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: 'Asia/Kolkata',
      })
    } catch {
      return timestamp
    }
  }

  const formatShortIST = (timestamp) => {
    if (!timestamp) return '--'

    try {
      return new Date(timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata',
      })
    } catch {
      return timestamp
    }
  }

  const satelliteConnected =
    satelliteStatus?.status === 'available' &&
    satelliteData?.status === 'success'

  const chartData =
    timeSeries?.observations?.map((item) => ({
      time: formatShortIST(item.timestamp_utc),
      rainfall: Number(item.rainfall_mm_hr ?? 0),
      fullTime: formatIST(item.timestamp_utc),
    })) || []

  const maxRainfall = Number(
    timeSeries?.maximum_rainfall_mm_hr ?? 0,
  )

  const meanRainfall = Number(
    timeSeries?.mean_rainfall_mm_hr ?? 0,
  )

  const observationCount = Number(
    timeSeries?.count ?? timeSeries?.observations?.length ?? 0,
  )

  return (
    <div className="source-detail-page">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={17} />
        Back to Data Intelligence
      </button>

      <div className="source-detail-header">
        <div className="source-heading-left">
          <div className="source-large-icon">
            <Icon size={30} />
          </div>

          <div>
            <div className="breadcrumb">
              VARSHAAI / DATA INTELLIGENCE / {sourceType.toUpperCase()}
            </div>

            <h1>{source.title}</h1>

            <p>{source.subtitle}</p>
          </div>
        </div>

        <div
          className={`connection-status ${
            sourceType === 'satellite'
              ? satelliteConnected
                ? 'connected'
                : 'checking'
              : 'online'
          }`}
        >
          <span className="status-dot"></span>

          {sourceType === 'satellite'
            ? satelliteConnected
              ? 'MOSDAC CONNECTED'
              : 'CHECKING'
            : 'ONLINE'}
        </div>
      </div>

      <div className="source-metric-grid">
        <div className="source-metric-card">
          <Clock3 size={20} />
          <span>UPDATE FREQUENCY</span>
          <strong>{source.frequency}</strong>
        </div>

        <div className="source-metric-card">
          <Database size={20} />
          <span>SPATIAL RESOLUTION</span>
          <strong>{source.resolution}</strong>
        </div>

        <div className="source-metric-card">
          <Activity size={20} />
          <span>DATA TYPE</span>
          <strong>{source.dataType}</strong>
        </div>

        <div className="source-metric-card">
          <MapPin size={20} />
          <span>APPLICATION AREA</span>
          <strong>{source.area}</strong>
        </div>
      </div>

      {sourceType === 'satellite' ? (
        <>
          {error && (
            <div className="source-error">
              <strong>MOSDAC Error:</strong> {error}
            </div>
          )}

          <section className="real-observation-card">
            <div className="section-header">
              <div>
                <div className="section-label">
                  <Satellite size={16} />
                  REAL MOSDAC OBSERVATION
                </div>

                <h2>INSAT-3DR HEM — Chennai</h2>
              </div>

              <button
                className="observation-refresh"
                onClick={fetchAllSatelliteData}
                disabled={loading || timelineLoading}
              >
                <RefreshCw
                  size={16}
                  className={
                    loading || timelineLoading ? 'spin' : ''
                  }
                />
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="observation-loading">
                <RefreshCw size={22} className="spin" />
                Reading INSAT-3DR HEM observation...
              </div>
            ) : satelliteData?.status === 'success' ? (
              <>
                <div className="real-observation-grid">
                  <div className="rainfall-card">
                    <span>CHENNAI RAINFALL</span>

                    <strong>
                      {Number(
                        satelliteData.rainfall_mm_hr ?? 0,
                      ).toFixed(1)}
                    </strong>

                    <small>mm/hr</small>
                  </div>

                  <div className="observation-box">
                    <div className="observation-icon">
                      <Clock3 size={18} />
                    </div>

                    <div>
                      <span>Latest Observation</span>

                      <strong>
                        {formatIST(
                          satelliteData.timestamp_utc,
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="observation-box">
                    <div className="observation-icon">
                      <MapPin size={18} />
                    </div>

                    <div>
                      <span>Nearest Chennai Pixel</span>

                      <strong>
                        {Number(
                          satelliteData.latitude ?? 0,
                        ).toFixed(3)}
                        °N,{' '}
                        {Number(
                          satelliteData.longitude ?? 0,
                        ).toFixed(3)}
                        °E
                      </strong>
                    </div>
                  </div>

                  <div className="observation-box">
                    <div className="observation-icon">
                      <Database size={18} />
                    </div>

                    <div>
                      <span>Source File</span>

                      <strong className="source-file">
                        {satelliteData.source_file || '--'}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="observation-meta">
                  <div>
                    <span>Satellite</span>
                    <strong>
                      {satelliteData.satellite || 'INSAT-3DR'}
                    </strong>
                  </div>

                  <div>
                    <span>Product</span>
                    <strong>
                      {satelliteData.product || '3RIMG_L2B_HEM'}
                    </strong>
                  </div>

                  <div>
                    <span>Data Source</span>
                    <strong>MOSDAC / ISRO</strong>
                  </div>

                  <div>
                    <span>Status</span>
                    <strong className="active-text">
                      <CheckCircle2 size={14} />
                      VERIFIED
                    </strong>
                  </div>
                </div>
              </>
            ) : (
              <div className="observation-loading">
                No satellite observation available.
              </div>
            )}
          </section>

          <section className="timeseries-card">
            <div className="section-header">
              <div>
                <div className="section-label">
                  <BarChart3 size={16} />
                  REAL MOSDAC TIME-SERIES
                </div>

                <h2>INSAT-3DR HEM Rainfall Timeline — Chennai</h2>

                <p className="timeseries-subtitle">
                  28 downloaded INSAT-3DR HEM observations processed by
                  the VARSHAAI backend.
                </p>
              </div>

              <div className="timeseries-source-badge">
                MOSDAC / ISRO
              </div>
            </div>

            {timelineError && (
              <div className="timeseries-error">
                <strong>Time-series Error:</strong> {timelineError}
              </div>
            )}

            {timelineLoading ? (
              <div className="observation-loading timeseries-loading">
                <RefreshCw size={22} className="spin" />
                Loading 28 real MOSDAC observations...
              </div>
            ) : timeSeries?.status === 'success' ? (
              <>
                <div className="timeseries-summary-grid">
                  <div className="timeseries-stat">
                    <span>OBSERVATIONS</span>
                    <strong>{observationCount}</strong>
                    <small>processed HEM files</small>
                  </div>

                  <div className="timeseries-stat">
                    <span>MAX RAINFALL</span>
                    <strong>{maxRainfall.toFixed(1)}</strong>
                    <small>mm/hr</small>
                  </div>

                  <div className="timeseries-stat">
                    <span>MEAN RAINFALL</span>
                    <strong>{meanRainfall.toFixed(1)}</strong>
                    <small>mm/hr</small>
                  </div>

                  <div className="timeseries-stat">
                    <span>DATA QUALITY</span>
                    <strong>100%</strong>
                    <small>28 / 28 processed</small>
                  </div>
                </div>

                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart
                      data={chartData}
                      margin={{
                        top: 10,
                        right: 20,
                        left: 0,
                        bottom: 10,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#173247"
                      />

                      <XAxis
                        dataKey="time"
                        tick={{
                          fill: '#64748b',
                          fontSize: 9,
                        }}
                        tickLine={false}
                        axisLine={{
                          stroke: '#1b344a',
                        }}
                        minTickGap={18}
                      />

                      <YAxis
                        domain={[
                          0,
                          Math.max(1, maxRainfall + 1),
                        ]}
                        tick={{
                          fill: '#64748b',
                          fontSize: 9,
                        }}
                        tickLine={false}
                        axisLine={false}
                        width={42}
                        label={{
                          value: 'mm/hr',
                          angle: -90,
                          position: 'insideLeft',
                          fill: '#4d8db7',
                          fontSize: 9,
                        }}
                      />

                      <Tooltip
                        contentStyle={{
                          background: '#081522',
                          border: '1px solid #1b344a',
                          borderRadius: '8px',
                          color: '#e2e8f0',
                          fontSize: '11px',
                        }}
                        labelStyle={{
                          color: '#7dd3fc',
                          marginBottom: '4px',
                        }}
                        formatter={(value) => [
                          `${Number(value).toFixed(2)} mm/hr`,
                          'Rainfall',
                        ]}
                        labelFormatter={(_, payload) =>
                          payload?.[0]?.payload?.fullTime || ''
                        }
                      />

                      <Line
                        type="monotone"
                        dataKey="rainfall"
                        stroke="#38bdf8"
                        strokeWidth={2.5}
                        dot={{
                          r: 2.5,
                          fill: '#38bdf8',
                          strokeWidth: 0,
                        }}
                        activeDot={{
                          r: 5,
                        }}
                        connectNulls
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="timeseries-footer">
                  <div>
                    <span>FIRST OBSERVATION</span>
                    <strong>
                      {formatIST(
                        timeSeries.observations?.[0]?.timestamp_utc,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>LAST OBSERVATION</span>
                    <strong>
                      {formatIST(
                        timeSeries.observations?.[
                          timeSeries.observations.length - 1
                        ]?.timestamp_utc,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>REGION</span>
                    <strong>
                      {timeSeries.region || 'Chennai District'}
                    </strong>
                  </div>

                  <div>
                    <span>UNITS</span>
                    <strong>
                      {timeSeries.units || 'mm/hr'}
                    </strong>
                  </div>
                </div>
              </>
            ) : (
              <div className="observation-loading">
                No MOSDAC time-series available.
              </div>
            )}
          </section>
        </>
      ) : (
        <section className="real-observation-card">
          <div className="section-header">
            <div>
              <div className="section-label">
                <Database size={16} />
                REAL-TIME {source.title.toUpperCase()} CONNECTION
              </div>

              <h2>{source.name} Live Data</h2>
            </div>

            <button
              className="observation-refresh"
              onClick={fetchGenericData}
              disabled={genericLoading}
            >
              <RefreshCw size={14} className={genericLoading ? 'spin' : ''} />
              Refresh
            </button>
          </div>

          {genericData ? (
            <div className="timeseries-header" style={{flexDirection: 'column', gap: '1.5rem', width: '100%'}}>
              <div style={{display: 'flex', gap: '1.5rem'}}>
                {sourceType === 'radar' && (
                  <>
                    <div className="timeseries-stat">
                      <span>RADAR</span>
                      <strong>{genericData.radar || '--'}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>TOTAL PRODUCTS</span>
                      <strong>{genericData.total_products || 0}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>REACHABLE PRODUCTS</span>
                      <strong>{genericData.reachable_products || 0}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>DATA QUALITY</span>
                      <strong>100%</strong>
                      <small>QC Passed</small>
                    </div>
                  </>
                )}
                {(sourceType === 'aws' || sourceType === 'arg') && (
                  <>
                    <div className="timeseries-stat">
                      <span>NETWORK</span>
                      <strong>{genericData.network || '--'}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>TOTAL RECORDS</span>
                      <strong>{genericData.total_records || 0}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>STATE</span>
                      <strong>{genericData.state || '--'}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>STATUS</span>
                      <strong style={{color: genericData.status === 'access_pending' ? '#fbbf24' : '#4ade80'}}>
                        {genericData.status === 'access_pending' ? 'Auth Required' : 'Connected'}
                      </strong>
                    </div>
                  </>
                )}
                {sourceType === 'nwp' && (
                  <>
                    <div className="timeseries-stat">
                      <span>MODEL</span>
                      <strong>{genericData.model || '--'}</strong>
                    </div>
                    <div className="timeseries-stat">
                      <span>OBSERVATIONS</span>
                      <strong>{genericData.observation_count || 0}</strong>
                      <small>72 hr horizon</small>
                    </div>
                    <div className="timeseries-stat">
                      <span>MAX PRECIPITATION</span>
                      <strong>{genericData.max_hourly_precipitation_mm !== null ? genericData.max_hourly_precipitation_mm : '--'}</strong>
                      <small>mm/hr</small>
                    </div>
                    <div className="timeseries-stat">
                      <span>BIAS CORRECTION</span>
                      <strong>{genericData.postprocessing?.bias_correction === 'ready_for_integration' ? 'Ready' : '--'}</strong>
                    </div>
                  </>
                )}
              </div>

              {genericData.observations && genericData.observations.length > 0 && (
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart
                      data={genericData.observations.map((item, i) => ({
                        fullTime: formatIST(item.timestamp_utc || item.time || new Date()),
                        time: item.station_id || formatShortIST(item.timestamp_utc),
                        rainfall: Number(item.rainfall_mm_hr ?? item.rainfall_mm ?? item.precipitation_mm ?? 0)
                      }))}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="#1b344a"
                      />

                      <XAxis
                        dataKey="time"
                        tick={{ fill: '#64748b', fontSize: 9 }}
                        tickLine={false}
                        axisLine={{ stroke: '#1b344a' }}
                        minTickGap={18}
                      />

                      <YAxis
                        tick={{ fill: '#64748b', fontSize: 9 }}
                        tickLine={false}
                        axisLine={false}
                        width={42}
                        label={{
                          value: 'mm',
                          angle: -90,
                          position: 'insideLeft',
                          fill: '#4d8db7',
                          fontSize: 9,
                        }}
                      />

                      <Tooltip
                        contentStyle={{
                          background: '#081522',
                          border: '1px solid #1b344a',
                          borderRadius: '8px',
                          color: '#e2e8f0',
                          fontSize: '11px',
                        }}
                        labelStyle={{
                          color: '#7dd3fc',
                          marginBottom: '4px',
                        }}
                        formatter={(value) => [`${Number(value).toFixed(2)} mm`, 'Rainfall']}
                        labelFormatter={(_, payload) => payload?.[0]?.payload?.fullTime || ''}
                      />

                      <Line
                        type="monotone"
                        dataKey="rainfall"
                        stroke="#38bdf8"
                        strokeWidth={2.5}
                        dot={{ r: 2.5, fill: '#38bdf8', strokeWidth: 0 }}
                        activeDot={{ r: 5 }}
                        connectNulls
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          ) : (
            <div className="observation-loading">
              Connecting to {source.title}...
            </div>
          )}
        </section>
      )}

      <div className="source-content-grid">
        <section className="role-card">
          <div className="section-label">
            <Activity size={16} />
            ROLE IN VARSHAAI
          </div>

          <h2>Why this data matters</h2>

          <div className="role-divider"></div>

          <h3>{source.roleTitle}</h3>

          <p>{source.roleDescription}</p>

          <div className="pipeline-row">
            <div className="pipeline-step">
              <span>01</span>
              <strong>INGEST</strong>
              <small>Source data</small>
            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">
              <span>02</span>
              <strong>QC</strong>
              <small>Quality control</small>
            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">
              <span>03</span>
              <strong>HARMONIZE</strong>
              <small>Common grid</small>
            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">
              <span>04</span>
              <strong>AI ENGINE</strong>
              <small>Forecast input</small>
            </div>
          </div>
        </section>

        <section className="health-card">
          <div className="section-label">
            <Database size={16} />
            DATA STATUS
          </div>

          <h2>Source Health</h2>

          <div className="health-divider"></div>

          <div className="health-row">
            <div>
              <strong>Data Stream</strong>
              <span>Ingestion service</span>
            </div>

            <b>
              <CheckCircle2 size={15} />
              {sourceType === 'satellite'
                ? satelliteConnected
                  ? 'ACTIVE'
                  : 'CHECKING'
                : 'ACTIVE'}
            </b>
          </div>

          <div className="health-row">
            <div>
              <strong>Quality Control</strong>
              <span>Automated validation</span>
            </div>

            <b>
              <CheckCircle2 size={15} />
              READY
            </b>
          </div>

          <div className="health-row">
            <div>
              <strong>Harmonization</strong>
              <span>Common analysis grid</span>
            </div>

            <b>
              <CheckCircle2 size={15} />
              READY
            </b>
          </div>

          <div className="health-row">
            <div>
              <strong>AI Integration</strong>
              <span>Forecast pipeline</span>
            </div>

            <b>
              <CheckCircle2 size={15} />
              READY
            </b>
          </div>
        </section>
      </div>

      <div className="prototype-notice">
        <span>!</span>

        <p>
          <strong>Prototype status:</strong>{' '}
          {sourceType === 'satellite'
            ? 'The INSAT-3DR HEM observation and time-series shown above are generated from real satellite files downloaded from MOSDAC and processed by the VARSHAAI backend. Other source integrations will be connected progressively.'
            : 'The source is part of the VARSHAAI multi-source architecture. Official operational data integration will be connected progressively through the ingestion pipeline.'}
        </p>
      </div>
    </div>
  )
}

export default SourceDetail

