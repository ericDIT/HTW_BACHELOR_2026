import MenuButton from '../shared/Menu_button'
import BackButton from '../shared/Back_button'

function DayMenu({ onBack, onSelectStation, onSelectLine }) {
    return (
        <>
            <BackButton onClick={onBack} />
            <p style={{ margin: '0 0 12px', fontSize: 13, opacity: 0.7 }}>Welche Tagesstatistik?</p>
            <MenuButton onClick={onSelectStation}>
                Statistik für die Station
            </MenuButton>
            <MenuButton onClick={onSelectLine}>
                Statistik für eine Linie
            </MenuButton>
        </>
    )
}

export default DayMenu