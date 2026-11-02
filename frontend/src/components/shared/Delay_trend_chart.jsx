import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function DelayTrendChart({ data }) {
    return (
        <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="fact_date" tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.6)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.6)' }} />
                <Tooltip />
                <Line type="monotone" dataKey="average_delay" stroke="#aa3bff" strokeWidth={2} dot={false} name="Ø Verspätung" />
            </LineChart>
        </ResponsiveContainer>
    )
}

export default DelayTrendChart