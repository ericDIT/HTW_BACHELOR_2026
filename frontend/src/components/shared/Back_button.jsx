function BackButton({ onClick }) {
    return (
        <button
            onClick={onClick}
            style={{
                background: 'none', border: 'none', color: 'white',
                cursor: 'pointer', fontSize: 13, padding: 0,
                marginBottom: 16, display: 'flex', alignItems: 'center', gap: 6,
                opacity: 0.7
            }}
        >
            ← Zurück
        </button>
    )
}

export default BackButton