import { Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import Profile from './pages/Profile.jsx'
import Predict from './pages/Predict.jsx'
import Colleges from './pages/Colleges.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Admin from './pages/Admin.jsx'
import Saved from './pages/Saved.jsx'
import Compare from './pages/Compare.jsx'
import Chatbot from './components/Chatbot.jsx'

function useAuth() {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  })
  return { user, setUser }
}

function Protected({ user, children }) {
  if (!user) return <Navigate to="/login" replace />
  return children
}

function Nav({ user, onLogout }) {
  return (
    <nav className="bg-white border-b border-slate-200 px-6 py-4 flex flex-wrap gap-2 items-center justify-between">
      <Link to="/" className="font-bold text-brand-700 text-lg">🎓 Admission AI</Link>
      <div className="flex gap-4 items-center text-sm">
        {user ? (
          <>
            <Link to="/dashboard" className="hover:text-brand-600">Dashboard</Link>
            <Link to="/predict" className="hover:text-brand-600">Predict</Link>
            <Link to="/colleges" className="hover:text-brand-600">Colleges</Link>
            <Link to="/saved" className="hover:text-brand-600">Saved</Link>
            <Link to="/compare" className="hover:text-brand-600">Compare</Link>
            <Link to="/profile" className="hover:text-brand-600">Profile</Link>
            {user.role === 'admin' && <Link to="/admin" className="hover:text-brand-600">Admin</Link>}
            <button onClick={onLogout} className="btn-primary">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="hover:text-brand-600">Login</Link>
            <Link to="/signup" className="btn-primary">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  )
}

export default function App() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    navigate('/login')
  }

  return (
    <div className="min-h-screen">
      <Nav user={user} onLogout={handleLogout} />
      <main className="max-w-6xl mx-auto p-6">
        <Routes>
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="/signup" element={<Signup setUser={setUser} />} />
          <Route path="/dashboard" element={<Protected user={user}><Dashboard /></Protected>} />
          <Route path="/predict" element={<Protected user={user}><Predict /></Protected>} />
          <Route path="/colleges" element={<Protected user={user}><Colleges /></Protected>} />
          <Route path="/saved" element={<Protected user={user}><Saved /></Protected>} />
          <Route path="/compare" element={<Protected user={user}><Compare /></Protected>} />
          <Route path="/profile" element={<Protected user={user}><Profile /></Protected>} />
          <Route path="/admin" element={<Protected user={user}><Admin /></Protected>} />
        </Routes>
      </main>
      {user && <Chatbot />}
    </div>
  )
}
