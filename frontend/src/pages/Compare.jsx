import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts'
import api from '../api'
import { getCompare, setCompare } from '../compare'

const COLORS = ['#4f46e5', '#059669', '#d97706', '#dc2626']

export default function Compare() {
  const [ids, setIds] = useState(getCompare())
  const [colleges, setColleges] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (ids.length === 0) { setColleges([]); return }
    setLoading(true)
    api.get('/colleges/compare', { params: { ids: ids.join(',') } })
      .then((res) => setColleges(res.data)).finally(() => setLoading(false))
  }, [ids])

  const remove = (id) => {
    const next = ids.filter((i) => i !== id)
    setCompare(next)
    setIds(next)
  }

  const years = [...new Set(colleges.flatMap((c) => c.trend.map((t) => t.year)))].sort()
  const chartData = years.map((y) => {
    const row = { year: y }
    colleges.forEach((c, i) => {
      const t = c.trend.find((x) => x.year === y)
      if (t) row[`c${i}`] = t.closing_rank
    })
    return row
  })

  const minFees = colleges.length ? Math.min(...colleges.map((c) => c.fees)) : null
  const rows = [
    ['Branch', (c) => c.branch],
    ['State', (c) => c.state],
    ['City', (c) => c.city || '—'],
    ['Type', (c) => c.ownership],
    ['Entrance exam', (c) => c.exam],
    ['Fees', (c) => <span className={c.fees === minFees && colleges.length > 1 ? 'text-green-600 font-semibold' : ''}>₹{Number(c.fees).toLocaleString()}</span>],
    ['Latest closing rank', (c) => c.latest_cutoff?.toLocaleString() ?? '—'],
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Compare Colleges</h1>
      {ids.length === 0 ? (
        <p className="text-slate-400 text-sm">Koi college select nahi hai. <Link to="/colleges" className="text-brand-600">College Predictor</Link> ya <Link to="/saved" className="text-brand-600">Saved</Link> page se "Compare" tick karo (max 4).</p>
      ) : loading ? <p className="text-slate-400">Loading...</p> : (
        <div className="space-y-6">
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2 w-40"></th>
                  {colleges.map((c, i) => (
                    <th key={c.id} className="py-2 pr-4">
                      <div className="flex items-start justify-between gap-2">
                        <span style={{ color: COLORS[i] }}>{c.name}</span>
                        <button onClick={() => remove(c.id)} className="text-slate-400 hover:text-red-500">✕</button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(([label, fn]) => (
                  <tr key={label} className="border-b last:border-0">
                    <td className="py-2 text-slate-500">{label}</td>
                    {colleges.map((c) => <td key={c.id} className="pr-4">{fn(c)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-slate-400 mt-2">Green = lowest fees. Lower closing rank = tougher to get in.</p>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-4">Cutoff Trend (closing rank by year)</h2>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend formatter={(v) => colleges[Number(v.slice(1))]?.name + ' (' + colleges[Number(v.slice(1))]?.branch + ')'} />
                {colleges.map((c, i) => (
                  <Line key={c.id} type="monotone" dataKey={`c${i}`} stroke={COLORS[i]} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
