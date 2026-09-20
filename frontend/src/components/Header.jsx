import {
  CloudRain,
  Activity,
  Server,
  Cpu,
} from 'lucide-react'

import '../styles/Header.css'

function Header() {
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