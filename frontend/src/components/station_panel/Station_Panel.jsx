import { useEffect, useState } from 'react'

function StationPanel({ station, onClose, onShowStats }) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        setLoading(true)
        setData(null)
        fetch(`http://localhost:8000/api/station/info?station_id=${encodeURIComponent(station.id)}`)
            .then(res => res.json())
            .then(data => {
                setData(data)
                setLoading(false)
            })
            .catch(err => {
                console.error(err)
                setLoading(false)
            })
    }, [station.id])

    return (
        <div style={{
            position: 'absolute',
            top: 60,
            left: 16,
            width: 280,
            background: 'rgba(20, 20, 30, 0.92)',
            borderRadius: 12,
            padding: 16,
            color: 'white',
            pointerEvents: 'auto',
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
            backdropFilter: 'blur(8px)',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16 }}>{station.name}</h3>
                <button onClick={onClose} style={{
                    background: 'none', border: 'none', color: 'white',
                    cursor: 'pointer', fontSize: 18, lineHeight: 1
                }}>✕</button>
            </div>

            {loading ? (
                <p style={{ margin: 0, opacity: 0.6 }}>Lädt...</p>
            ) : (
                <>
                    <p style={{ margin: '0 0 10px', opacity: 0.6, fontSize: 12 }}>{data.stop_name} - Abfahrten</p>
                    {data.departures.map((dep, index) => (
                        <div key={index} style={{
                            borderTop: '1px solid rgba(255,255,255,0.1)',
                            paddingTop: 8,
                            marginTop: 8,
                            display: 'grid',
                            gridTemplateColumns: '1fr auto',
                            gap: '2px 8px',
                            fontSize: 13
                        }}>
                            <span style={{ fontWeight: 'bold', color: '#aa3bff' }}>{dep.line}</span>
                            <span style={{ textAlign: 'right', opacity: 0.9 }}>{dep.time}</span>
                            <span style={{ opacity: 0.7 }}>{dep.direction}</span>
                            <span style={{ textAlign: 'right', opacity: 0.5, fontSize: 11 }}>{dep.date}</span>
                        </div>
                    ))}
                </>
            )}
            <button onClick={onShowStats} style={{
                marginTop: 16,
                width: '100%',
                padding: '8px 0',
                background: 'rgba(170, 59, 255, 0.2)',
                border: '1px solid rgba(170, 59, 255, 0.5)',
                borderRadius: 8,
                color: 'white',
                cursor: 'pointer',
                fontSize: 13,
            }}>
                Statistiken anzeigen
            </button>
        </div>
    )
}

export default StationPanel