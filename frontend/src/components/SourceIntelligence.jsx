import {
  ArrowLeft,
  Satellite,
  RadioTower,
  CloudRain,
  Gauge,
  Globe2,
  Activity,
  Map,
  Clock3,
  Database,
  CheckCircle2,
  Zap,
} from 'lucide-react'

import '../styles/SourceIntelligence.css'


function SourceIntelligence({ source, onBack }) {


  // =========================================================
  // DEFAULT SOURCE
  // =========================================================

  if (!source) {

    return (

      <div className="source-page">

        <button
          className="back-button"
          onClick={onBack}
          type="button"
        >

          <ArrowLeft size={18} />

          Back to Data Intelligence

        </button>

        <h1>
          Data Source
        </h1>

        <p>
          No data source selected.
        </p>

      </div>

    )

  }


  // =========================================================
  // SOURCE-SPECIFIC INFORMATION
  // =========================================================

  const sourceDetails = {

    satellite: {

      title: 'Satellite Intelligence',

      subtitle:
        'INSAT-3D / INSAT-3DR satellite rainfall and cloud intelligence',

      icon: Satellite,

      product: 'Cloud-top Brightness Temperature + QPE',

      resolution: '~4 km',

      interval: '30 minutes',

      quality: '98.2%',

      channel: 'MOSDAC / Satellite Feed',

      contribution:
        'Provides large-area cloud and precipitation information for short-term rainfall monitoring and nowcasting.',

      model:
        'VARSHAAI-NOW',

    },


    radar: {

      title: 'Radar Intelligence',

      subtitle:
        'Doppler Weather Radar reflectivity and rainfall estimation',

      icon: RadioTower,

      product: 'Reflectivity → Rainfall Rate',

      resolution: '~1 km',

      interval: '10 minutes',

      quality: '96.8%',

      channel: 'DWR Radar Feed',

      contribution:
        'Provides high-resolution precipitation structure and movement required for short-term rainfall nowcasting.',

      model:
        'VARSHAAI-NOW',

    },


    aws: {

      title: 'AWS Observations',

      subtitle:
        'Automatic Weather Station surface observations',

      icon: CloudRain,

      product: 'Rainfall + Weather Observations',

      resolution: 'Point observations',

      interval: '10 minutes',

      quality: '94.6%',

      channel: 'AWS Observation Network',

      contribution:
        'Provides ground-level observations for quality control, rainfall verification and local calibration.',

      model:
        'VARSHAAI-NOW + VARSHAAI-FCAST',

    },


    arg: {

      title: 'ARG Observations',

      subtitle:
        'Automatic Rain Gauge rainfall observations',

      icon: Gauge,

      product: 'Rain Gauge Measurements',

      resolution: 'Point observations',

      interval: '10 minutes',

      quality: '91.4%',

      channel: 'ARG Observation Network',

      contribution:
        'Provides localized rainfall measurements used to validate and correct gridded precipitation estimates.',

      model:
        'VARSHAAI-NOW + VARSHAAI-FCAST',

    },


    nwp: {

      title: 'NWP Model Intelligence',

      subtitle:
        'Numerical Weather Prediction model data and ML post-processing',

      icon: Globe2,

      product: 'WRF / GFS / IMD Forecast Fields',

      resolution: '~12 km',

      interval: '3–6 hours',

      quality: '95.1%',

      channel: 'NWP Forecast Feed',

      contribution:
        'Provides atmospheric dynamics and larger-scale weather evolution for extended rainfall prediction.',

      model:
        'VARSHAAI-FCAST',

    },

  }


  const details = sourceDetails[source.id] || sourceDetails.satellite

  const Icon = details.icon


  return (

    <div className="source-page">


      {/* =====================================================
          BACK BUTTON
          ===================================================== */}

      <button
        className="back-button"
        onClick={onBack}
        type="button"
      >

        <ArrowLeft size={18} />

        Back to Data Intelligence

      </button>


      {/* =====================================================
          PAGE HEADER
          ===================================================== */}

      <div className="source-page-header">

        <div className="source-title-area">

          <div className="source-main-icon">

            <Icon size={38} />

          </div>


          <div>

            <div className="source-breadcrumb">
              VARSHAAI / DATA INTELLIGENCE / {source.type}
            </div>

            <h1>
              {details.title}
            </h1>

            <p>
              {details.subtitle}
            </p>

          </div>

        </div>


        <div className="source-online">

          <span></span>

          SOURCE ENGINE ONLINE

        </div>

      </div>


      {/* =====================================================
          ACTIVE SOURCE
          ===================================================== */}

      <section className="active-source-panel">

        <div className="active-source-left">

          <div className="small-label">
            ACTIVE DATA SOURCE
          </div>

          <h2>
            {source.name}
          </h2>

          <p>
            Operational data stream for Chennai District
            rainfall intelligence.
          </p>

        </div>


        <div className="active-status">

          <CheckCircle2 size={21} />

          <div>

            <span>
              STATUS
            </span>

            <strong>
              {source.status}
            </strong>

          </div>

        </div>

      </section>


      {/* =====================================================
          METRICS
          ===================================================== */}

      <section className="source-metrics-grid">


        <div className="source-metric">

          <div className="metric-icon">
            <Activity size={22} />
          </div>

          <div>

            <span>
              PRIMARY PRODUCT
            </span>

            <strong>
              {details.product}
            </strong>

          </div>

        </div>


        <div className="source-metric">

          <div className="metric-icon">
            <Map size={22} />
          </div>

          <div>

            <span>
              SPATIAL RESOLUTION
            </span>

            <strong>
              {details.resolution}
            </strong>

          </div>

        </div>


        <div className="source-metric">

          <div className="metric-icon">
            <Clock3 size={22} />
          </div>

          <div>

            <span>
              TEMPORAL UPDATE
            </span>

            <strong>
              {details.interval}
            </strong>

          </div>

        </div>


        <div className="source-metric">

          <div className="metric-icon">
            <Zap size={22} />
          </div>

          <div>

            <span>
              DATA QUALITY
            </span>

            <strong>
              {details.quality}
            </strong>

          </div>

        </div>


      </section>


      {/* =====================================================
          MAIN INFORMATION
          ===================================================== */}

      <div className="source-content-grid">


        {/* Observation panel */}

        <section className="source-observation-panel">

          <div className="panel-header">

            <div>

              <div className="small-label">
                SOURCE OBSERVATION
              </div>

              <h2>
                {details.title}
              </h2>

            </div>

          </div>


          <div className="source-visual">

            <div className="visual-grid"></div>

            <div className="visual-center">

              <div className="pulse-circle">

                <Icon size={30} />

              </div>

              <strong>
                CHENNAI
              </strong>

              <span>
                LIVE DATA REGION
              </span>

            </div>


            <div className="visual-status">

              <span></span>

              DATA STREAM ACTIVE

            </div>

          </div>

        </section>


        {/* Profile */}

        <section className="source-profile">

          <div className="small-label">
            SOURCE PROFILE
          </div>

          <h2>
            Data Characteristics
          </h2>


          <div className="profile-row">

            <Database size={19} />

            <div>

              <span>
                DATA CHANNEL
              </span>

              <strong>
                {details.channel}
              </strong>

            </div>

          </div>


          <div className="profile-row">

            <Map size={19} />

            <div>

              <span>
                SPATIAL SCALE
              </span>

              <strong>
                {details.resolution}
              </strong>

            </div>

          </div>


          <div className="profile-row">

            <Clock3 size={19} />

            <div>

              <span>
                UPDATE FREQUENCY
              </span>

              <strong>
                {details.interval}
              </strong>

            </div>

          </div>


          <div className="profile-row">

            <Activity size={19} />

            <div>

              <span>
                DATA QUALITY
              </span>

              <strong className="good">
                GOOD
              </strong>

            </div>

          </div>

        </section>


      </div>


      {/* =====================================================
          AI CONTRIBUTION
          ===================================================== */}

      <section className="ai-contribution">

        <div className="ai-contribution-icon">

          <Zap size={26} />

        </div>


        <div className="ai-contribution-text">

          <div className="small-label">
            AI CONTRIBUTION
          </div>

          <h2>
            Role in VARSHAAI prediction
          </h2>

          <p>
            {details.contribution}
          </p>

        </div>


        <div className="ai-model-badge">

          <strong>
            {details.model}
          </strong>

          <span>
            CHENNAI PREDICTION
          </span>

        </div>

      </section>


    </div>

  )

}


export default SourceIntelligence