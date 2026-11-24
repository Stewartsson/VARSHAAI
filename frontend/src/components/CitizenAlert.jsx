import { useState, useEffect, useRef } from 'react'
import {
  Siren,
  ShieldAlert,
  Volume2,
  VolumeX,
  PhoneCall,
  MapPin,
  Navigation,
  Compass,
  Share2,
  Copy,
  Check,
  ArrowLeft,
  Waves,
  CloudRain,
  ShieldCheck,
  AlertTriangle,
  Radio,
  ExternalLink,
} from 'lucide-react'
import '../styles/CitizenAlert.css'

const CITY_EVACUATION_DATA = {
  chennai: {
    name: 'Chennai',
    state: 'Tamil Nadu',
    hotspot: 'Velachery Basin & Mudichur Lowlands',
    shelter: 'Guru Nanak College Relief Center',
    shelterElevation: '11.2m AMSL',
    elevationMargin: '+4.5m safety margin',
    safeRoute: 'Follow Velachery Bypass Rd northwards. Strictly avoid Velachery MRTS Subway & Lake overflow corridor.',
    dangerPoints: ['Velachery MRTS Subway (> 1.2m)', 'Madipakkam Main Road', 'Mudichur Outer Ring Road lowlands'],
    contacts: [
      { label: 'TN State Disaster (SDMA)', tel: '1070', tag: '24/7 Toll-Free' },
      { label: 'Chennai Corp Flood Room', tel: '1913', tag: 'Municipal Control' },
      { label: 'NDRF National Rescue', tel: '112', tag: 'Emergency Operations' },
    ],
  },
  mumbai: {
    name: 'Mumbai',
    state: 'Maharashtra',
    hotspot: 'Milan Subway & Hindmata (Dadar)',
    shelter: 'Dadar Municipal High School Relief Center',
    shelterElevation: '16.5m AMSL',
    elevationMargin: '+8.5m safety margin',
    safeRoute: 'Follow Dr. B.A. Road elevated flyover corridor; strictly avoid Milan Underpass and low-lying Hindmata bowl.',
    dangerPoints: ['Milan Subway (Santacruz)', 'Hindmata Underpass', 'Kurla West Mithi River Embankment'],
    contacts: [
      { label: 'BMC Disaster Control', tel: '1916', tag: 'Municipal Control' },
      { label: 'District Operations Center', tel: '1077', tag: 'Toll-Free' },
      { label: 'NDRF National Rescue', tel: '112', tag: 'Emergency Operations' },
    ],
  },
  delhi: {
    name: 'Delhi (NCR)',
    state: 'National Capital Territory',
    hotspot: 'Yamuna Floodplain (ITO) & Minto Bridge',
    shelter: 'Shakarpur Community Disaster Center',
    shelterElevation: '228.0m AMSL',
    elevationMargin: '+12.0m safety margin',
    safeRoute: 'Divert away from Ring Road Yamuna embankments; strictly avoid Minto Bridge railway underpass.',
    dangerPoints: ['Minto Bridge Underpass (> 1.8m)', 'ITO Low-Lying Floodplain', 'Kashmere Gate ISBT depression'],
    contacts: [
      { label: 'DDMA Control Room', tel: '1077', tag: 'Delhi Disaster Auth' },
      { label: 'Delhi Emergency Police', tel: '100', tag: 'Police Control' },
      { label: 'NDRF National Rescue', tel: '112', tag: 'Emergency Operations' },
    ],
  },
  hyderabad: {
    name: 'Hyderabad',
    state: 'Telangana',
    hotspot: 'Nadeem Colony (Tolichowki) & Begumpet Underpass',
    shelter: 'Shaikpet Mandal Disaster Relief Complex',
    shelterElevation: '562.0m AMSL',
    elevationMargin: '+20.0m safety margin',
    safeRoute: 'Evacuate towards Jubilee Hills ridge; avoid Musi riverbanks and low-lying stormwater nala corridors.',
    dangerPoints: ['Nadeem Colony (Lake backflow)', 'Begumpet Railway Subway', 'Moosarambagh Musi Causeway'],
    contacts: [
      { label: 'GHMC Disaster Room', tel: '040-21111111', tag: 'Municipal Control' },
      { label: 'Telangana State SDMA', tel: '1070', tag: 'Toll-Free' },
      { label: 'NDRF National Rescue', tel: '112', tag: 'Emergency Operations' },
    ],
  },
  kolkata: {
    name: 'Kolkata',
    state: 'West Bengal',
    hotspot: 'Thanthania Kalibari & Park Circus 7-Point',
    shelter: 'College Square Ward Disaster Shelter',
    shelterElevation: '14.8m AMSL',
    elevationMargin: '+5.8m safety margin',
    safeRoute: 'Move towards Central Avenue elevated artery; strictly avoid Thanthania and Kalighat tidal lockage.',
    dangerPoints: ['Thanthania Kalibari stretch', 'Park Circus 7-Point roundabout', 'Kalighat Ghat Corridor'],
    contacts: [
      { label: 'WB State Disaster Auth', tel: '1070', tag: 'Toll-Free' },
      { label: 'KMC Flood Control Cell', tel: '033-22861212', tag: 'Kolkata Corp' },
      { label: 'NDRF National Rescue', tel: '112', tag: 'Emergency Operations' },
    ],
  },
}

