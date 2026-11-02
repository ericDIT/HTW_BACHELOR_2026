import MenuButton from '../shared/Menu_button'
import DelayTrendChart from '../shared/Delay_trend_chart'
import TransportTypeDelayChart from '../shared/Transporttype_delay_chart'
import { useDelayTrend } from '../hooks/Use_delay_trend'

function MainStationMenu({ onSelectDay, station }) {
    const { data, loading, error } = useDelayTrend(station.id)

    return (
        <div style={{ display: 'flex', gap: 20 }}>
            <div style={{ flex: '1 1 0', minWidth: 0 }}>
                {loading && <p style={{ fontSize: 13, opacity: 0.6 }}>Lade Diagramme...</p>}
                {error && <p style={{ fontSize: 13, color: '#ff6b6b' }}>{error}</p>}

                {!loading && !error && (
                    <>
                        <p style={{ margin: '0 0 8px', fontSize: 12, opacity: 0.7 }}>Ø Verspätung (30 Tage)</p>
                        <DelayTrendChart data={data} />

                        <p style={{ margin: '16px 0 8px', fontSize: 12, opacity: 0.7 }}>Bus vs. Bahn (30 Tage)</p>
                        <TransportTypeDelayChart data={data} />
                    </>
                )}
            </div>

            <div style={{ flex: '1 1 0', minWidth: 0 }}>
                <p style={{ margin: '0 0 12px', fontSize: 13, opacity: 0.7 }}>Was möchtest du berechnen?</p>
                <MenuButton onClick={onSelectDay}>
                    Statistiken für einen Tag
                </MenuButton>
                <MenuButton disabled>
                    Weitere Statistiken <span style={{ fontSize: 11 }}>(folgen)</span>
                </MenuButton>
            </div>
        </div>
    )
}

export default MainStationMenu