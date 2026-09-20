import { useState } from 'react'

import {
  LayoutDashboard,
  Database,
  BrainCircuit,
  Waves,
  BarChart3,
  Siren,
} from 'lucide-react'

import Header from './components/Header'
import Sidebar from './components/Sidebar'

import CommandCenter from './components/CommandCenter'
import DataIntelligence from './components/DataIntelligence'
import AIForecast from './components/AIForecast'
import Inundation from './components/Inundation'
import Validation from './components/Validation'
import AlertCenter from './components/AlertCenter'
import SourceDetail from './components/SourceDetail'


function App() {

  // =========================================================
  // ACTIVE PAGE
  // =========================================================

  const [activePage, setActivePage] = useState('command')


  // =========================================================
  // NAVIGATION ITEMS
  // =========================================================

  const navigationItems = [
    {
      id: 'command',
      label: 'Command Center',
      icon: LayoutDashboard,
    },

    {
      id: 'data',
      label: 'Data Intelligence',
      icon: Database,
    },

    {
      id: 'forecast',
      label: 'AI Forecast',
      icon: BrainCircuit,
    },

    {
      id: 'inundation',
      label: 'Inundation',
      icon: Waves,
    },

    {
      id: 'validation',
      label: 'Validation',
      icon: BarChart3,
    },

    {
      id: 'alerts',
      label: 'Alert Center',
      icon: Siren,
    },
  ]


  // =========================================================
  // SOURCE DETAIL NAVIGATION
  // =========================================================

  const handleSourceSelect = (sourceType) => {

    setActivePage(`source-${sourceType}`)

  }


  // =========================================================
  // BACK TO DATA INTELLIGENCE
  // =========================================================

  const handleSourceBack = () => {

    setActivePage('data')

  }


  // =========================================================
  // APPLICATION
  // =========================================================

  return (

    <div className="app-shell">


      {/* =====================================================
          HEADER
          ===================================================== */}

      <Header />


      {/* =====================================================
          BODY
          ===================================================== */}

      <div className="app-body">


        {/* ===================================================
            SIDEBAR
            =================================================== */}

        <Sidebar
          navigationItems={navigationItems}
          activePage={activePage}
          setActivePage={setActivePage}
        />


        {/* ===================================================
            MAIN CONTENT
            =================================================== */}

        <main className="main-content">


          {/* =================================================
              COMMAND CENTER
              ================================================= */}

          {activePage === 'command' && (
            <CommandCenter />
          )}


          {/* =================================================
              DATA INTELLIGENCE
              ================================================= */}

          {activePage === 'data' && (
            <DataIntelligence
              onSourceSelect={handleSourceSelect}
            />
          )}


          {/* =================================================
              AI FORECAST
              ================================================= */}

          {activePage === 'forecast' && (
            <AIForecast />
          )}


          {/* =================================================
              INUNDATION
              ================================================= */}

          {activePage === 'inundation' && (
            <Inundation />
          )}


          {/* =================================================
              VALIDATION
              ================================================= */}

          {activePage === 'validation' && (
            <Validation />
          )}


          {/* =================================================
              ALERT CENTER
              ================================================= */}

          {activePage === 'alerts' && (
            <AlertCenter />
          )}


          {/* =================================================
              SATELLITE DETAIL
              ================================================= */}

          {activePage === 'source-satellite' && (
            <SourceDetail
              sourceType="satellite"
              onBack={handleSourceBack}
            />
          )}


          {/* =================================================
              RADAR DETAIL
              ================================================= */}

          {activePage === 'source-radar' && (
            <SourceDetail
              sourceType="radar"
              onBack={handleSourceBack}
            />
          )}


          {/* =================================================
              AWS DETAIL
              ================================================= */}

          {activePage === 'source-aws' && (
            <SourceDetail
              sourceType="aws"
              onBack={handleSourceBack}
            />
          )}


          {/* =================================================
              ARG DETAIL
              ================================================= */}

          {activePage === 'source-arg' && (
            <SourceDetail
              sourceType="arg"
              onBack={handleSourceBack}
            />
          )}


          {/* =================================================
              NWP DETAIL
              ================================================= */}

          {activePage === 'source-nwp' && (
            <SourceDetail
              sourceType="nwp"
              onBack={handleSourceBack}
            />
          )}


        </main>

      </div>

    </div>

  )
}


export default App