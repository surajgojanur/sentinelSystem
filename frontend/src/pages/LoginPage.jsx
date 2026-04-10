import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const DEMO_CREDS = [
  { role: 'admin', username: 'admin', password: 'admin123', color: 'text-purple-400', bg: 'bg-purple-400/10 border-purple-400/20' },
  { role: 'hr', username: 'hr_jane', password: 'hr123', color: 'text-warn', bg: 'bg-warn/10 border-warn/20' },
  { role: 'intern', username: 'intern_bob', password: 'intern123', color: 'text-accent', bg: 'bg-accent/10 border-accent/20' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      toast.success('Welcome back!')
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (username, password) => {
    setForm({ username, password })
    setLoading(true)
    setError('')
    try {
      await login(username, password)
      toast.success('Signed in!')
    } catch {
      setError('Quick login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-900 grid-bg p-4">
      {/* Ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-accent/5 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent/10 border border-accent/30 mb-4 shadow-glow"
          >
            <Shield size={28} className="text-accent" />
          </motion.div>
          <h1 className="text-3xl font-bold text-white tracking-tight">SecureAI</h1>
          <p className="text-slate-500 mt-1 text-sm font-mono tracking-wider">ENTERPRISE GOVERNANCE PLATFORM</p>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl p-8 shadow-card">
          <h2 className="text-lg font-semibold text-white mb-6">Sign in to your account</h2>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm mb-4"
            >
              <AlertCircle size={14} />
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-1.5">Username</label>
              <input
                type="text"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                className="w-full px-4 py-3 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-accent/50 focus:shadow-glow transition-all text-sm font-mono"
                placeholder="your_username"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="w-full px-4 py-3 pr-10 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-accent/50 focus:shadow-glow transition-all text-sm font-mono"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-accent transition-colors"
                >
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-accent text-bg-900 font-bold text-sm tracking-wide hover:bg-accent-dim transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-glow"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </motion.button>
          </form>

          <p className="text-center text-slate-500 text-xs mt-4">
            No account?{' '}
            <Link to="/register" className="text-accent hover:underline">Create one</Link>
          </p>
        </div>

        {/* Demo credentials */}
        <div className="mt-6">
          <p className="text-center text-xs text-slate-600 font-mono uppercase tracking-wider mb-3">Quick Demo Access</p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_CREDS.map(({ role, username, password, color, bg }) => (
              <motion.button
                key={role}
                whileHover={{ scale: 1.03, y: -2 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => quickLogin(username, password)}
                disabled={loading}
                className={`p-3 rounded-xl border glass-light text-center cursor-pointer transition-all ${bg}`}
              >
                <p className={`text-xs font-bold uppercase tracking-wider ${color}`}>{role}</p>
                <p className="text-[10px] text-slate-500 font-mono mt-0.5">{username}</p>
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
