import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertCircle, CheckCircle2, KeyRound, Search, UserPlus, XCircle } from 'lucide-react'

import api from '../utils/api'

const FALLBACK_ROLES = ['Admin', 'HR', 'Intern', 'Developer', 'Manager', 'Team Lead', 'Finance', 'Analyst', 'Security']

export default function AdminCreateUserPage() {
  const [roles, setRoles] = useState(FALLBACK_ROLES)
  const [form, setForm] = useState({ username: '', role: 'intern' })
  const [checkForm, setCheckForm] = useState({ username: '', login_code: '' })
  const [loading, setLoading] = useState(false)
  const [checkLoading, setCheckLoading] = useState(false)
  const [rolesLoading, setRolesLoading] = useState(true)
  const [error, setError] = useState('')
  const [checkError, setCheckError] = useState('')
  const [created, setCreated] = useState(null)
  const [checkResult, setCheckResult] = useState(null)

  useEffect(() => {
    let active = true

    api.get('/roles')
      .then(res => {
        if (!active) return
        const nextRoles = (res.data?.roles || []).map(role => role.name).filter(Boolean)
        if (nextRoles.length) {
          setRoles(nextRoles)
          setForm(current => {
            if (nextRoles.some(role => role.toLowerCase() === current.role)) return current
            const defaultRole = nextRoles.find(role => role.toLowerCase() === 'intern') || nextRoles[0]
            return { ...current, role: defaultRole.toLowerCase() }
          })
        }
      })
      .finally(() => {
        if (active) setRolesLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/admin/create-user', form)
      setCreated(res.data)
      setForm(current => ({ ...current, username: '' }))
    } catch (err) {
      setError(err.response?.data?.error || 'User creation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCodeCheck = async e => {
    e.preventDefault()
    setCheckLoading(true)
    setCheckError('')
    try {
      const res = await api.post('/admin/check-user-code', checkForm)
      setCheckResult(res.data)
    } catch (err) {
      setCheckResult(null)
      setCheckError(err.response?.data?.error || 'Code check failed')
    } finally {
      setCheckLoading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full overflow-y-auto">
      <div className="px-6 py-6 max-w-5xl space-y-6">
        <div>
          <h1 className="text-xl font-bold text-white">Admin User Access</h1>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5 tracking-widest uppercase">Create users, issue login codes, and verify employee codes</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="glass rounded-2xl p-6 border border-white/5 shadow-card">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
                <UserPlus size={18} />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Create User</h2>
                <p className="text-xs text-slate-500">Only admins can issue new accounts.</p>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm mb-4">
                <AlertCircle size={14} />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-1.5">Username</label>
                <input
                  type="text"
                  value={form.username}
                  onChange={e => setForm(current => ({ ...current, username: e.target.value }))}
                  className="w-full px-4 py-3 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-accent/50 transition-all text-sm font-mono"
                  placeholder="new_user"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-1.5">Role</label>
                <select
                  value={form.role}
                  onChange={e => setForm(current => ({ ...current, role: e.target.value }))}
                  disabled={rolesLoading}
                  className="w-full px-4 py-3 rounded-xl bg-bg-800 border border-white/8 text-white focus:outline-none focus:border-accent/50 transition-all text-sm disabled:opacity-60"
                >
                  {roles.map(role => (
                    <option key={role} value={role.toLowerCase()}>{role}</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={loading || rolesLoading}
                className="w-full py-3 rounded-xl bg-accent text-bg-900 font-bold text-sm tracking-wide hover:bg-accent-dim transition-all disabled:opacity-50 shadow-glow"
              >
                {loading ? 'Creating user...' : 'Create User'}
              </button>
            </form>
          </div>

          <div className="glass rounded-2xl p-6 border border-white/5 shadow-card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-purple-400/10 border border-purple-400/20 flex items-center justify-center text-purple-400">
                <KeyRound size={18} />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white">Issued Login Code</h2>
                <p className="text-xs text-slate-500">Share this once with the new user.</p>
              </div>
            </div>

            {created ? (
              <div className="space-y-4">
                <div className="rounded-xl bg-bg-800/80 border border-white/8 p-4">
                  <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">Username</p>
                  <p className="text-white font-semibold mt-1">{created.user.username}</p>
                </div>
                <div className="rounded-xl bg-accent/10 border border-accent/20 p-4">
                  <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">Employee Code / Password</p>
                  <p className="text-xl text-accent font-bold font-mono tracking-[0.25em] mt-2">{created.login_code}</p>
                </div>
                <p className="text-xs text-slate-500">The user will sign in with their username and this code only.</p>
              </div>
            ) : (
              <div className="rounded-xl bg-bg-800/70 border border-dashed border-white/10 p-5 text-sm text-slate-500">
                Create a user to generate and display their login code here.
              </div>
            )}
          </div>
        </div>

        <div className="glass rounded-2xl p-6 border border-white/5 shadow-card">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-warn/10 border border-warn/20 flex items-center justify-center text-warn">
              <Search size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Employee Code Check</h2>
              <p className="text-xs text-slate-500">Verify whether an employee code matches the stored code.</p>
            </div>
          </div>

          {checkError && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm mb-4">
              <AlertCircle size={14} />
              {checkError}
            </div>
          )}

          <form onSubmit={handleCodeCheck} className="grid gap-4 lg:grid-cols-[1fr_1fr_auto] items-end">
            <div>
              <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-1.5">Username</label>
              <input
                type="text"
                value={checkForm.username}
                onChange={e => setCheckForm(current => ({ ...current, username: e.target.value }))}
                className="w-full px-4 py-3 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-warn/50 transition-all text-sm font-mono"
                placeholder="employee_username"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-500 uppercase tracking-wider mb-1.5">Employee Code</label>
              <input
                type="text"
                value={checkForm.login_code}
                onChange={e => setCheckForm(current => ({ ...current, login_code: e.target.value.toUpperCase() }))}
                className="w-full px-4 py-3 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-warn/50 transition-all text-sm font-mono tracking-[0.2em]"
                placeholder="CODE123456"
                required
              />
            </div>

            <button
              type="submit"
              disabled={checkLoading}
              className="px-5 py-3 rounded-xl bg-warn text-bg-900 font-bold text-sm tracking-wide hover:brightness-105 transition-all disabled:opacity-50"
            >
              {checkLoading ? 'Checking...' : 'Check Code'}
            </button>
          </form>

          {checkResult && (
            <div className={`mt-5 rounded-2xl p-5 border ${checkResult.valid ? 'bg-success/10 border-success/20' : 'bg-danger/10 border-danger/20'}`}>
              <div className="flex items-center gap-2 mb-3">
                {checkResult.valid ? <CheckCircle2 size={18} className="text-success" /> : <XCircle size={18} className="text-danger" />}
                <p className={`text-sm font-bold ${checkResult.valid ? 'text-success' : 'text-danger'}`}>{checkResult.message}</p>
              </div>
              <div className="grid gap-3 md:grid-cols-3 text-sm">
                <div className="rounded-xl bg-bg-900/40 border border-white/8 p-3">
                  <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Username</p>
                  <p className="text-white mt-1">{checkResult.user.username}</p>
                </div>
                <div className="rounded-xl bg-bg-900/40 border border-white/8 p-3">
                  <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Role</p>
                  <p className="text-white mt-1 uppercase">{checkResult.user.role}</p>
                </div>
                <div className="rounded-xl bg-bg-900/40 border border-white/8 p-3">
                  <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Status</p>
                  <p className={`mt-1 font-semibold ${checkResult.valid ? 'text-success' : 'text-danger'}`}>{checkResult.valid ? 'Matched' : 'Not Matched'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
