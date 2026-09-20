import {
  BarChart3,
  CheckCircle2,
  Database,
  Download,
  Gauge,
  MapPin,
  RefreshCw,
  Target,
  TrendingUp,
} from 'lucide-react'

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import '../styles/Validation.css'


// ============================================================
// DEMO VALIDATION DATA
// ============================================================

const rainfallData = [
  {
    time: '00:00',
    observed: 8,
    nowcast: 10,
    nwp: 7,
    blended: 9,
  },
  {
    time: '03:00',
    observed: 22,
    nowcast: 20,
    nwp: 18,
    blended: 21,
  },
  {
    time: '06:00',
    observed: 46,
    nowcast: 43,
    nwp: 39,
    blended: 45,
  },
  {
    time: '09:00',
    observed: 72,
    nowcast: 69,
    nwp: 61,
    blended: 70,
  },
  {
    time: '12:00',
    observed: 96,
    nowcast: 91,
    nwp: 84,
    blended: 94,
  },
  {
    time: '15:00',
    observed: 82,
    nowcast: 79,
    nwp: 76,
    blended: 81,
  },
  {
    time: '18:00',
    observed: 61,
    nowcast: 64,
    nwp: 57,
    blended: 62,
  },
  {
    time: '21:00',
    observed: 34,
    nowcast: 31,
    nwp: 29,
    blended: 33,
  },
]


const modelComparison = [
  {
    model: 'VARSHAAI-NOW',
    pod: 0.93,
    far: 0.10,
    csi: 0.85,
  },
  {
    model: 'NWP',
    pod: 0.79,
    far: 0.18,
    csi: 0.68,
  },
  {
    model: 'BLENDED',
    pod: 0.95,
    far: 0.08,
    csi: 0.89,
  },
]


// ============================================================
// COMPONENT
// ============================================================

