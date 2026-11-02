import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function TransportTypeDelayChart({ data }) {
    return (
        <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="fact_date" tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.6)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.6)' }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="avg_bus_delay" stroke="#3bff9b" strokeWidth={2} dot={false} name="Bus" />
                <Line type="monotone" dataKey="avg_train_delay" stroke="#ffcc3b" strokeWidth={2} dot={false} name="Bahn" />
            </LineChart>
        </ResponsiveContainer>
    )
}

export default TransportTypeDelayChart