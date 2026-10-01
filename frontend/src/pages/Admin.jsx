import { useEffect, useState } from 'react'
import api from '../api'

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [collegeForm, setCollegeForm] = useState({ name: '', branch: 'CSE', state: 'UP', city: '', ownership: 'Government', fees: 0, exam: 'JEE' })
  const [file, setFile] = useState(null)
  const [uploadMsg, setUploadMsg] = useState('')
  const [trainResult, setTrainResult] = useState(null)
  const [training, setTraining] = useState(false)
  const [message, setMessage] = useState('')

  const loadStats = () => api.get('/admin/stats').then((res) => setStats(res.data)).catch(() => {})

  useEffect(() => { loadStats() }, [])

  const addCollege = async (e) => {
    e.preventDefault()
    await api.post('/admin/colleges', collegeForm)
    setMessage('College added ✓')
    loadStats()
  }

  const uploadDataset = async (e) => {
    e.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/admin/dataset/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setUploadMsg(`Uploaded: ${res.data.rows} rows validated ✓`)
    } catch (err) {
      setUploadMsg(err.response?.data?.detail || 'Upload failed')
    }
  }

  const trainModel = async () => {
    setTraining(true)
    setTrainResult(null)
    try {
      const res = await api.post('/admin/model/train')
      setTrainResult(res.data)
      loadStats()
    } catch (err) {
      setUploadMsg(err.response?.data?.detail || 'Training failed')
    } finally {
      setTraining(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Admin Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card"><p className="text-slate-500 text-sm">Total Students</p><p className="text-2xl font-bold">{stats?.total_users ?? '—'}</p></div>
        <div className="card"><p className="text-slate-500 text-sm">Predictions Made</p><p className="text-2xl font-bold">{stats?.total_predictions ?? '—'}</p></div>
        <div className="card"><p className="text-slate-500 text-sm">Colleges</p><p className="text-2xl font-bold">{stats?.total_colleges ?? '—'}</p></div>
        <div className="card"><p className="text-slate-500 text-sm">Active Model</p><p className="text-lg font-bold">{stats?.active_model?.algorithm ?? 'Not trained'}</p></div>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-4">Add College</h2>
        {message && <div className="bg-green-50 text-green-700 text-sm p-2 rounded-xl mb-3">{message}</div>}
        <form onSubmit={addCollege} className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <input className="input" placeholder="Name" value={collegeForm.name}
            onChange={(e) => setCollegeForm({ ...collegeForm, name: e.target.value })} required />
          <input className="input" placeholder="Branch" value={collegeForm.branch}
            onChange={(e) => setCollegeForm({ ...collegeForm, branch: e.target.value })} />
          <input className="input" placeholder="State" value={collegeForm.state}
            onChange={(e) => setCollegeForm({ ...collegeForm, state: e.target.value })} />
          <input className="input" placeholder="City" value={collegeForm.city}
            onChange={(e) => setCollegeForm({ ...collegeForm, city: e.target.value })} />
          <select className="input" value={collegeForm.ownership}
            onChange={(e) => setCollegeForm({ ...collegeForm, ownership: e.target.value })}>
            <option>Government</option><option>Private</option>
          </select>
          <input className="input" type="number" placeholder="Fees" value={collegeForm.fees}
            onChange={(e) => setCollegeForm({ ...collegeForm, fees: Number(e.target.value) })} />
          <input className="input" placeholder="Exam" value={collegeForm.exam}
            onChange={(e) => setCollegeForm({ ...collegeForm, exam: e.target.value })} />
          <button className="btn-primary">Add College</button>
        </form>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-4">Dataset Management</h2>
        <p className="text-sm text-slate-500 mb-3">
          CSV columns required: student_score, entrance_rank, category, state, college, branch, cutoff, year, admitted
        </p>
        <form onSubmit={uploadDataset} className="flex gap-3 items-center">
          <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} />
          <button className="btn-primary">Upload & Validate</button>
        </form>
        {uploadMsg && <p className="text-sm mt-2 text-slate-600">{uploadMsg}</p>}
      </div>

      <div className="card">
        <h2 className="font-semibold mb-4">Model Training</h2>
        <button className="btn-primary" onClick={trainModel} disabled={training}>
          {training ? 'Training (this can take a minute)...' : 'Train Model'}
        </button>
        {trainResult && (
          <div className="mt-4 text-sm">
            <p className="font-medium mb-2">Selected: {trainResult.selected_model}</p>
            <table className="w-full text-xs">
              <thead><tr className="text-left text-slate-500"><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th></tr></thead>
              <tbody>
                {Object.entries(trainResult.all_results).map(([name, m]) => (
                  <tr key={name} className="border-t">
                    <td className="py-1">{name}</td>
                    <td>{m.accuracy}</td><td>{m.precision}</td><td>{m.recall}</td><td>{m.f1}</td><td>{m.roc_auc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