function Validation() {

  // ----------------------------------------------------------
  // EXPORT DEMO REPORT
  // ----------------------------------------------------------

  const handleExport = () => {

    const report = `
VARSHAAI MODEL VALIDATION REPORT
================================

Event:
Chennai Heavy Rainfall Event

Period:
06 December 2023 - 07 December 2023

Location:
Chennai District, Tamil Nadu

--------------------------------
VALIDATION METRICS
--------------------------------

Probability of Detection (POD): 0.93
False Alarm Ratio (FAR):        0.10
Critical Success Index (CSI):   0.85

Mean Absolute Error (MAE):      5.1 mm
Root Mean Square Error (RMSE):  6.9 mm

--------------------------------
CONFUSION MATRIX
--------------------------------

True Positive:  42
False Positive: 6
False Negative: 4
True Negative:  48

--------------------------------
MODEL ARCHITECTURE
--------------------------------

VARSHAAI-NOW:
ConvLSTM
Radar + Satellite
Lead time: 0-3 hours

VARSHAAI-FCAST:
NWP + ML Bias Correction
Lead time: 3-72 hours

--------------------------------
NOTE
--------------------------------

This dashboard currently displays
prototype validation values.
Final deployment requires operational
IMD event datasets and continuous
backtesting.
`

    const blob = new Blob(
      [report],
      { type: 'text/plain' }
    )

    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')

    link.href = url

    link.download = 'VARSHAAI_Validation_Report.txt'

    document.body.appendChild(link)

    link.click()

    document.body.removeChild(link)

    URL.revokeObjectURL(url)
  }


  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (

    <div className="validation-page">

      {/* ======================================================
          PAGE HEADER
          ====================================================== */}

      <div className="validation-header">

        <div>

          <div className="validation-breadcrumb">
            VARSHAAI / MODEL VALIDATION
          </div>

          <h1>
            Validation & Skill Scores
          </h1>

          <p>
            Historical event backtesting and
            meteorological model verification
          </p>

        </div>


        <div className="validation-header-actions">

          <div className="validation-status">

            <span className="validation-status-dot"></span>

            VALIDATION READY

          </div>


          <button
            className="export-button"
            onClick={handleExport}
          >

            <Download size={16} />

            Export Report

          </button>

        </div>

      </div>


      {/* ======================================================
          EVENT INFORMATION
          ====================================================== */}

      <div className="event-card">

        <div className="event-icon">

          <MapPin size={22} />

        </div>


        <div className="event-information">

          <div className="event-label">
            BACKTEST EVENT
          </div>

          <h2>
            Chennai Heavy Rainfall Event
          </h2>

          <p>
            06 December 2023 – 07 December 2023
            &nbsp; • &nbsp;
            Chennai District, Tamil Nadu
          </p>

        </div>


        <div className="event-meta">

          <div>
            <span>Duration</span>
            <strong>24 Hours</strong>
          </div>

          <div>
            <span>Resolution</span>
            <strong>1 km / 10 min</strong>
          </div>

          <div>
            <span>Status</span>
            <strong className="success-text">
              <CheckCircle2 size={15} />
              Complete
            </strong>
          </div>

        </div>

      </div>


      {/* ======================================================
          KPI METRICS
          ====================================================== */}

      <div className="validation-section-title">

        <div>

          <span>01</span>

          <div>
            <h2>Verification Metrics</h2>
            <p>Rainfall event detection performance</p>
          </div>

        </div>

      </div>


      <div className="metric-grid">

        <div className="metric-card">

          <div className="metric-card-top">

            <div className="metric-icon">
              <Target size={19} />
            </div>

            <span className="metric-label">
              POD
            </span>

          </div>

          <div className="metric-value">
            0.93
          </div>

          <div className="metric-description">
            Probability of Detection
          </div>

          <div className="metric-progress">
            <div style={{ width: '93%' }}></div>
          </div>

        </div>


        <div className="metric-card">

          <div className="metric-card-top">

            <div className="metric-icon">
              <Gauge size={19} />
            </div>

            <span className="metric-label">
              FAR
            </span>

          </div>

          <div className="metric-value">
            0.10
          </div>

          <div className="metric-description">
            False Alarm Ratio
          </div>

          <div className="metric-progress">
            <div style={{ width: '90%' }}></div>
          </div>

        </div>


        <div className="metric-card">

          <div className="metric-card-top">

            <div className="metric-icon">
              <TrendingUp size={19} />
            </div>

            <span className="metric-label">
              CSI
            </span>

          </div>

          <div className="metric-value">
            0.85
          </div>

          <div className="metric-description">
            Critical Success Index
          </div>

          <div className="metric-progress">
            <div style={{ width: '85%' }}></div>
          </div>

        </div>


        <div className="metric-card">

          <div className="metric-card-top">

            <div className="metric-icon">
              <BarChart3 size={19} />
            </div>

            <span className="metric-label">
              MAE
            </span>

          </div>

          <div className="metric-value">
            5.1
            <small> mm</small>
          </div>

          <div className="metric-description">
            Mean Absolute Error
          </div>

          <div className="metric-quality">
            GOOD PERFORMANCE
          </div>

        </div>


        <div className="metric-card">

          <div className="metric-card-top">

            <div className="metric-icon">
              <RefreshCw size={19} />
            </div>

            <span className="metric-label">
              RMSE
            </span>

          </div>

          <div className="metric-value">
            6.9
            <small> mm</small>
          </div>

          <div className="metric-description">
            Root Mean Square Error
          </div>

          <div className="metric-quality">
            ACCEPTABLE
          </div>

        </div>

      </div>


      {/* ======================================================
          CHART + CONFUSION MATRIX
          ====================================================== */}

      <div className="validation-two-column">

        {/* ----------------------------------------------------
            RAINFALL COMPARISON
            ---------------------------------------------------- */}

        <div className="validation-panel chart-panel">

          <div className="panel-header">

            <div>

              <div className="panel-kicker">
                TIME SERIES
              </div>

              <h2>
                Observed vs Predicted Rainfall
              </h2>

              <p>
                Chennai district event backtest
              </p>

            </div>

          </div>


          <div className="chart-container">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <LineChart
                data={rainfallData}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 0,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11 }}
                />

                <YAxis
                  tick={{ fontSize: 11 }}
                  unit=" mm"
                />

                <Tooltip />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="observed"
                  name="Observed"
                  strokeWidth={3}
                  dot={false}
                />

                <Line
                  type="monotone"
                  dataKey="nowcast"
                  name="VARSHAAI-NOW"
                  strokeWidth={2}
                  dot={false}
                />

                <Line
                  type="monotone"
                  dataKey="nwp"
                  name="NWP"
                  strokeWidth={2}
                  dot={false}
                />

                <Line
                  type="monotone"
                  dataKey="blended"
                  name="Blended"
                  strokeWidth={3}
                  dot={false}
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        </div>


        {/* ----------------------------------------------------
            CONFUSION MATRIX
            ---------------------------------------------------- */}

        <div className="validation-panel confusion-panel">

          <div className="panel-header">

            <div>

              <div className="panel-kicker">
                EVENT DETECTION
              </div>

              <h2>
                Confusion Matrix
              </h2>

              <p>
                Rainfall threshold: ≥ 35 mm/hr
              </p>

            </div>

          </div>


          <div className="matrix">

            <div className="matrix-corner"></div>

            <div className="matrix-axis">
              OBSERVED RAIN
            </div>

            <div className="matrix-axis">
              OBSERVED NO RAIN
            </div>


            <div className="matrix-row-label">
              FORECAST RAIN
            </div>

            <div className="matrix-cell matrix-tp">

              <strong>42</strong>

              <span>
                True Positive
              </span>

            </div>

            <div className="matrix-cell matrix-fp">

              <strong>6</strong>

              <span>
                False Positive
              </span>

            </div>


            <div className="matrix-row-label">
              FORECAST NO RAIN
            </div>

            <div className="matrix-cell matrix-fn">

              <strong>4</strong>

              <span>
                False Negative
              </span>

            </div>

            <div className="matrix-cell matrix-tn">

              <strong>48</strong>

              <span>
                True Negative
              </span>

            </div>

          </div>


          <div className="matrix-total">

            <Database size={15} />

            <span>
              Total samples
            </span>

            <strong>
              100
            </strong>

          </div>

        </div>

      </div>


      {/* ======================================================
          MODEL COMPARISON
          ====================================================== */}

      <div className="validation-panel model-panel">

        <div className="panel-header">

          <div>

            <div className="panel-kicker">
              MODEL PERFORMANCE
            </div>

            <h2>
              Model Comparison
            </h2>

            <p>
              Skill comparison across rainfall detection models
            </p>

          </div>

        </div>


        <div className="model-content">

          <div className="model-chart">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart
                data={modelComparison}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 0,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="model"
                  tick={{ fontSize: 11 }}
                />

                <YAxis
                  domain={[0, 1]}
                  tick={{ fontSize: 11 }}
                />

                <Tooltip />

                <Legend />

                <Bar
                  dataKey="pod"
                  name="POD"
                />

                <Bar
                  dataKey="csi"
                  name="CSI"
                />

              </BarChart>

            </ResponsiveContainer>

          </div>


          <div className="model-table">

            <div className="table-row table-header">

              <span>MODEL</span>
              <span>POD</span>
              <span>FAR</span>
              <span>CSI</span>

            </div>


            {modelComparison.map((model) => (

              <div
                className="table-row"
                key={model.model}
              >

                <strong>
                  {model.model}
                </strong>

                <span>
                  {model.pod.toFixed(2)}
                </span>

                <span>
                  {model.far.toFixed(2)}
                </span>

                <span className="highlight-score">
                  {model.csi.toFixed(2)}
                </span>

              </div>

            ))}

          </div>

        </div>

      </div>


      {/* ======================================================
          TWO MODEL ARCHITECTURE
          ====================================================== */}

      <div className="validation-panel architecture-panel">

        <div className="panel-header">

          <div>

            <div className="panel-kicker">
              VARSHAAI ARCHITECTURE
            </div>

            <h2>
              Two-Model Forecast Strategy
            </h2>

            <p>
              Different atmospheric lead times require
              different modelling approaches
            </p>

          </div>

        </div>


        <div className="architecture-grid">

          {/* NOWCAST */}

          <div className="architecture-card">

            <div className="architecture-number">
              01
            </div>

            <div className="architecture-icon">
              <RefreshCw size={24} />
            </div>

            <div className="architecture-title">
              VARSHAAI-NOW
            </div>

            <div className="architecture-model">
              ConvLSTM
            </div>

            <div className="architecture-range">
              0 – 3 HOURS
            </div>

            <div className="architecture-description">

              Uses rapidly updating

              <strong>
                radar reflectivity + satellite cloud data
              </strong>

              to predict short-term rainfall movement
              and intensity.

            </div>

          </div>


          <div className="architecture-arrow">
            →
          </div>


          {/* FCAST */}

          <div className="architecture-card">

            <div className="architecture-number">
              02
            </div>

            <div className="architecture-icon">
              <TrendingUp size={24} />
            </div>

            <div className="architecture-title">
              VARSHAAI-FCAST
            </div>

            <div className="architecture-model">
              NWP + ML Bias Correction
            </div>

            <div className="architecture-range">
              3 – 72 HOURS
            </div>

            <div className="architecture-description">

              Uses

              <strong>
                NWP forecasts + historical observations
              </strong>

              to correct systematic bias and improve
              rainfall prediction.

            </div>

          </div>


          <div className="architecture-arrow">
            →
          </div>


          {/* OUTPUT */}

          <div className="architecture-card output-card">

            <div className="architecture-number">
              03
            </div>

            <div className="architecture-icon">
              <Target size={24} />
            </div>

            <div className="architecture-title">
              FINAL RISK
            </div>

            <div className="architecture-model">
              Probabilistic Forecast
            </div>

            <div className="architecture-range">
              DISTRICT / BLOCK
            </div>

            <div className="architecture-description">

              Combines forecast confidence,
              rainfall intensity and hydrological
              conditions to generate

              <strong>
                actionable flood risk.
              </strong>

            </div>

          </div>

        </div>

      </div>


      {/* ======================================================
          VALIDATION PIPELINE
          ====================================================== */}

      <div className="validation-pipeline">

        <div className="pipeline-step">

          <span>01</span>

          <strong>
            OBSERVATIONS
          </strong>

          <small>
            AWS + ARG + Radar
          </small>

        </div>


        <div className="pipeline-line"></div>


        <div className="pipeline-step">

          <span>02</span>

          <strong>
            FORECAST
          </strong>

          <small>
            Satellite + NWP + ML
          </small>

        </div>


        <div className="pipeline-line"></div>


        <div className="pipeline-step">

          <span>03</span>

          <strong>
            VERIFICATION
          </strong>

          <small>
            POD / FAR / CSI
          </small>

        </div>


        <div className="pipeline-line"></div>


        <div className="pipeline-step">

          <span>04</span>

          <strong>
            DECISION
          </strong>

          <small>
            Flood Risk Alert
          </small>

        </div>

      </div>


      {/* ======================================================
          PROTOTYPE NOTICE
          ====================================================== */}

      <div className="prototype-notice">

        <div className="prototype-icon">
          !
        </div>

        <div>

          <strong>
            Prototype Validation Dataset
          </strong>

          <p>
            The values displayed in this demonstration are
            representative prototype results. Final SIH deployment
            will use operational IMD observations, radar,
            satellite and NWP datasets for continuous event
            backtesting.
          </p>

        </div>

      </div>

    </div>

  )
}


export default Validation