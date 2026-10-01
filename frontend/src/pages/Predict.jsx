import { useState } from 'react'
import api from '../api'

const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS']

function chanceColor(label) {
  if (label === 'High Chance') return 'text-green-600 bg-green-50'
  if (label === 'Moderate Chance') return 'text-amber-600 bg-amber-50'
  return 'text-red-600 bg-red-50'
}

export default function Predict() {
  const [form, setForm] = useState({ entrance_rank: '', category: 'General', tenth_pct: 75, twelfth_pct: 75 })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const res = await api.post('/predict', {
        ...form,
        entrance_rank: Number(form.entrance_rank),
        tenth_pct: Number(form.tenth_pct),
        twelfth_pct: Number(form.twelfth_pct),
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">AI Admission Prediction</h1>

      <form onSubmit={handleSubmit} className="card space-y-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-slate-600">Entrance Rank</label>
            <input className="input" type="number" required
              value={form.entrance_rank}
              onChange={(e) => setForm({ ...form, entrance_rank: e.target.value })} />
          </div>
          <div>
            <label className="text-sm text-slate-600">Category</label>
            <select className="input" value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-slate-600">10th %</label>
            <input className="input" type="number" step="0.1" value={form.tenth_pct}
              onChange={(e) => setForm({ ...form, tenth_pct: e.target.value })} />
          </div>
          <div>
            <label className="text-sm text-slate-600">12th %</label>
            <input className="input" type="number" step="0.1" value={form.twelfth_pct}
              onChange={(e) => setForm({ ...form, twelfth_pct: e.target.value })} />
          </div>
        </div>
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? 'Predicting...' : 'Predict Admission Chance'}
        </button>
      </form>

      {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-xl mb-4">{error}</div>}

      {result && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-slate-500 text-sm">Admission Probability</p>
              <p className="text-4xl font-bold">{Math.round(result.probability * 100)}%</p>
            </div>
            <span className={`px-4 py-2 rounded-full font-medium ${chanceColor(result.label)}`}>
              {result.label}
            </span>
          </div>

          <p className="text-slate-600 mb-4">{result.explanation_text}</p>

          <h3 className="font-semibold mb-2">Why this prediction?</h3>
          <div className="space-y-2">
            {result.factors.slice(0, 5).map((f, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-sm w-32 text-slate-600">{f.feature}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 ${f.direction === 'positive' ? 'bg-green-500' : 'bg-red-400'}`}
                    style={{ width: `${Math.min(100, Math.abs(f.impact) * 200)}%` }}
                  />
                </div>
                <span className="text-xs text-slate-400 w-16 text-right">
                  {f.direction === 'positive' ? '+' : '-'}{Math.abs(f.impact).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
