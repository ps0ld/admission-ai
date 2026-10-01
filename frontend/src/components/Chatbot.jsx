import { useState, useRef, useEffect } from 'react'
import api from '../api'

const SUGGESTIONS = [
  'Mere 68k rank hai, UP se hu aur CSE chahiye',
  'Colleges suggest karo',
  'Why this prediction?',
]

const bucketStyle = { Safe: 'bg-green-100 text-green-700', Target: 'bg-amber-100 text-amber-700', Reach: 'bg-red-100 text-red-700' }

export default function Chatbot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Namaste! Main Admission AI counsellor hoon. Apna rank, state aur branch batao.' },
  ])
  const [input, setInput] = useState('')
  const [context, setContext] = useState({})
  const [sending, setSending] = useState(false)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, open])

  const send = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || sending) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: msg }])
    setSending(true)
    try {
      const res = await api.post('/chatbot', { message: msg, context })
      setContext(res.data.context || {})
      setMessages((m) => [...m, { role: 'bot', text: res.data.reply, colleges: res.data.colleges }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'bot', text: err.response?.data?.detail || 'Kuch gadbad ho gayi, dobara try karo.' }])
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <button onClick={() => setOpen(!open)}
        className="fixed bottom-5 right-5 z-50 bg-brand-600 hover:bg-brand-700 text-white rounded-full px-5 py-3 shadow-lg font-medium">
        {open ? '✕ Close' : '🤖 Ask Admission AI'}
      </button>

      {open && (
        <div className="fixed bottom-20 right-5 z-50 w-[92vw] max-w-sm h-[70vh] max-h-[560px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col">
          <div className="px-4 py-3 border-b bg-brand-600 text-white rounded-t-2xl">
            <p className="font-semibold">Admission AI Counsellor</p>
            <p className="text-xs opacity-80">Estimates only, guarantee nahi</p>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm">
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 whitespace-pre-wrap ${m.role === 'user' ? 'bg-brand-600 text-white' : 'bg-slate-100'}`}>
                  {m.text}
                  {m.colleges?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {m.colleges.map((c) => (
                        <div key={c.college_id} className="bg-white rounded-lg px-2 py-1 text-slate-800 flex justify-between gap-2">
                          <span>{c.name} ({c.branch})</span>
                          <span className={`text-xs px-2 rounded-full ${bucketStyle[c.category_bucket]}`}>{c.category_bucket}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && <p className="text-slate-400 text-xs">Soch raha hoon...</p>}
            <div ref={endRef} />
          </div>

          <div className="px-3 pb-1 flex gap-1 flex-wrap">
            {messages.length < 3 && SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)} className="text-xs bg-brand-50 text-brand-700 rounded-full px-2 py-1">{s}</button>
            ))}
          </div>

          <div className="p-3 border-t flex gap-2">
            <input className="input" placeholder="Apna sawaal likho..." value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()} />
            <button className="btn-primary" onClick={() => send()} disabled={sending}>Send</button>
          </div>
        </div>
      )}
    </>
  )
}
