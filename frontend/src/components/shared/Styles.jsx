export const menuButtonStyle = {
    width: '100%',
    padding: '10px 14px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 8,
    color: 'white',
    cursor: 'pointer',
    fontSize: 13,
    textAlign: 'left',
    marginBottom: 8,
}

export const inputStyle = {
    width: '100%',
    padding: '8px 10px',
    background: 'rgba(255,255,255,0.07)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: 8,
    color: 'white',
    fontSize: 13,
    boxSizing: 'border-box',
    marginBottom: 12,
}

export const calculateButtonStyle = (enabled) => ({
    width: '100%',
    padding: '8px 0',
    background: enabled ? 'rgba(170, 59, 255, 0.2)' : 'rgba(255,255,255,0.05)',
    border: `1px solid ${enabled ? 'rgba(170, 59, 255, 0.5)' : 'rgba(255,255,255,0.1)'}`,
    borderRadius: 8,
    color: enabled ? 'white' : 'rgba(255,255,255,0.3)',
    cursor: enabled ? 'pointer' : 'not-allowed',
    fontSize: 13,
})

export const statRowStyle = {
    borderTop: '1px solid rgba(255,255,255,0.07)',
    paddingTop: 8,
    marginTop: 8,
    fontSize: 13,
}