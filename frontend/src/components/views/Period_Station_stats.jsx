import { useState } from "react";


function PeriodStationStats({ station, onBack, onResult }) {

    const [selectedFromDate, setSelectedFromDate] = useState('')
    const [selectedToDate, setSelectedToDate] = useState('')
    const { data: result, loading, error, execute, reset } = usePostFetch()

    useEffect(() => {
        onResult?.(!!result)
    }, [result])

    const handleCalculate = () => {
        execute(`http://localhost:8000/api/XXX`)
    }
}

export default PeriodStationStats