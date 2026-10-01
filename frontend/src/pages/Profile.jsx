import { useState, useEffect } from 'react'
import api from '../api'

const BRANCHES = ['CSE', 'IT', 'ECE', 'ME', 'CE']
const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS']
const STATES = ['UP', 'Delhi', 'MP', 'Bihar', 'Rajasthan', 'Maharashtra']

export default function Profile() {
  const [form, setForm] = useState({
    category: 'General', state: '', tenth_pct: '', twelfth_pct: '',
    diploma_pct: '', entrance_exam: '', entrance_rank: '',
    preferred_branch: '', preferred_state: '', budget_max: '',
  })
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/profile').then((res) => {
      const data = { ...res.data }
      Object.keys(data).forEach((k) => { if (data[k] === null) data[k] = '' })
      setForm((f) => ({ ...f, ...data }))
    }).finally(() => setLoading(false))
  }, [])

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaved(false)
    const payload = { ...form }
    ;['tenth_pct', 'twelfth_pct', 'diploma_pct', 'entrance_rank', 'budget_max'].forEach((k) => {
      payload[k] = payload[k] === '' ? null : Number(payload[k])
    })
    await api.put('/profile', payload)
    setSaved(true)
  }

  if (loading) return <p className="text-slate-500">Loading profile...</p>

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Your Academic Profile</h1>
      <form onSubmit={handleSubmit} className="card space-y-4">
        {saved && <div className="bg-green-50 text-green-700 text-sm p-3 rounded-xl">Profile saved ✓</div>}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-slate-600">Category</label>
            <select className="input" value={form.category} onChange={handleChange('category')}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-600">State</label>
            <select className="input" value={form.state} onChange={handleChange('state')}>
              <option value="">Select</option>
              {STATES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-slate-600">10th %</label>
            <input className="input" type="number" step="0.01" value={form.tenth_pct} onChange={handleChange('tenth_pct')} />
          </div>
          <div>
            <label className="text-sm text-slate-600">12th %</label>
            <input className="input" type="number" step="0.01" value={form.twelfth_pct} onChange={handleChange('twelfth_pct')} />
          </div>
          <div>
            <label className="text-sm text-slate-600">Diploma %</label>
            <input className="input" type="number" step="0.01" value={form.diploma_pct} onChange={handleChange('diploma_pct')} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-slate-600">Entrance Exam</label>
            <input className="input" placeholder="e.g. JEE Main" value={form.entrance_exam} onChange={handleChange('entrance_exam')} />
          </div>
          <div>
            <label className="text-sm text-slate-600">Entrance Rank</label>
            <input className="input" type="number" value={form.entrance_rank} onChange={handleChange('entrance_rank')} />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-slate-600">Preferred Branch</label>
            <select className="input" value={form.preferred_branch} onChange={handleChange('preferred_branch')}>
              <option value="">Select</option>
              {BRANCHES.map((b) => <option key={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-600">Preferred State</label>
            <select className="input" value={form.preferred_state} onChange={handleChange('preferred_state')}>
              <option value="">Select</option>
              {STATES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-600">Budget Max (₹)</label>
            <input className="input" type="number" value={form.budget_max} onChange={handleChange('budget_max')} />
          </div>
        </div>

        <button className="btn-primary">Save Profile</button>
      </form>
    </div>
  )
}
