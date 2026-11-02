import { statRowStyle } from './styles'

// rows is a list of [label, value, unit]
function StatGrid({ rows }) {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 24px' }}>
            {rows.map(([label, value, unit]) => (
                <div key={label} style={statRowStyle}>
                    <span style={{ opacity: 0.6, display: 'block', marginBottom: 2 }}>{label}</span>
                    <span style={{ color: '#aa3bff', fontWeight: 'bold' }}>
                        {value ?? '–'}{unit ? ' ' + unit : ''}
                    </span>
                </div>
            ))}
        </div>
    )
}

export default StatGrid