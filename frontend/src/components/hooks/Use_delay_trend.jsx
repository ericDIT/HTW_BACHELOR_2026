import { useState, useEffect } from 'react'

function toDateString(date) {
    return date.toISOString().slice(0, 10)
}

export function useDelayTrend(stationId) {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const to = new Date()
        const from = new Date()
        from.setDate(from.getDate() - 30)

        setLoading(true)
        setError(null)
        fetch(`http://localhost:8000/api/daily_facts/trend?station_id=${encodeURIComponent(stationId)}&from_date=${toDateString(from)}&to_date=${toDateString(to)}`)
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json()
                    throw new Error(err.detail)
                }
                return res.json()
            })
            .then(json => { setData(json); setLoading(false) })
            .catch(err => { setError(err.message); setLoading(false) })
    }, [stationId])

    return { data, loading, error }
}