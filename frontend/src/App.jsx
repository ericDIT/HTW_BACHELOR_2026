import { useState } from 'react'
import Map, { Marker, Popup } from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import StationPanel from './components/station_panel/Station_Panel'
import StatsPanel from './components/stats_panel/Stats_Panel'

const stations = [
  { id: "A=1@O=S Halensee (Berlin)@X=13290147@Y=52496698@U=86@L=900040101@",
    name: "S Halensee",
    longitude: 13.290147,
    latitude: 52.496698
  }
]

function App() {
  const [viewState, setViewState] = useState({
    longitude: 13.404954,
    latitude: 52.520008,
    zoom: 11
  })
  const [selectedStation, setSelectedStation] = useState(null)
  const [showStats, setShowStats] = useState(false)

  console.log("selectedStation:", selectedStation)
  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh" }}>

      <Map
        {...viewState}
        onMove={e => setViewState(e.viewState)}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        mapboxAccessToken={import.meta.env.VITE_MAPBOX_PUBLIC_TOKEN}
        minZoom={10}
        maxBounds={[
          [13.088333, 52.338190],  // Südwest-Ecke Berlin
          [13.761390, 52.675499]   // Nordost-Ecke Berlin
        ]}
      >
        {stations.map(station => (
          <Marker
            key={station.id}
            longitude={station.longitude}
            latitude={station.latitude}
            anchor='center'
            onClick={(e) => {
              e.originalEvent.stopPropagation()
              setSelectedStation(station)
            }}
          >
            <div 
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: "#aa3bff",
                border: "2px solid white",
                cursor: "pointer"
              }}
            />
          </Marker>
        ))}
        {selectedStation && (
          <StationPanel
              station={selectedStation}
              onClose={() => { setSelectedStation(null); setShowStats(false) }}
              onShowStats={() => setShowStats(true)}
          />
        )}
        {showStats && selectedStation && (
          <StatsPanel
              station={selectedStation}
              onClose={() => setShowStats(false)}
          />
        )}
      </Map>

      <div style={{
        position: "absolute",
        top: 0, left: 0,
        width: "100%", height: "100%",
        pointerEvents: "none"
      }}>
        <div style={{ pointerEvents: "auto", padding: 10, color: "white" }}>
          BA | Eric M. | Testsystem
        </div>
      </div>

    </div>
  )
}

export default App