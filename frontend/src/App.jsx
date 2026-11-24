import { useState, useEffect } from 'react'

import {
  LayoutDashboard,
  Database,
  BrainCircuit,
  Waves,
  BarChart3,
  Siren,
  Radio,
  Navigation,
  Camera,
  Globe,
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
import CityHub from './components/CityHub'
import CitizenAlert from './components/CitizenAlert'
import UrbanSimulation from './components/UrbanSimulation'
import CrowdsourceTriage from './components/CrowdsourceTriage'
import LiveSatelliteMaps from './components/LiveSatelliteMaps'


function getInitialPage() {
  if (typeof window !== 'undefined') {
    const p = new URLSearchParams(window.location.search).get('page')
    if (p) return p
    const hash = window.location.hash.replace('#', '')
    if (hash) return hash
  }
  return 'command'
}


function App() {

  // =========================================================
  // ACTIVE PAGE & BROWSER HISTORY SYNCHRONIZATION
  // =========================================================

  const [activePage, setActivePage] = useState(getInitialPage)

  // Navigate to page and create a browser history entry (so Back/Forward work seamlessly)
  const navigateToPage = (newPage, replace = false) => {
    if (!newPage) return
    if (newPage === activePage) return

    setActivePage(newPage)

    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      url.searchParams.set('page', newPage)
      url.hash = ''

      if (replace) {
        window.history.replaceState({ page: newPage }, '', url.toString())
      } else {
        // Only push if history state isn't already this page
        if (window.history.state?.page !== newPage) {
          window.history.pushState({ page: newPage }, '', url.toString())
        }
      }

      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // Listen to browser Back and Forward button events (popstate)
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Initialize root history state
    const initial = getInitialPage()
    const url = new URL(window.location.href)
    url.searchParams.set('page', initial)
    window.history.replaceState({ page: initial }, '', url.toString())

    const handlePopState = (event) => {
      const targetPage =
        event.state?.page ||
        new URLSearchParams(window.location.search).get('page') ||
        window.location.hash.replace('#', '') ||
        'command'

      setActivePage(targetPage)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const handleNavigateBack = () => {
    if (typeof window !== 'undefined') {
      if (window.history.length > 1) {
        window.history.back()
      } else {
        navigateToPage('command')
      }
    }
  }

  const handleNavigateForward = () => {
    if (typeof window !== 'undefined') {
      window.history.forward()
    }
  }


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

    {
      id: 'cities',
      label: 'Multi-City Radar',
      icon: Radio,
    },

    {
      id: 'satellite-maps',
      label: 'Live Satellite & Ocean',
      icon: Globe,
    },

    {
      id: 'routing',
      label: 'Safe Routing & Stress',
      icon: Navigation,
    },

    {
      id: 'crowdsource',
      label: 'Crowdsourced Triage',
      icon: Camera,
    },
  ]


  // =========================================================
  // SOURCE DETAIL NAVIGATION
  // =========================================================

  const handleSourceSelect = (sourceType) => {

    navigateToPage(`source-${sourceType}`)

  }


  // =========================================================
  // BACK TO DATA INTELLIGENCE
  // =========================================================

  const handleSourceBack = () => {

    handleNavigateBack()

  }


  // =========================================================
  // APPLICATION
  // =========================================================

  const isDirectMobileView =
    typeof window !== 'undefined' &&
    (new URLSearchParams(window.location.search).get('page') === 'citizen-alert' ||
      window.location.hash === '#citizen-alert')

  if (isDirectMobileView) {
    return (
      <div className="app-shell standalone-mobile">
        <CitizenAlert
          onBack={() => {
            if (typeof window !== 'undefined' && window.history.length > 1) {
              window.history.back()
            } else {
              window.location.href = window.location.origin
            }
          }}
        />
      </div>
    )
  }

  return (

    <div className="app-shell">


      {/* =====================================================
          HEADER
          ===================================================== */}

      <Header
        activePage={activePage}
        onNavigateBack={handleNavigateBack}
        onNavigateForward={handleNavigateForward}
      />


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
          setActivePage={navigateToPage}
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
              MULTI-CITY RADAR / NATIONAL GRID
              ================================================= */}

          {activePage === 'cities' && (
            <CityHub />
          )}


          {/* =================================================
              LIVE METEOROLOGICAL SATELLITE & OCEAN OBSERVATORY
              ================================================= */}

          {activePage === 'satellite-maps' && (
            <LiveSatelliteMaps />
          )}


          {/* =================================================
              SAFE ROUTING & URBAN DRAINAGE SIMULATOR
              ================================================= */}

          {activePage === 'routing' && (
            <UrbanSimulation />
          )}


          {/* =================================================
              CROWDSOURCED TRIAGE & SNAP-AND-VERIFY
              ================================================= */}

          {activePage === 'crowdsource' && (
            <CrowdsourceTriage />
          )}


          {/* =================================================
              CITIZEN ALERT & EVACUATION MOBILE TERMINAL
              ================================================= */}

          {activePage === 'citizen-alert' && (
            <CitizenAlert onBack={handleNavigateBack} />
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