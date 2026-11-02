import { useState, useEffect } from 'react'

export function useStationLines(stationId) {
    const [lines, setLines] = useState({})
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        setLoading(true)
        setError(null)
        fetch(`http://localhost:8000/api/station/lines?station_id=${encodeURIComponent(stationId)}`)
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json()
                    throw new Error(err.detail)
                }
                return res.json()
            })
            .then(data => {
                setLines(data)
                setLoading(false)
            })
            .catch(err => {
                setError(err.message)
                setLoading(false)
            })
    }, [stationId])

    return { lines, loading, error }
}