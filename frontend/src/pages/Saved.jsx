import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { getCompare, toggleCompare } from '../compare'

export default function Saved() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [compareIds, setCompareIds] = useState(getCompare())
  const [note, setNote] = useState('')

  useEffect(() => {
    api.get('/saved').then((res) => setItems(res.data)).finally(() => setLoading(false))
  }, [])

  const remove = async (id) => {
    await api.delete(`/saved/${id}`)
    setItems(items.filter((i) => i.college_id !== id))
  }

  const onCompare = (id) => {
    const { ids, error } = toggleCompare(id)
    setCompareIds(ids)
    setNote(error || '')
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Saved Colleges ❤️</h1>
        <Link to="/compare" className="btn-primary">Compare ({compareIds.length})</Link>
      </div>
      {note && <div className="bg-amber-50 text-amber-700 text-sm p-2 rounded-xl mb-3">{note}</div>}
      {loading ? <p className="text-slate-400">Loading...</p> : items.length === 0 ? (
        <p className="text-slate-400 text-sm">Abhi koi college save nahi kiya. <Link to="/colleges" className="text-brand-600">College Predictor</Link> se save karo.</p>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {items.map((c) => (
            <div key={c.college_id} className="card">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold">{c.name}</p>
                  <p className="text-sm text-slate-500">{c.branch} · {c.city}, {c.state} · {c.ownership}</p>
                </div>
                <button onClick={() => remove(c.college_id)} className="text-slate-400 hover:text-red-500" title="Remove">✕</button>
              </div>
              <p className="text-sm mt-3">Fees: ₹{Number(c.fees).toLocaleString()} · Last cutoff: {c.latest_cutoff?.toLocaleString() ?? '—'}</p>
              <label className="text-sm mt-3 flex items-center gap-2">
                <input type="checkbox" checked={compareIds.includes(c.college_id)} onChange={() => onCompare(c.college_id)} />
                Add to compare
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