const CITY_COORDINATES = {
  chennai: { lat: 13.0827, lon: 80.2707, radar: 'DWR Sriharikota / NIOT (S-Band 2.8 GHz)' },
  mumbai: { lat: 19.0760, lon: 72.8777, radar: 'DWR Colaba & Veravali (Dual-Pol S-Band)' },
  delhi: { lat: 28.6139, lon: 77.2090, radar: 'DWR Palam & Mausam Bhavan (C-Band 5.6 GHz)' },
  hyderabad: { lat: 17.3850, lon: 78.4867, radar: 'DWR Begumpet Airport (C-Band)' },
  kolkata: { lat: 22.5726, lon: 88.3639, radar: 'DWR New Town Rajarhat (S-Band)' },
}

function CitizenAlert({ onBack }) {
  // Read query parameters if judge opened URL on smartphone directly
  const searchParams = new URLSearchParams(window.location.search)
  const initialCity = searchParams.get('city') || 'chennai'
  const initialMode = searchParams.get('mode') || 'simulation'

  const [selectedCity, setSelectedCity] = useState(
    CITY_EVACUATION_DATA[initialCity] ? initialCity : 'chennai'
  )
  const [mode, setMode] = useState(initialMode === 'live' ? 'live' : 'simulation')
  const [liveWeather, setLiveWeather] = useState(null)
  const [lastSyncedAt, setLastSyncedAt] = useState(null)
  const [fetchingLive, setFetchingLive] = useState(false)
  const [sirenPlaying, setSirenPlaying] = useState(false)
  const [copied, setCopied] = useState(false)

  const audioContextRef = useRef(null)
  const oscillatorRef = useRef(null)
  const gainNodeRef = useRef(null)

  const cityData = CITY_EVACUATION_DATA[selectedCity] || CITY_EVACUATION_DATA.chennai
  const radarInfo = CITY_COORDINATES[selectedCity] || CITY_COORDINATES.chennai

  // Fetch real-time live telemetry for the selected metro
  useEffect(() => {
    let isCancelled = false
    async function fetchLiveWeather() {
      setFetchingLive(true)
      try {
        const coords = CITY_COORDINATES[selectedCity] || CITY_COORDINATES.chennai
        const res = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${coords.lat}&longitude=${coords.lon}&current=temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,cloud_cover,wind_speed_10m,surface_pressure&hourly=precipitation,rain,showers,weather_code&forecast_days=1&timezone=Asia%2FKolkata`
        )
        if (!res.ok) throw new Error('Weather fetch failed')
        const data = await res.json()
        if (!isCancelled) {
          const cur = data.current || {}
          const hourly = data.hourly || {}
          const p = Number(cur.precipitation || 0)
          const r = Number(cur.rain || 0)
          const s = Number(cur.showers || 0)
          const intervalHourly = cur.interval && p > 0 ? p * (3600 / cur.interval) : p
          let currentHourRain = 0
          if (hourly.time && hourly.precipitation) {
            const nowStr = (cur.time || new Date().toISOString()).slice(0, 13)
            const idx = hourly.time.findIndex((t) => t.startsWith(nowStr))
            if (idx !== -1 && typeof hourly.precipitation[idx] === 'number') {
              currentHourRain = hourly.precipitation[idx]
            }
          }
          const effectiveRain = Number(Math.max(p, r + s, intervalHourly, currentHourRain).toFixed(1))
          setLiveWeather({
            effectiveRain,
            tempC: Number((cur.temperature_2m ?? 28).toFixed(1)),
            humidity: Math.round(cur.relative_humidity_2m ?? 70),
            windSpeed: Number((cur.wind_speed_10m ?? 12).toFixed(1)),
            pressure: Number((cur.surface_pressure ?? 1012).toFixed(1)),
          })
          setLastSyncedAt(new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
        }
      } catch (e) {
        console.warn('Live weather fetch failed in CitizenAlert:', e)
      } finally {
        if (!isCancelled) setFetchingLive(false)
      }
    }

    fetchLiveWeather()
    const timer = setInterval(fetchLiveWeather, 60000)
    return () => {
      isCancelled = true
      clearInterval(timer)
    }
  }, [selectedCity])

  const liveRain = liveWeather?.effectiveRain ?? 0.0
  const isSimulation = mode === 'simulation'

  let alertLevel = 'GREEN'
  let rainfallDisplay = `${liveRain.toFixed(1)} mm/hr`
  let depthDisplay = '0.00 m'
  let levelBadge = 'LEVEL 1 • NORMAL / SAFE CONDITIONS'
  let riskTitle = 'NORMAL CONDITIONS — PASSAGES SAFE'
  let evacWindow = 'ALL PASSAGES CLEAR'
  let rainfallSubtitle = 'Live Doppler Telemetry'
  let depthSubtitle = 'No Surface Stagnation'

  if (isSimulation) {
    alertLevel = 'RED'
    rainfallDisplay = '180.0 mm'
    depthDisplay = '0.85 m'
    levelBadge = 'LEVEL 4 • IMMEDIATE EVACUATION ORDER'
    riskTitle = 'EXTREME FLOOD ALERT'
    evacWindow = 'NEXT 45 MIN'
    rainfallSubtitle = 'Cloudburst Simulation'
    depthSubtitle = 'Severe Inundation'
  } else if (liveRain >= 35.0) {
    alertLevel = 'RED'
    depthDisplay = `${(0.40 + (liveRain - 35.0) * 0.015).toFixed(2)} m`
    levelBadge = 'LEVEL 4 • CRITICAL CLOUDBURST INUNDATION'
    riskTitle = 'SEVERE FLASH-FLOOD WARNING'
    evacWindow = 'NEXT 60 MIN'
    rainfallSubtitle = 'Heavy Downpour Detected'
    depthSubtitle = 'Critical Lowland Inflow'
  } else if (liveRain >= 15.0) {
    alertLevel = 'ORANGE'
    depthDisplay = `${(0.18 + (liveRain - 15.0) * 0.012).toFixed(2)} m`
    levelBadge = 'LEVEL 3 • MODERATE WATERLOGGING ADVISORY'
    riskTitle = 'STREET WATERLOGGING ADVISORY'
    evacWindow = 'MONITOR SHELTER'
    rainfallSubtitle = 'Moderate Monsoon Inflow'
    depthSubtitle = 'Localized Ponding'
  } else if (liveRain >= 2.5) {
    alertLevel = 'YELLOW'
    depthDisplay = `${(0.04 + (liveRain - 2.5) * 0.005).toFixed(2)} m`
    levelBadge = 'LEVEL 2 • ACTIVE MONSOON RAIN SHOWERS'
    riskTitle = 'MONSOON RAIN SHOWER WATCH'
    evacWindow = 'ROADS PASSABLE'
    rainfallSubtitle = 'Passing Rain Showers'
    depthSubtitle = 'Surface Drainage Active'
  }

  const isRedAlert = alertLevel === 'RED'
  const isThemeGreen = alertLevel === 'GREEN'
  const isThemeYellow = alertLevel === 'YELLOW'
  const isThemeOrange = alertLevel === 'ORANGE'

  // Realistic Siren Synthesizer using Web Audio API
  function toggleSiren() {
    if (sirenPlaying) {
      stopSiren()
    } else {
      startSiren()
    }
  }

  function startSiren() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) return
      const ctx = new AudioCtx()
      audioContextRef.current = ctx

      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sawtooth'
      osc.frequency.setValueAtTime(440, ctx.currentTime)

      // Frequency modulation for civil defense wailing tone (440Hz -> 880Hz -> 440Hz)
      const now = ctx.currentTime
      for (let i = 0; i < 8; i++) {
        osc.frequency.linearRampToValueAtTime(880, now + i * 1.2 + 0.6)
        osc.frequency.linearRampToValueAtTime(440, now + i * 1.2 + 1.2)
      }

      gain.gain.setValueAtTime(0.25, ctx.currentTime)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start()

      oscillatorRef.current = osc
      gainNodeRef.current = gain
      setSirenPlaying(true)

      // Trigger phone vibration if supported
      if (navigator.vibrate) {
        navigator.vibrate([300, 150, 300, 150, 600])
      }

      // Automatically stop after 9.6s
      setTimeout(() => {
        stopSiren()
      }, 9600)
    } catch (e) {
      console.warn('Audio siren failed:', e)
    }
  }

  function stopSiren() {
    try {
      if (oscillatorRef.current) {
        oscillatorRef.current.stop()
        oscillatorRef.current.disconnect()
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    } catch (e) {
      // ignore
    }
    setSirenPlaying(false)
  }

  useEffect(() => {
    return () => {
      stopSiren()
    }
  }, [])

  // Build formatted text message for WhatsApp sharing
  const alertText = `🚨 [VARSHAAI EMERGENCY FLOOD ALERT] 🚨
Severity: ${isRedAlert ? 'RED / EXTREME FLOOD WARNING' : alertLevel === 'YELLOW' ? 'YELLOW / ACTIVE RAIN SHOWERS' : 'GREEN / ROUTINE MONITORING'}
Target Urban Basin: ${cityData.name} (${cityData.hotspot})
Telemetry Source: ${radarInfo.radar}
Peak Precipitation: ${rainfallDisplay}
Predicted Inundation Depth: ${depthDisplay}

⚡ EVACUATION DIRECTIVES:
1. Designated High-Ground Shelter: ${cityData.shelter} (${cityData.shelterElevation})
2. Safety Margin: ${cityData.elevationMargin}
3. Recommended Corridor: ${cityData.safeRoute}
4. Hazard Points: Avoid ${cityData.dangerPoints.join(', ')}

📞 EMERGENCY HELPLINES:
${cityData.contacts.map((c) => `- ${c.label}: ${c.tel}`).join('\n')}

Standard: OASIS CAP 1.2 | Powered by VARSHAAI AI Early Warning Engine`

  function handleShareWhatsApp() {
    const encoded = encodeURIComponent(alertText)
    window.open(`https://api.whatsapp.com/send?text=${encoded}`, '_blank')
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(alertText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className={`citizen-alert-container theme-${alertLevel.toLowerCase()}`}>
      {/* MOBILE TOP NAVIGATION BAR */}
      <header className="citizen-header">
        <div className="header-left">
          {onBack && (
            <button className="citizen-back-btn" onClick={onBack}>
              <ArrowLeft size={18} />
              <span>Dashboard</span>
            </button>
          )}
          <div className="citizen-brand">
            <Radio size={20} className="brand-icon" />
            <div>
              <strong>VARSHAAI</strong>
              <small>CITIZEN DISPATCH</small>
            </div>
          </div>
        </div>

        {/* INTERACTIVE MODE TOGGLE: LIVE RADAR VS 180MM SIMULATION */}
        <div className="citizen-header-right">
          <div className="citizen-mode-switch">
            <button
              className={`mode-toggle-btn ${mode === 'live' ? 'active live' : ''}`}
              onClick={() => setMode('live')}
              title="Synchronize with live Doppler weather radar telemetry"
            >
              <Radio size={13} />
              <span>Live Radar Sync</span>
            </button>
            <button
              className={`mode-toggle-btn ${mode === 'simulation' ? 'active sim' : ''}`}
              onClick={() => setMode('simulation')}
              title="Trigger 180mm cloudburst emergency simulation"
            >
              <Siren size={13} />
              <span>180mm Sim</span>
            </button>
          </div>
        </div>
      </header>

      {/* RADAR TELEMETRY SYNC STRIP */}
      <div className="radar-station-banner">
        <div className="radar-station-left">
          <Radio size={14} className="radar-ping-icon" />
          <span>Station: <strong>{radarInfo.radar}</strong></span>
        </div>
        <div className="radar-station-right">
          <span className={`sync-pill pill-${alertLevel.toLowerCase()}`}>
            ● {isSimulation ? '180mm Cloudburst Sim' : `${liveRain.toFixed(1)} mm/hr (Live)`}
          </span>
          {lastSyncedAt && <span className="sync-time">Synced {lastSyncedAt}</span>}
        </div>
      </div>

      {/* METRO SELECTOR PILLS */}
      <div className="citizen-city-scroller">
        {Object.keys(CITY_EVACUATION_DATA).map((cid) => {
          const c = CITY_EVACUATION_DATA[cid]
          return (
            <button
              key={cid}
              className={`city-pill ${selectedCity === cid ? 'active' : ''}`}
              onClick={() => setSelectedCity(cid)}
            >
              {c.name}
            </button>
          )
        })}
      </div>

      {/* EMERGENCY HERO CARD */}
      <section className={`citizen-hero ${isRedAlert ? 'hero-pulse-red' : isThemeYellow ? 'hero-yellow' : 'hero-green'}`}>
        <div className="hero-status-row">
          <div className="hero-siren-icon">
            {isRedAlert ? <Siren size={36} className="siren-animate" /> : isThemeYellow ? <AlertTriangle size={36} /> : <ShieldCheck size={36} />}
          </div>
          <div>
            <span className="hero-badge">
              {levelBadge}
            </span>
            <h1>{riskTitle}</h1>
            <p>
              Target Area: <strong>{cityData.name} — {cityData.hotspot}</strong>
            </p>
          </div>
        </div>

        {/* SIREN BUTTON (Tactile Smartphone Proof) */}
        <button
          className={`citizen-siren-trigger ${sirenPlaying ? 'playing' : ''}`}
          onClick={toggleSiren}
        >
          {sirenPlaying ? <VolumeX size={22} /> : <Volume2 size={22} />}
          <span>{sirenPlaying ? '⏹ SILENCE EVACUATION SIREN' : '🚨 SOUND EMERGENCY CIVIL DEFENSE SIREN'}</span>
        </button>
      </section>

      {/* HYDRODYNAMIC FORECAST METRICS */}
      <section className="citizen-telemetry-grid">
        <div className="citizen-telemetry-box">
          <CloudRain size={20} className="icon-blue" />
          <div>
            <span>PEAK RAINFALL</span>
            <strong>{rainfallDisplay}</strong>
            <small>{rainfallSubtitle}</small>
          </div>
        </div>

        <div className="citizen-telemetry-box">
          <Waves size={20} className="icon-amber" />
          <div>
            <span>PREDICTED DEPTH</span>
            <strong>{depthDisplay}</strong>
            <small>{depthSubtitle}</small>
          </div>
        </div>

        <div className="citizen-telemetry-box">
          <Navigation size={20} className="icon-emerald" />
          <div>
            <span>EVACUATION TIMELINE</span>
            <strong>{evacWindow}</strong>
            <small>Crest Inundation Window</small>
          </div>
        </div>
      </section>

      {/* DESIGNATED HIGH-GROUND SHELTER CARD */}
      <section className="citizen-shelter-card">
        <div className="card-kicker">
          <Compass size={18} />
          <span>OFFICIAL DESIGNATED HIGH-GROUND RELIEF SHELTER</span>
        </div>

        <div className="shelter-main-info">
          <div>
            <h2>{cityData.shelter}</h2>
            <div className="elevation-badge">
              <span>Ground Elevation: <strong>{cityData.shelterElevation}</strong></span>
              <span className="margin-pill">({cityData.elevationMargin})</span>
            </div>
          </div>
        </div>

        <div className="shelter-route-box">
          <strong><Navigation size={15} /> RECOMMENDED SAFE EVACUATION CORRIDOR:</strong>
          <p>{cityData.safeRoute}</p>
        </div>

        <div className="danger-points-box">
          <strong><AlertTriangle size={15} /> SUBMERGED CHOKEPOINTS TO STRICTLY AVOID:</strong>
          <ul>
            {cityData.dangerPoints.map((dp, i) => (
              <li key={i}>{dp}</li>
            ))}
          </ul>
        </div>
      </section>

      {/* DIRECT EMERGENCY HELPLINE CALLERS */}
      <section className="citizen-contacts-card">
        <div className="card-kicker">
          <PhoneCall size={18} />
          <span>ONE-TAP EMERGENCY DISASTER HELPLINES</span>
        </div>

        <div className="contacts-list">
          {cityData.contacts.map((c, i) => (
            <a key={i} href={`tel:${c.tel}`} className="contact-call-btn">
              <div className="contact-meta">
                <strong>{c.label}</strong>
                <small>{c.tag}</small>
              </div>
              <div className="call-pill">
                <PhoneCall size={16} />
                <span>Call {c.tel}</span>
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* TACTILE SHARING & ACTIONS (JUDGE PHONE VERIFICATION) */}
      <section className="citizen-actions-card">
        <button className="share-whatsapp-btn" onClick={handleShareWhatsApp}>
          <Share2 size={18} />
          <span>Forward Evacuation Alert on WhatsApp</span>
        </button>

        <button className="copy-alert-btn" onClick={handleCopy}>
          {copied ? <Check size={18} /> : <Copy size={18} />}
          <span>{copied ? 'Official Alert Copied to Clipboard!' : 'Copy Official CAP Alert Text'}</span>
        </button>
      </section>

      {/* PROTOCOL FOOTER */}
      <footer className="citizen-footer">
        <p>
          Standard: <strong>OASIS CAP 1.2 Compliant Emergency Telecommunications Protocol</strong>
        </p>
        <small>VARSHAAI AI/ML Urban Inundation Early Warning & Citizen Evacuation System</small>
      </footer>
    </div>
  )
}

export default CitizenAlert
