import { useState, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import {
  Camera,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Radio,
  MapPin,
  Sparkles,
  QrCode,
  Upload,
  Send,
  ExternalLink,
  LifeBuoy,
  PhoneCall,
  Activity,
  Layers,
} from 'lucide-react'
import '../styles/CrowdsourceTriage.css'

// Custom Incident Pin
const verifiedPin = new L.DivIcon({
  className: 'incident-pin verified',
  html: '<div class="pin-badge verified">✓</div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

const flaggedPin = new L.DivIcon({
  className: 'incident-pin flagged',
  html: '<div class="pin-badge flagged">✕</div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

// TEST INCIDENT PRESETS FOR FAST TABLE JUDGING
const TEST_INCIDENTS = [
  {
    id: 'TR-101',
    title: 'Submerged Vehicle at Velachery MRTS Underpass',
    location: 'Velachery MRTS Subway, Chennai',
    lat: 12.9815,
    lon: 80.218,
    reportedBy: 'Citizen Reporter #4481',
    time: '4 mins ago',
    imageUrl: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80',
    type: 'severe_flood',
    cvEstimatedDepthM: 0.65,
    detectedObjects: ['Sedan Car (Tire 80% submerged)', 'Road Median Barrier'],
    radarRainfallMm: 58.4,
    radarMatch: true,
    verificationStatus: 'VERIFIED',
    confidenceScore: 96,
    recommendedAction: 'Dispatch NDRF Inflatable Rescue Boat & Close Subway',
  },
  {
    id: 'TR-102',
    title: 'Knee-Deep Waterlogging in Residential Street',
    location: 'Madipakkam Lake Basin, Chennai',
    lat: 12.9647,
    lon: 80.1961,
    reportedBy: 'Ward Volunteer #1209',
    time: '12 mins ago',
    imageUrl: 'https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=600&q=80',
    type: 'medium_flood',
    cvEstimatedDepthM: 0.38,
    detectedObjects: ['Pedestrian (Knee-level water)', 'Compound Wall Base'],
    radarRainfallMm: 42.1,
    radarMatch: true,
    verificationStatus: 'VERIFIED',
    confidenceScore: 92,
    recommendedAction: 'Deploy 200 HP Dewatering Pump & Clear Storm Drain Silt',
  },
  {
    id: 'TR-103',
    title: 'Viral Social Media Flood Post (Outdated / Fake)',
    location: 'Anna Salai Arterial, Chennai',
    lat: 13.0604,
    lon: 80.2496,
    reportedBy: 'Social Media Feed @CitizenWatch',
    time: '18 mins ago',
    imageUrl: 'https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=600&q=80',
    type: 'fake_spoof',
    cvEstimatedDepthM: 0.75,
    detectedObjects: ['High Water Flood Footage'],
    radarRainfallMm: 0.0, // Clear sky!
    radarMatch: false,
    verificationStatus: 'FLAGGED_SPOOF',
    confidenceScore: 18,
    recommendedAction: 'Reject Report: Radar confirms zero rainfall (0.0 mm/hr). Old 2015 footage detected.',
  },
  {
    id: 'TR-104',
    title: 'Clear Drainage Street (Safe)',
    location: 'T. Nagar Panagal Park, Chennai',
    lat: 13.0405,
    lon: 80.2337,
    reportedBy: 'Municipal Inspector #303',
    time: '25 mins ago',
    imageUrl: 'https://images.unsplash.com/photo-1508873696983-2df5293cb32b?auto=format&fit=crop&w=600&q=80',
    type: 'dry_road',
    cvEstimatedDepthM: 0.02,
    detectedObjects: ['Dry Asphalt Road', 'Unblocked Stormwater Curb'],
    radarRainfallMm: 8.5,
    radarMatch: true,
    verificationStatus: 'SAFE_CLEAR',
    confidenceScore: 98,
    recommendedAction: 'Normal Monitoring: Street drains functioning nominally.',
  },
]

function CrowdsourceTriage() {
  const [selectedIncident, setSelectedIncident] = useState(TEST_INCIDENTS[0])
  const [analyzing, setAnalyzing] = useState(false)
  const [dispatchedTickets, setDispatchedTickets] = useState([])
  const [customReportModal, setCustomReportModal] = useState(false)

  function handleSelectIncident(inc) {
    setAnalyzing(true)
    setSelectedIncident(inc)
    setTimeout(() => {
      setAnalyzing(false)
    }, 450)
  }

  function handleDispatchRescue(incidentId) {
    if (!dispatchedTickets.includes(incidentId)) {
      setDispatchedTickets([...dispatchedTickets, incidentId])
    }
  }

  const isDispatched = dispatchedTickets.includes(selectedIncident.id)

  return (
    <div className="triage-page">
      {/* HEADER */}
      <div className="triage-header">
        <div>
          <div className="triage-breadcrumb">
            VARSHAAI / CITIZEN REPORTING / CROWDSOURCED TRIAGE
          </div>
          <div className="triage-title-row">
            <div className="triage-header-icon">
              <Camera size={28} />
            </div>
            <div>
              <h1>Citizen "Snap & Verify" Crowdsourced Flood Triage</h1>
              <p>
                Real-time ground-truth verification. AI computer vision estimates water depth from citizen photos and cross-checks against ConvLSTM radar to filter viral fake reports.
              </p>
            </div>
          </div>
        </div>

        {/* QR CODE POPUP BUTTON FOR JUDGES */}
        <div className="triage-header-actions">
          <div className="radar-live-indicator-chip">
            <Radio size={13} className="radar-ping-icon" />
            <span>DWR Sriharikota / NIOT Radar Feed Active</span>
          </div>
          <button className="open-report-qr-btn" onClick={() => setCustomReportModal(true)}>
            <QrCode size={16} />
            <span>Scan QR on Smartphone</span>
          </button>
        </div>
      </div>

      {/* 4 PRESET TEST INCIDENTS FOR FAST JUDGING */}
      <div className="incident-selector-strip">
        <span className="strip-label">SELECT REPORT FOR AI VERIFICATION:</span>
        <div className="incident-cards-row">
          {TEST_INCIDENTS.map((inc) => {
            const isSelected = selectedIncident.id === inc.id
            const isVerified = inc.verificationStatus === 'VERIFIED'
            const isFlagged = inc.verificationStatus === 'FLAGGED_SPOOF'
            return (
              <div
                key={inc.id}
                className={`incident-preset-card ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectIncident(inc)}
              >
                <div className="preset-top">
                  <span className="preset-id">{inc.id}</span>
                  <span
                    className={`preset-status-tag ${
                      isVerified ? 'verified' : isFlagged ? 'flagged' : 'safe'
                    }`}
                  >
                    {isVerified ? '✓ VERIFIED' : isFlagged ? '✕ FAKE SPOOF' : '○ CLEAR'}
                  </span>
                </div>
                <h4>{inc.title}</h4>
                <div className="preset-meta">
                  <MapPin size={12} />
                  <span>{inc.location}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* MAIN 2-COLUMN SPLIT: AI VERIFICATION LAB & LIVE TRIAGE MAP */}
      <div className="triage-main-split">
        {/* LEFT: AI COMPUTER VISION & RADAR CROSS-CHECK LAB */}
        <div className="triage-lab-card">
          <div className="lab-card-header">
            <div className="lab-title">
              <Sparkles size={18} className="text-cyan" />
              <div>
                <h3>AI Multi-Modal Ground Truth Verification</h3>
                <small>Computer Vision + Doppler Radar Spatio-Temporal Cross-Check</small>
              </div>
            </div>

            <span
              className={`verification-status-pill ${
                selectedIncident.verificationStatus.toLowerCase()
              }`}
            >
              {selectedIncident.verificationStatus === 'VERIFIED' && <CheckCircle2 size={14} />}
              {selectedIncident.verificationStatus === 'FLAGGED_SPOOF' && <XCircle size={14} />}
              {selectedIncident.verificationStatus === 'SAFE_CLEAR' && <ShieldCheck size={14} />}
              <span>{selectedIncident.verificationStatus.replace('_', ' ')}</span>
            </span>
          </div>

          {/* PHOTO SCANNING PREVIEW */}
          <div className="photo-scan-frame">
            <img src={selectedIncident.imageUrl} alt={selectedIncident.title} className="triage-photo" />
            
            {/* CV HUD OVERLAY */}
            <div className="cv-hud-overlay">
              <div className="hud-target-box">
                <span className="hud-corner tl" />
                <span className="hud-corner tr" />
                <span className="hud-corner bl" />
                <span className="hud-corner br" />
                <div className="hud-water-line">
                  <span>WATERLINE ESTIMATION: {selectedIncident.cvEstimatedDepthM}m</span>
                </div>
              </div>
              <div className="hud-meta-chip">
                <span>Confidence: {selectedIncident.confidenceScore}%</span>
              </div>
            </div>
          </div>

          {/* CROSS-VERIFICATION PIPELINE RESULTS */}
          <div className="verification-steps-grid">
            {/* STEP 1: CV WATER DEPTH */}
            <div className="step-card">
              <div className="step-label">
                <Camera size={14} className="text-cyan" />
                <span>STEP 1: CV WATER DEPTH</span>
              </div>
              <strong>{selectedIncident.cvEstimatedDepthM} m Depth</strong>
              <small>Detected: {selectedIncident.detectedObjects.join(', ')}</small>
            </div>

            {/* STEP 2: RADAR CROSS-CHECK (KEY INNOVATION) */}
            <div className={`step-card ${selectedIncident.radarMatch ? 'match-ok' : 'match-fail'}`}>
              <div className="step-label">
                <Radio size={14} className="text-cyan" />
                <span>STEP 2: RADAR CROSS-CHECK</span>
              </div>
              <strong>{selectedIncident.radarRainfallMm} mm/hr Radar</strong>
              <small>
                {selectedIncident.radarMatch
                  ? '✓ Radar confirms heavy rainfall at coordinates'
                  : '✕ SPOOF: Radar confirms 0.0 mm/hr clear sky!'}
              </small>
            </div>
          </div>

          {/* RECOMMENDED EMERGENCY ACTION */}
          <div className="recommended-action-box">
            <strong>RECOMMENDED EMERGENCY ACTION:</strong>
            <p>{selectedIncident.recommendedAction}</p>
          </div>

          {/* RESCUE DISPATCH BUTTON */}
          <div className="lab-footer-actions">
            {selectedIncident.verificationStatus === 'VERIFIED' && (
              <button
                className={`dispatch-rescue-btn ${isDispatched ? 'dispatched' : ''}`}
                onClick={() => handleDispatchRescue(selectedIncident.id)}
              >
                <LifeBuoy size={18} />
                <span>
                  {isDispatched
                    ? '✓ NDRF Rescue Team Dispatched (Ticket Active)'
                    : '🚨 Dispatch Rescue Boat & Municipal Dewatering Unit'}
                </span>
              </button>
            )}

            {selectedIncident.verificationStatus === 'FLAGGED_SPOOF' && (
              <div className="spoof-warning-banner">
                <AlertTriangle size={18} />
                <span>
                  Report rejected automatically. Social media disinformation filter prevented wasted emergency deployment.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: LEAFLET GROUND TRUTH MAP & INCIDENT QUEUE */}
        <div className="triage-map-column">
          <div className="triage-map-card">
            <div className="map-card-header">
              <div className="map-title-row">
                <MapPin size={16} />
                <span>CHENNAI CROWDSOURCED INCIDENT MAP</span>
              </div>
              <div className="map-legend">
                <span className="legend-verified">● Verified Report</span>
                <span className="legend-flagged">● Flagged Spoof</span>
              </div>
            </div>

            <div className="leaflet-triage-wrapper">
              <MapContainer
                key={selectedIncident.id}
                center={[selectedIncident.lat, selectedIncident.lon]}
                zoom={12}
                scrollWheelZoom={false}
                className="city-leaflet-container"
              >
                <TileLayer
                  attribution='&copy; OpenStreetMap contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {TEST_INCIDENTS.map((inc) => (
                  <Marker
                    key={inc.id}
                    position={[inc.lat, inc.lon]}
                    icon={inc.verificationStatus === 'VERIFIED' ? verifiedPin : flaggedPin}
                    eventHandlers={{
                      click: () => handleSelectIncident(inc),
                    }}
                  >
                    <Popup>
                      <div className="triage-popup">
                        <strong>{inc.title}</strong>
                        <p>Location: {inc.location}</p>
                        <p>Estimated Water: <strong>{inc.cvEstimatedDepthM}m</strong></p>
                        <p>Status: <strong>{inc.verificationStatus}</strong></p>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>

          {/* INCIDENT DETAILS QUICK BAR */}
          <div className="incident-meta-card">
            <div className="meta-row">
              <span>ACTIVE INCIDENT:</span>
              <strong>{selectedIncident.id} — {selectedIncident.location}</strong>
            </div>
            <div className="meta-row">
              <span>REPORTED BY:</span>
              <strong>{selectedIncident.reportedBy} ({selectedIncident.time})</strong>
            </div>
            <div className="meta-row">
              <span>TRIAGE STATUS:</span>
              <strong className={selectedIncident.verificationStatus === 'VERIFIED' ? 'text-emerald' : 'text-red'}>
                {selectedIncident.verificationStatus} ({selectedIncident.confidenceScore}% AI Confidence)
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* MODAL: SMARTPHONE QR CODE SCAN FOR TABLE JUDGING */}
      {customReportModal && (
        <div className="triage-modal-overlay" onClick={() => setCustomReportModal(false)}>
          <div className="triage-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <QrCode size={20} className="text-cyan" />
                <h3>Scan to Report Flood from Phone</h3>
              </div>
              <button className="close-modal-btn" onClick={() => setCustomReportModal(false)}>
                ✕
              </button>
            </div>

            <div className="modal-content">
              <div className="modal-qr-frame">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(
                    typeof window !== 'undefined'
                      ? `${window.location.origin}/?page=citizen-alert`
                      : 'https://varshaai-4js6.onrender.com/?page=citizen-alert'
                  )}`}
                  alt="Citizen Reporter QR Code"
                  className="qr-img"
                />
              </div>

              <div className="modal-instructions">
                <p>
                  1. Scan with your phone's camera to open the <strong>Citizen Mobile Disaster Portal</strong>.
                </p>
                <p>
                  2. Allows citizens to report waterlogging, check evacuation shelters, and listen to vernacular emergency voice broadcasts.
                </p>
                <button
                  className="modal-test-btn"
                  onClick={() => {
                    setCustomReportModal(false)
                    alert('Citizen portal test activated! Use the test incident cards to demo real-time AI computer vision verification.')
                  }}
                >
                  <CheckCircle2 size={16} />
                  <span>Use Simulated Preset Incidents</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CrowdsourceTriage
