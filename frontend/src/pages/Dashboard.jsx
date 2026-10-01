import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import api from '../api'

export default function Dashboard() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/predict/history').then((res) => setHistory(res.data)).finally(() => setLoading(false))
  }, [])

  const chartData = [...history].reverse().map((h, i) => ({
    name: `#${i + 1}`,
    probability: Math.round(h.probability * 100),
  }))

  const avgChance = history.length
    ? Math.round((history.reduce((s, h) => s + h.probability, 0) / history.length) * 100)
    : 0

  const [downloading, setDownloading] = useState(false)
  const downloadReport = async () => {
    setDownloading(true)
    try {
      const res = await api.get('/report/pdf', { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'admission-report.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your Dashboard</h1>
        <button className="btn-primary" onClick={downloadReport} disabled={downloading}>
          {downloading ? 'Generating...' : '📄 Download PDF Report'}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card">
          <p className="text-slate-500 text-sm">Predictions Made</p>
          <p className="text-2xl font-bold">{history.length}</p>
        </div>
        <div className="card">
          <p className="text-slate-500 text-sm">Average Chance</p>
          <p className="text-2xl font-bold">{avgChance}%</p>
        </div>
        <div className="card">
          <p className="text-slate-500 text-sm">Best Prediction</p>
          <p className="text-2xl font-bold">
            {history.length ? Math.round(Math.max(...history.map((h) => h.probability)) * 100) + '%' : '—'}
          </p>
        </div>
        <div className="card">
          <p className="text-slate-500 text-sm">Latest Result</p>
          <p className="text-2xl font-bold">{history[0]?.label || '—'}</p>
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-4">Prediction Trend</h2>
        {loading ? (
          <p className="text-slate-400 text-sm">Loading...</p>
        ) : chartData.length === 0 ? (
          <p className="text-slate-400 text-sm">Make your first prediction to see your trend here.</p>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="probability" stroke="#4f46e5" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
