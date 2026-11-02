import { useState, useEffect } from 'react'
import BackButton from '../shared/Back_button'
import DateInput from '../shared/Date_input'
import StatGrid from '../shared/Stat_grid'
import { calculateButtonStyle, inputStyle } from '../shared/styles'
import { formatRate } from '../shared/format'
import { usePostFetch } from '../hooks/Use_post_fetch'
import { useStationLines } from '../hooks/Use_station_lines'

function DayLineStats({ station, onBack, onResult }) {
    const [selectedDate, setSelectedDate] = useState('')
    const [selectedLine, setSelectedLine] = useState('')
    const { lines, loading: linesLoading, error: linesError } = useStationLines(station.id)
    const { data: result, loading, error, execute, reset } = usePostFetch()

    useEffect(() => {
        onResult?.(!!result)
    }, [result])

    const handleCalculate = () => {
        execute(`http://localhost:8000/api/daily_facts/by_line?fact_date=${selectedDate}&station_id=${encodeURIComponent(station.id)}&line_id=${encodeURIComponent(selectedLine)}`)
    }

    const handleBack = () => {
        reset()
        onBack()
    }

    if (!result) {
        return (
            <>
                <BackButton onClick={handleBack} />

                <p style={{ margin: '0 0 12px', fontSize: 13, opacity: 0.7 }}>Wähle eine Linie:</p>
                {linesLoading && <p style={{ fontSize: 13, opacity: 0.6, marginBottom: 12 }}>Lade Linien...</p>}
                {linesError && <p style={{ fontSize: 13, color: '#ff6b6b', marginBottom: 12 }}>{linesError}</p>}
                {!linesLoading && !linesError && (
                    <select
                        value={selectedLine}
                        onChange={e => setSelectedLine(e.target.value)}
                        style={inputStyle}
                    >
                        <option value="" disabled style={{ background: '#14141e', color: 'white' }}>
                            Linie auswählen
                        </option>
                        {Object.entries(lines).map(([id, name]) => (
                            <option key={id} value={id} style={{ background: '#14141e', color: 'white' }}>
                                {name}
                            </option>
                        ))}
                    </select>
                )}
                <p style={{ margin: '0 0 12px', fontSize: 13, opacity: 0.7 }}>Wähle einen Tag aus:</p>
                <DateInput value={selectedDate} onChange={setSelectedDate} />
                <button
                    onClick={handleCalculate}
                    disabled={!selectedDate}
                    style={calculateButtonStyle(!!selectedDate)}
                >
                    Tagesstatistik berechnen
                </button>
                {loading && <p style={{ marginTop: 16, opacity: 0.6, fontSize: 13 }}>Berechne...</p>}
                {error && <p style={{ marginTop: 16, fontSize: 13, color: '#ff6b6b' }}>{error}</p>}
            </>
        )
    }

    return (
        <>
            <BackButton onClick={handleBack} />
            <p style={{ margin: '0 0 16px', opacity: 0.5, fontSize: 12 }}>
                Tagesstatistik {lines[selectedLine]} – {selectedDate}
            </p>
            <StatGrid rows={[
                ['Ø Verspätung', result.average_delay, 'min'],
                ['Max. Verspätung', result.max_delay, 'min'],
                ['Verspätungsrate', formatRate(result.delay_rate), '%'],
                ['Ø Verspätung Morgen', result.morning_avg_delay, 'min'],
                ['Ø Verspätung Abend', result.evening_avg_delay, 'min'],
                ['Abfahrten Morgen', result.morning_departures, ''],
                ['Abfahrten Abend', result.evening_departures, ''],
                ['Abfahrten gesamt', result.total_departures, ''],
                ['Fahrten niedrige Auslastung', result.occupancy_occurance_l, ''],
                ['Fahrten mittlere Auslastung', result.occupancy_occurance_m, ''],
                ['Fahrten hohe Auslastung', result.occupancy_occurance_h, ''],
            ]} />
        </>
    )
}

export default DayLineStats