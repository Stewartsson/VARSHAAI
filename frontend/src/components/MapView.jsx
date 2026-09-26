import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Polygon,
  ZoomControl,
} from 'react-leaflet'

import 'leaflet/dist/leaflet.css'

import '../styles/MapView.css'


function MapView() {

  /*
   * Prototype center:
   * Thoothukudi / Tuticorin region
   *
   * Later this will come from:
   * Backend API → GeoJSON / raster prediction
   */

  const center = [13.0827, 80.2707]


  const riskZones = [
    {
      id: 1,
      position: [13.0827, 80.2707],
      name: 'Chennai Central',
      rainfall: '168 mm',
      floodDepth: '0.74 m',
      risk: 'HIGH',
    },
    {
      id: 2,
      position: [13.1200, 80.2500],
      name: 'North Zone',
      rainfall: '132 mm',
      floodDepth: '0.42 m',
      risk: 'MODERATE',
    },
    {
      id: 3,
      position: [13.0100, 80.2200],
      name: 'South Zone',
      rainfall: '104 mm',
      floodDepth: '0.28 m',
      risk: 'LOW',
    },
  ]


  const floodArea = [
    [13.1100, 80.2400],
    [13.1300, 80.2600],
    [13.1200, 80.3000],
    [13.0800, 80.3100],
    [13.0500, 80.2800],
    [13.0600, 80.2500],
  ]


  return (
    <div className="map-wrapper">

      <MapContainer
        center={center}
        zoom={11}
        scrollWheelZoom={true}
        zoomControl={false}
        className="varshaai-map"
      >

        <ZoomControl position="bottomright" />


        {/* =========================
            BASE MAP
        ========================= */}

        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />


        {/* =========================
            FLOOD PREDICTION AREA
        ========================= */}

        <Polygon
          positions={floodArea}
          pathOptions={{
            color: '#ef6c63',
            fillColor: '#ef6c63',
            fillOpacity: 0.25,
            weight: 2,
          }}
        >

          <Popup>

            <div className="map-popup">

              <strong>
                Predicted Inundation Zone
              </strong>

              <span>
                Risk: HIGH
              </span>

              <span>
                Predicted depth: 0.74 m
              </span>

            </div>

          </Popup>

        </Polygon>


        {/* =========================
            OBSERVATION / RISK POINTS
        ========================= */}

        {riskZones.map((zone) => (

          <CircleMarker
            key={zone.id}
            center={zone.position}
            radius={9}
            pathOptions={{
              color:
                zone.risk === 'HIGH'
                  ? '#ff6257'
                  : zone.risk === 'MODERATE'
                    ? '#e5b94c'
                    : '#55d49a',

              fillColor:
                zone.risk === 'HIGH'
                  ? '#ff6257'
                  : zone.risk === 'MODERATE'
                    ? '#e5b94c'
                    : '#55d49a',

              fillOpacity: 0.8,

              weight: 2,
            }}
          >

            <Popup>

              <div className="map-popup">

                <strong>
                  {zone.name}
                </strong>

                <span>
                  Rainfall: {zone.rainfall}
                </span>

                <span>
                  Flood depth: {zone.floodDepth}
                </span>

                <span>
                  Risk: {zone.risk}
                </span>

              </div>

            </Popup>

          </CircleMarker>

        ))}


      </MapContainer>


      {/* =========================
          MAP LEGEND
      ========================= */}

      <div className="map-legend">

        <div className="legend-title">
          RISK LEVEL
        </div>

        <div className="legend-item">
          <span className="legend-dot low"></span>
          Low
        </div>

        <div className="legend-item">
          <span className="legend-dot moderate"></span>
          Moderate
        </div>

        <div className="legend-item">
          <span className="legend-dot high"></span>
          High
        </div>

      </div>


      {/* =========================
          MAP LAYER INDICATOR
      ========================= */}

      <div className="map-layer-status">

        <span></span>

        LIVE PREDICTION LAYER

      </div>

    </div>
  )
}

export default MapView