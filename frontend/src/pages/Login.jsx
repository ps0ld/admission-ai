import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api'

export default function Login({ setUser }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      setUser(res.data.user)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto mt-12">
      <div className="card">
        <h1 className="text-2xl font-bold mb-1">Welcome back</h1>
        <p className="text-slate-500 mb-6">Login to see your admission predictions</p>
        {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-xl mb-4">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input className="input" type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)} required />
          <input className="input" type="password" placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)} required />
          <button className="btn-primary w-full" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="text-sm text-slate-500 mt-4">
          No account? <Link to="/signup" className="text-brand-600 font-medium">Sign up</Link>
        </p>
        <p className="text-xs text-slate-400 mt-4">Demo admin: admin@admission-ai.com / Admin@123</p>
      </div>
    </div>
  )
}
