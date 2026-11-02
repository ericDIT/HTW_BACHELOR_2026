import { inputStyle } from './styles'

function DateInput({ value, onChange }) {
    return (
        <input
            type="date"
            value={value}
            onChange={e => onChange(e.target.value)}
            style={inputStyle}
        />
    )
}

export default DateInput