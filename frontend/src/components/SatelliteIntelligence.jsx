import {
  Satellite,
  CloudRain,
  Thermometer,
  Radio,
  Clock3,
  Database,
  Activity,
  Map,
  RefreshCw,
  CheckCircle2,
  ArrowDown,
} from 'lucide-react'

import '../styles/SatelliteIntelligence.css'


function SatelliteIntelligence() {

  return (

    <div className="satellite-page">

      {/* =====================================================
          PAGE HEADER
          ===================================================== */}

      <div className="satellite-page-header">

        <div>

          <div className="satellite-breadcrumb">
            VARSHAAI / DATA INTELLIGENCE / SATELLITE
          </div>

          <div className="satellite-title-row">

            <div className="satellite-title-icon">
              <Satellite size={30} />
            </div>

            <div>

              <h1>
                Satellite Intelligence
              </h1>

              <p>
                INSAT-3D / 3DR satellite rainfall and cloud intelligence
              </p>

            </div>

          </div>

        </div>


        <div className="satellite-live-status">

          <span className="satellite-status-dot"></span>

          SATELLITE ENGINE ONLINE

        </div>

      </div>


      {/* =====================================================
          SOURCE IDENTITY
          ===================================================== */}

      <section className="satellite-source-banner">

        <div className="satellite-source-main">

          <div className="satellite-large-icon">
            <Satellite size={34} />
          </div>

          <div>

            <div className="satellite-overline">
              ACTIVE DATA SOURCE
            </div>

            <h2>
              INSAT-3D / INSAT-3DR
            </h2>

            <p>
              Geostationary meteorological satellite observations
              supporting rainfall monitoring and early warning.
            </p>

          </div>

        </div>


        <div className="satellite-source-status">

          <CheckCircle2 size={18} />

          <div>
            <span>STATUS</span>
            <strong>ACTIVE</strong>
          </div>

        </div>

      </section>


      {/* =====================================================
          KPI CARDS
          ===================================================== */}

      <section className="satellite-kpi-grid">


        <div className="satellite-kpi-card">

          <div className="satellite-kpi-icon">
            <CloudRain size={22} />
          </div>

          <div className="satellite-kpi-content">

            <span className="satellite-kpi-label">
              SATELLITE QPE
            </span>

            <strong>
              42.6 mm/hr
            </strong>

            <small>
              Estimated rainfall intensity
            </small>

          </div>

        </div>


        <div className="satellite-kpi-card">

          <div className="satellite-kpi-icon">
            <Thermometer size={22} />
          </div>

          <div className="satellite-kpi-content">

            <span className="satellite-kpi-label">
              CLOUD-TOP BT
            </span>

            <strong>
              218 K
            </strong>

            <small>
              Brightness temperature
            </small>

          </div>

        </div>


        <div className="satellite-kpi-card">

          <div className="satellite-kpi-icon">
            <Map size={22} />
          </div>

          <div className="satellite-kpi-content">

            <span className="satellite-kpi-label">
              SPATIAL RESOLUTION
            </span>

            <strong>
              ~4 km
            </strong>

            <small>
              Satellite grid resolution
            </small>

          </div>

        </div>


        <div className="satellite-kpi-card">

          <div className="satellite-kpi-icon">
            <Clock3 size={22} />
          </div>

          <div className="satellite-kpi-content">

            <span className="satellite-kpi-label">
              TEMPORAL UPDATE
            </span>

            <strong>
              30 min
            </strong>

            <small>
              Observation interval
            </small>

          </div>

        </div>

      </section>


      {/* =====================================================
          MAIN CONTENT GRID
          ===================================================== */}

      <div className="satellite-main-grid">


        {/* ===================================================
            SATELLITE MAP
            =================================================== */}

        <section className="satellite-panel satellite-map-panel">

          <div className="satellite-panel-header">

            <div>

              <span className="satellite-section-label">
                SATELLITE OBSERVATION
              </span>

              <h2>
                Cloud & Rainfall Intelligence
              </h2>

            </div>

            <button className="satellite-refresh-button">
              <RefreshCw size={15} />
              Refresh
            </button>

          </div>


          <div className="satellite-map">

            <div className="satellite-map-grid"></div>

            <div className="satellite-cloud cloud-one"></div>
            <div className="satellite-cloud cloud-two"></div>
            <div className="satellite-cloud cloud-three"></div>

            <div className="rain-cell rain-cell-one"></div>
            <div className="rain-cell rain-cell-two"></div>
            <div className="rain-cell rain-cell-three"></div>

            <div className="satellite-location-marker">

              <div className="marker-pulse"></div>

              <div className="marker-point"></div>

              <span>
                THOOTHUKUDI
              </span>

            </div>


            <div className="satellite-map-overlay">

              <div className="overlay-title">
                INSAT-3DR QPE
              </div>

              <div className="overlay-time">
                Latest observation • 10:00 IST
              </div>

            </div>


            <div className="satellite-map-legend">

              <div className="legend-title">
                RAINFALL INTENSITY
              </div>

              <div className="legend-scale">

                <span>Low</span>

                <div className="legend-gradient"></div>

                <span>High</span>

              </div>

            </div>

          </div>

        </section>


        {/* ===================================================
            SOURCE DETAILS
            =================================================== */}

        <section className="satellite-panel satellite-details-panel">

          <div className="satellite-panel-header">

            <div>

              <span className="satellite-section-label">
                SOURCE PROFILE
              </span>

              <h2>
                Data Characteristics
              </h2>

            </div>

          </div>


          <div className="satellite-detail-list">


            <div className="satellite-detail-row">

              <div className="detail-icon">
                <Satellite size={17} />
              </div>

              <div>
                <span>Platform</span>
                <strong>INSAT-3D / 3DR</strong>
              </div>

            </div>


            <div className="satellite-detail-row">

              <div className="detail-icon">
                <CloudRain size={17} />
              </div>

              <div>
                <span>Primary Products</span>
                <strong>Cloud-top BT + QPE</strong>
              </div>

            </div>


            <div className="satellite-detail-row">

              <div className="detail-icon">
                <Map size={17} />
              </div>

              <div>
                <span>Spatial Resolution</span>
                <strong>~4 km</strong>
              </div>

            </div>


            <div className="satellite-detail-row">

              <div className="detail-icon">
                <Clock3 size={17} />
              </div>

              <div>
                <span>Temporal Resolution</span>
                <strong>30 minutes</strong>
              </div>

            </div>


            <div className="satellite-detail-row">

              <div className="detail-icon">
                <Radio size={17} />
              </div>

              <div>
                <span>Data Channel</span>
                <strong>MOSDAC / Satellite Feed</strong>
              </div>

            </div>


            <div className="satellite-detail-row">

              <div className="detail-icon">
                <Activity size={17} />
              </div>

              <div>
                <span>Data Quality</span>
                <strong className="quality-good">
                  GOOD
                </strong>
              </div>

            </div>

          </div>

        </section>

      </div>


      {/* =====================================================
          PROCESSING PIPELINE
          ===================================================== */}

      <section className="satellite-panel satellite-pipeline-panel">

        <div className="satellite-panel-header">

          <div>

            <span className="satellite-section-label">
              PROCESSING PIPELINE
            </span>

            <h2>
              Satellite Data → AI Ready Dataset
            </h2>

          </div>

        </div>


        <div className="satellite-pipeline">


          <div className="pipeline-stage">

            <div className="pipeline-stage-icon">
              <Satellite size={21} />
            </div>

            <div>
              <strong>
                INSAT-3D / 3DR
              </strong>

              <span>
                Raw satellite observations
              </span>
            </div>

          </div>


          <ArrowDown className="pipeline-arrow" size={20} />


          <div className="pipeline-stage">

            <div className="pipeline-stage-icon">
              <Database size={21} />
            </div>

            <div>
              <strong>
                Quality Control
              </strong>

              <span>
                Missing / invalid data filtering
              </span>
            </div>

          </div>


          <ArrowDown className="pipeline-arrow" size={20} />


          <div className="pipeline-stage">

            <div className="pipeline-stage-icon">
              <Map size={21} />
            </div>

            <div>
              <strong>
                Regridding
              </strong>

              <span>
                ~4 km → common 1 km grid
              </span>
            </div>

          </div>


          <ArrowDown className="pipeline-arrow" size={20} />


          <div className="pipeline-stage">

            <div className="pipeline-stage-icon">
              <Clock3 size={21} />
            </div>

            <div>
              <strong>
                Temporal Alignment
              </strong>

              <span>
                30 min → common 10 min axis
              </span>
            </div>

          </div>


          <ArrowDown className="pipeline-arrow" size={20} />


          <div className="pipeline-stage pipeline-stage-final">

            <div className="pipeline-stage-icon">
              <Activity size={21} />
            </div>

            <div>
              <strong>
                AI ENGINE
              </strong>

              <span>
                VARSHAAI-NOW input
              </span>
            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          AI CONTRIBUTION
          ===================================================== */}

      <section className="satellite-ai-banner">

        <div className="satellite-ai-icon">
          <Activity size={26} />
        </div>

        <div className="satellite-ai-content">

          <span>
            AI CONTRIBUTION
          </span>

          <h2>
            Satellite observations strengthen short-term
            rainfall nowcasting
          </h2>

          <p>
            Cloud-top brightness temperature and satellite
            precipitation estimates are harmonized with DWR
            radar and surface observations before entering
            the VARSHAAI-NOW ConvLSTM nowcasting engine.
          </p>

        </div>


        <div className="satellite-ai-model">

          <strong>
            VARSHAAI-NOW
          </strong>

          <span>
            0–3 HR NOWCAST
          </span>

        </div>

      </section>

    </div>

  )
}


export default SatelliteIntelligence