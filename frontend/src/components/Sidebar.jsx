import {
  ChevronRight,
  Database,
  BrainCircuit,
  Activity,
  Server,
} from 'lucide-react'

import '../styles/Sidebar.css'

function Sidebar({
  navigationItems,
  activePage,
  setActivePage,
}) {
  return (
    <aside className="sidebar">

      <div className="sidebar-section">

        <div className="sidebar-label">
          OPERATIONS
        </div>

        <nav className="navigation-menu">

          {navigationItems.map((item) => {

            const Icon = item.icon

            const isActive =
              activePage === item.id

            return (
              <button
                key={item.id}
                className={`nav-item ${
                  isActive ? 'active' : ''
                }`}
                onClick={() =>
                  setActivePage(item.id)
                }
              >

                <Icon size={18} />

                <span>{item.label}</span>

                {isActive && (
                  <ChevronRight
                    size={15}
                    className="nav-arrow"
                  />
                )}

              </button>
            )
          })}

        </nav>

      </div>


      <div className="sidebar-divider"></div>


      <div className="pipeline-section">

        <div className="sidebar-label">
          AI PIPELINE
        </div>


        <div className="pipeline-item">

          <div className="pipeline-icon">
            <Database size={15} />
          </div>

          <div>
            <strong>DATA PIPELINE</strong>
            <span>Multi-source ingestion</span>
          </div>

          <div className="pipeline-status"></div>

        </div>


        <div className="pipeline-item">

          <div className="pipeline-icon">
            <BrainCircuit size={15} />
          </div>

          <div>
            <strong>AI ENGINE</strong>
            <span>Prediction models</span>
          </div>

          <div className="pipeline-status"></div>

        </div>


        <div className="pipeline-item">

          <div className="pipeline-icon">
            <Activity size={15} />
          </div>

          <div>
            <strong>INUNDATION</strong>
            <span>Flood simulation</span>
          </div>

          <div className="pipeline-status"></div>

        </div>

      </div>


      <div className="sidebar-bottom">

        <div className="connection-box">

          <div className="connection-header">

            <Server size={15} />

            <span>SYSTEM STATUS</span>

          </div>


          <div className="connection-row">
            <span>Backend API</span>

            <div className="connection-online">
              <span></span>
              Online
            </div>
          </div>


          <div className="connection-row">
            <span>Data Services</span>

            <div className="connection-online">
              <span></span>
              Ready
            </div>
          </div>


          <div className="connection-row">
            <span>AI Services</span>

            <div className="connection-online">
              <span></span>
              Ready
            </div>
          </div>

        </div>


        <div className="version">
          VARSHAAI v1.0 • SIH 2026
        </div>

      </div>

    </aside>
  )
}

export default Sidebar