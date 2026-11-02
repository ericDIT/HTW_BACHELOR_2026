export function formatRate(val) {
    const pct = val * 100
    return pct % 1 === 0 ? pct.toFixed(0) : pct.toFixed(1)
}