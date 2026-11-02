import { menuButtonStyle } from "./styles"

function MenuButton({ onClick, disabled, children }) {
    return (
        <button
            style={disabled ? { ...menuButtonStyle, opacity: 0.4, cursor: 'not-allowed' } : menuButtonStyle}
            onClick={onClick}
            disabled={disabled}
        >
            {children}
        </button>
    )
}

export default MenuButton