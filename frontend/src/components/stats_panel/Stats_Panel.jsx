import { useState, useRef, useLayoutEffect } from 'react'
import MainStationMenu from '../views/Main_menu'
import DayMenu from '../views/Day_menu'
import DayStationStats from '../views/Day_Station_stats'
import DayLineStats from '../views/Day_Line_stats'
import PeriodStationStats from '../views/Period_Station_stats'

const VIEWS = {
    MENU: 'menu',
    DAY_MENU: 'day_menu',
    DAY_STATION: 'day_station',
    DAY_LINE: 'day_line',
    PERIOD_STATION: 'period_station',
}

const PANEL_TOP = 60
const PANEL_BOTTOM_MARGIN = 24
const BASE_WIDTH = 800        
const RESULT_WIDTH = 520
const WIDE_EXTRA_WIDTH = 340 // zusätzliche Breite pro weiterer Spalte

function StatsPanel({ station, onClose }) {
    const [view, setView] = useState(VIEWS.MENU)
    const [hasResult, setHasResult] = useState(false)
    const [isWide, setIsWide] = useState(false)

    const contentRef = useRef(null)

    // misst, ob der Inhalt höher ist als der verfügbare Platz bis zum Bildschirmrand
    useLayoutEffect(() => {
        const el = contentRef.current
        if (!el) return

        const checkOverflow = () => {
            const maxHeight = window.innerHeight - PANEL_TOP - PANEL_BOTTOM_MARGIN
            // scrollHeight misst die tatsächliche Inhaltshöhe, unabhängig vom aktuellen Spalten-Layout
            const singleColumnHeight = el.scrollWidth > 0
                ? el.scrollHeight * (isWide ? 1 : 1) // Platzhalter, echte Messung unten
                : 0
            setIsWide(el.scrollHeight > maxHeight || el.scrollWidth > el.clientWidth)
        }

        checkOverflow()

        const resizeObserver = new ResizeObserver(checkOverflow)
        resizeObserver.observe(el)

        window.addEventListener('resize', checkOverflow)

        return () => {
            resizeObserver.disconnect()
            window.removeEventListener('resize', checkOverflow)
        }
    }, [view, hasResult])

    const goTo = (target) => {
        setHasResult(false)
        setView(target)
    }

    const baseWidth = hasResult ? RESULT_WIDTH : BASE_WIDTH
    const panelWidth = isWide ? baseWidth + WIDE_EXTRA_WIDTH : baseWidth
    const maxContentHeight = `calc(100vh - ${PANEL_TOP + PANEL_BOTTOM_MARGIN + 80}px)` // 80px ca. für Header/Padding

    return (
        <div style={{
            position: 'absolute',
            top: PANEL_TOP,
            right: 16,
            width: panelWidth,
            maxHeight: `calc(100vh - ${PANEL_TOP + PANEL_BOTTOM_MARGIN}px)`,
            background: 'rgba(20, 20, 30, 0.92)',
            borderRadius: 12,
            padding: 16,
            color: 'white',
            pointerEvents: 'auto',
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
            backdropFilter: 'blur(8px)',
            transition: 'width 0.3s ease',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexShrink: 0 }}>
                <h3 style={{ margin: 0, fontSize: 16 }}>{station.name} – Statistiken</h3>
                <button onClick={onClose} style={{
                    background: 'none', border: 'none', color: 'white',
                    cursor: 'pointer', fontSize: 18, lineHeight: 1
                }}>✕</button>
            </div>

            <div
                ref={contentRef}
                style={{
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    paddingTop: 16,
                    maxHeight: maxContentHeight,
                    overflowY: isWide ? 'hidden' : 'auto',
                    columnWidth: isWide ? '300px' : 'auto',
                    columnGap: 24,
                }}
            >

                {view === VIEWS.MENU && (
                    <MainStationMenu onSelectDay={() => goTo(VIEWS.DAY_MENU)} station={station} />
                )}

                {view === VIEWS.DAY_MENU && (
                    <DayMenu
                        onBack={() => goTo(VIEWS.MENU)}
                        onSelectStation={() => goTo(VIEWS.DAY_STATION)}
                        onSelectLine={() => goTo(VIEWS.DAY_LINE)}
                    />
                )}

                {view === VIEWS.DAY_STATION && (
                    <DayStationStats
                        station={station}
                        onBack={() => goTo(VIEWS.DAY_MENU)}
                        onResult={setHasResult}
                    />
                )}

                {view === VIEWS.DAY_LINE && (
                    <DayLineStats
                        station={station}
                        onBack={() => goTo(VIEWS.DAY_MENU)}
                        onResult={setHasResult}
                    />
                )}

                {view === VIEWS.PERIOD_STATION && (
                    <PeriodStationStats
                        station={station}
                        onBack={() => goTo(VIEWS.DAY_MENU)}
                        onResult={setHasResult}
                    />
                )}

            </div>
        </div>
    )
}

export default StatsPanel