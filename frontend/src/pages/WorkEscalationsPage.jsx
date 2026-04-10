import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw } from 'lucide-react'

import api from '../utils/api'

const STATUS_STYLES = {
  open: 'text-danger border-danger/20 bg-danger/10',
  resolved: 'text-success border-success/20 bg-success/10',
}

export default function WorkEscalationsPage() {
  const [escalations, setEscalations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [resolvingId, setResolvingId] = useState(null)

  const loadEscalations = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/work/escalations')
      setEscalations(res.data.escalations || [])
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load escalations.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadEscalations()
  }, [loadEscalations])

  const resolveEscalation = async escalationId => {
    setResolvingId(escalationId)
    setError('')
    setSuccess('')
    try {
      const res = await api.patch(`/work/escalations/${escalationId}`, { status: 'resolved' })
      const updated = res.data.escalation
      setEscalations(prev => prev.map(item => (item.id === escalationId ? updated : item)))
      setSuccess('Escalation resolved.')
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to resolve escalation.')
    } finally {
      setResolvingId(null)
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full overflow-y-auto">
      <div className="px-6 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Work Escalations</h1>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5 tracking-widest uppercase">
              Review and resolve assignment escalations
            </p>
          </div>
          <button
            onClick={loadEscalations}
            className="px-3 py-2 rounded-lg glass-light border border-white/8 text-slate-300 hover:text-accent text-xs font-mono"
          >
            <RefreshCw size={13} className="inline mr-1.5" />
            Refresh
          </button>
        </div>

        {error && <p className="text-xs text-danger">{error}</p>}
        {success && <p className="text-xs text-success">{success}</p>}

        <div className="glass rounded-2xl border border-white/5 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle size={15} className="text-danger" />
              <p className="text-xs font-bold text-white">Escalations</p>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">{escalations.length} items</span>
          </div>
          <div className="max-h-[70vh] overflow-y-auto">
            {loading ? (
              <p className="text-xs text-slate-500 px-5 py-6">Loading escalations...</p>
            ) : !escalations.length ? (
              <p className="text-xs text-slate-500 px-5 py-6">No escalations yet.</p>
            ) : (
              escalations.map(item => (
                <div key={item.id} className="px-5 py-4 border-b border-white/5 last:border-b-0">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{item.assignment?.title || item.assignment_title}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        Created by {item.created_by_username} • {item.reason || 'No reason provided.'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${STATUS_STYLES[item.status] || STATUS_STYLES.open}`}>
                        {item.status}
                      </span>
                      {item.status === 'open' && (
                        <button
                          type="button"
                          onClick={() => resolveEscalation(item.id)}
                          disabled={resolvingId === item.id}
                          className="rounded-xl border border-success/30 bg-success/10 px-3 py-2 text-xs font-semibold text-success hover:bg-success/20 disabled:opacity-50"
                        >
                          {resolvingId === item.id ? 'Resolving...' : 'Resolve'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
