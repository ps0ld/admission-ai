import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { getCompare, toggleCompare } from '../compare'

const BRANCHES = ['', 'CSE', 'IT', 'ECE', 'ME', 'CE']
const STATES = ['', 'UP', 'Delhi', 'MP', 'Bihar', 'Rajasthan', 'Maharashtra']
const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS']

const bucketStyle = {
  Safe: 'bg-green-50 text-green-700',
  Target: 'bg-amber-50 text-amber-700',
  Reach: 'bg-red-50 text-red-700',
}

export default function Colleges() {
  const [filters, setFilters] = useState({ rank: '', category: 'General', branch: '', state: '' })
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [savedIds, setSavedIds] = useState([])
  const [compareIds, setCompareIds] = useState(getCompare())
  const [note, setNote] = useState('')

  useEffect(() => {
    api.get('/saved').then((res) => setSavedIds(res.data.map((c) => c.college_id))).catch(() => {})
  }, [])

  const handleSearch = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const params = { rank: Number(filters.rank), category: filters.category }
      if (filters.branch) params.branch = filters.branch
      if (filters.state) params.state = filters.state
      const res = await api.get('/colleges/predictor', { params })
      setMatches(res.data)
    } finally {
      setLoading(false)
    }
  }

  const toggleSave = async (id) => {
    if (savedIds.includes(id)) {
      await api.delete(`/saved/${id}`)
      setSavedIds(savedIds.filter((i) => i !== id))
    } else {
      await api.post(`/saved/${id}`)
      setSavedIds([...savedIds, id])
    }
  }

  const onCompare = (id) => {
    const { ids, error } = toggleCompare(id)
    setCompareIds(ids)
    setNote(error || '')
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">College Predictor & Recommendations</h1>
        <Link to="/compare" className="btn-primary">Compare ({compareIds.length})</Link>
      </div>

      <form onSubmit={handleSearch} className="card mb-6 grid grid-cols-2 md:grid-cols-4 gap-4 items-end">
        <div>
          <label className="text-sm text-slate-600">Your Rank</label>
          <input className="input" type="number" required value={filters.rank}
            onChange={(e) => setFilters({ ...filters, rank: e.target.value })} />
        </div>
        <div>
          <label className="text-sm text-slate-600">Category</label>
          <select className="input" value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-sm text-slate-600">Branch</label>
          <select className="input" value={filters.branch}
            onChange={(e) => setFilters({ ...filters, branch: e.target.value })}>
            {BRANCHES.map((b) => <option key={b} value={b}>{b || 'Any'}</option>)}
          </select>
        </div>
        <div>
          <label className="text-sm text-slate-600">State</label>
          <select className="input" value={filters.state}
            onChange={(e) => setFilters({ ...filters, state: e.target.value })}>
            {STATES.map((s) => <option key={s} value={s}>{s || 'Any'}</option>)}
          </select>
        </div>
        <button className="btn-primary col-span-2 md:col-span-4" disabled={loading}>
          {loading ? 'Searching...' : 'Find Matching Colleges'}
        </button>
      </form>

      {note && <div className="bg-amber-50 text-amber-700 text-sm p-2 rounded-xl mb-3">{note}</div>}

      {matches.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b">
                <th className="py-2">College</th><th>Branch</th><th>Est. Chance</th>
                <th>Previous Cutoff</th><th>Bucket</th><th>Save</th><th>Compare</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m) => (
                <tr key={m.college_id} className="border-b last:border-0">
                  <td className="py-2 font-medium">{m.name}</td>
                  <td>{m.branch}</td>
                  <td>{Math.round(m.estimated_chance * 100)}%</td>
                  <td>{m.previous_cutoff.toLocaleString()}</td>
                  <td>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${bucketStyle[m.category_bucket]}`}>
                      {m.category_bucket}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => toggleSave(m.college_id)} className="text-lg"
                      title={savedIds.includes(m.college_id) ? 'Remove from saved' : 'Save college'}>
                      {savedIds.includes(m.college_id) ? '❤️' : '🤍'}
                    </button>
                  </td>
                  <td>
                    <input type="checkbox" checked={compareIds.includes(m.college_id)}
                      onChange={() => onCompare(m.college_id)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {matches.length === 0 && !loading && (
        <p className="text-slate-400 text-sm">Enter your rank to see matching colleges, split into Safe / Target / Reach choices.</p>
      )}
    </div>
  )
}
