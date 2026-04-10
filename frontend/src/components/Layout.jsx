import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import {
  MessageSquare, LayoutDashboard,
  LogOut, Shield, ChevronRight, Cpu, Database, ScanFace, UserPlus
} from 'lucide-react'

const ROLE_COLORS = {
  admin: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
  hr: 'text-warn bg-warn/10 border-warn/20',
  intern: 'text-accent bg-accent/10 border-accent/20',
}

const ROLE_BADGE = {
  admin: '⬡ ADMIN',
  hr: '◈ HR',
  intern: '◎ INTERN',
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const navItems = [
    { to: '/chat', icon: Cpu, label: 'AI Chatbot', desc: 'Governed AI' },
    { to: '/messages', icon: MessageSquare, label: 'Secure Msg', desc: 'Private comms' },
    { to: '/attendance', icon: ScanFace, label: 'Attendance', desc: 'Face check-in/out' },
    ...(user?.role === 'admin'
      ? [
          { to: '/user-access', icon: UserPlus, label: 'User Access', desc: 'Create accounts' },
          { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', desc: 'Audit & analytics' },
          { to: '/question-bank', icon: Database, label: 'Question Bank', desc: 'Dataset ops' },
          { to: '/ghost-mode', icon: Shield, label: 'Ghost Mode', desc: 'Stealth monitoring' },
          { to: '/attack-sim', icon: Shield, label: 'Attack Simulator', desc: 'Security testing' },
        ]
      : []),
  ]

  return (
    <div className="flex h-screen overflow-hidden bg-bg-900 grid-bg">
      <motion.aside
        initial={{ x: -80, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="w-64 flex flex-col glass border-r border-white/5 z-20"
      >
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center">
                <Shield size={18} className="text-accent" />
              </div>
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-success border-2 border-bg-900" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-widest text-white uppercase">SecureAI</h1>
              <p className="text-[10px] text-slate-500 tracking-wider font-mono">GOVERNANCE PLATFORM</p>
            </div>
          </div>
        </div>

        <div className="p-4 border-b border-white/5">
          <div className="glass-light rounded-xl p-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent/30 to-purple/30 border border-accent/20 flex items-center justify-center text-xs font-bold text-accent">
                {user?.username?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">{user?.username}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
              </div>
            </div>
            <div className="mt-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${ROLE_COLORS[user?.role] || 'text-slate-300 bg-white/5 border-white/10'}`}>
                {ROLE_BADGE[user?.role] || user?.role?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label, desc }) => (
            <NavLink key={to} to={to}>
              {({ isActive }) => (
                <motion.div
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200 group ${
                    isActive
                      ? 'bg-accent/10 border border-accent/20'
                      : 'hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                    isActive ? 'bg-accent/20 text-accent' : 'bg-white/5 text-slate-400 group-hover:text-accent group-hover:bg-accent/10'
                  }`}>
                    <Icon size={15} />
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm font-semibold ${isActive ? 'text-accent' : 'text-slate-300'}`}>{label}</p>
                    <p className="text-[11px] text-slate-600">{desc}</p>
                  </div>
                  {isActive && <ChevronRight size={13} className="text-accent/60" />}
                </motion.div>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-white/5">
          <motion.button
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => { logout(); navigate('/login') }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-danger/10 border border-transparent hover:border-danger/20 transition-all duration-200 group"
          >
            <div className="w-8 h-8 rounded-lg bg-white/5 group-hover:bg-danger/20 flex items-center justify-center transition-colors">
              <LogOut size={14} className="text-slate-400 group-hover:text-danger" />
            </div>
            <span className="text-sm text-slate-400 group-hover:text-danger transition-colors font-medium">Sign out</span>
          </motion.button>
        </div>
      </motion.aside>

      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <Outlet />
        </AnimatePresence>
      </main>
    </div>
  )
}
