import { useState } from 'react'

// loading/error/result pattern
export function usePostFetch() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const execute = (url) => {
        setLoading(true)
        setData(null)
        setError(null)
        return fetch(url, { method: 'POST' })
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json()
                    throw new Error(err.detail)
                }
                return res.json()
            })
            .then(json => {
                setData(json)
                setLoading(false)
            })
            .catch(err => {
                setError(err.message)
                setLoading(false)
            })
    }

    const reset = () => {
        setData(null)
        setError(null)
    }

    return { data, loading, error, execute, reset }
}

export default usePostFetch