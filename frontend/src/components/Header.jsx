import {
  CloudRain,
  Activity,
  Server,
  Cpu,
  ArrowLeft,
  ArrowRight,
} from 'lucide-react'

import '../styles/Header.css'

function Header({ activePage, onNavigateBack, onNavigateForward }) {
  return (
    <header className="top-header">

      <div className="brand-section">
        <div className="brand-icon">
          <CloudRain size={25} />
        </div>

        <div className="brand-text">
          <div className="brand-name">
            VARSHAAI
          </div>

          <div className="brand-subtitle">
            AI DISASTER INTELLIGENCE
          </div>
        </div>

        {/* IN-APP HISTORY NAV (BACK & FORWARD) */}
        <div className="header-nav-controls">
          <button
            type="button"
            className="header-nav-btn"
            title="Back to previous page"
            onClick={onNavigateBack}
          >
            <ArrowLeft size={14} />
            <span className="nav-btn-text">Back</span>
          </button>
          <button
            type="button"
            className="header-nav-btn icon-only"
            title="Forward to next page"
            onClick={onNavigateForward}
          >
            <ArrowRight size={14} />
          </button>
        </div>
      </div>


      <div className="header-center">
        <div className="system-title">
          HEAVY RAINFALL & INUNDATION
        </div>

        <div className="system-subtitle">
          EARLY WARNING COMMAND PLATFORM
        </div>
      </div>


      <div className="header-status">

        <div className="status-item">
          <Server size={16} />

          <div>
            <span>API</span>
            <strong>ONLINE</strong>
          </div>
        </div>


        <div className="status-item">
          <Cpu size={16} />

          <div>
            <span>AI ENGINE</span>
            <strong>READY</strong>
          </div>
        </div>


        <div className="live-indicator">
          <Activity size={16} />

          <span>LIVE</span>
        </div>

      </div>

    </header>
  )
}

export default Header