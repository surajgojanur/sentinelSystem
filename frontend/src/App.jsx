import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import WelcomePage from './pages/WelcomePage'
import ChatPage from './pages/ChatPage'
import PrivateChatPage from './pages/PrivateChatPage'
import DashboardPage from './pages/DashboardPage'
import QuestionBankPage from './pages/QuestionBankPage'
import FaceAttendancePage from './pages/FaceAttendancePage'
import FaceUnlockPage from './pages/FaceUnlockPage'
import GhostModePage from './pages/GhostModePage'
import AttackSimPage from './pages/AttackSimPage'
import WorkAssignmentsPage from './pages/WorkAssignmentsPage'
import MyWorkPage from './pages/MyWorkPage'

function ProtectedRoute({ children, adminOnly = false, managerOnly = false }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="flex h-full items-center justify-center bg-bg-900">
      <div className="flex gap-2">
        {[0, 1, 2].map(i => (
          <div key={i} className="typing-dot" style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.role !== 'admin') return <Navigate to="/chat" replace />
  if (managerOnly && !['admin', 'hr'].includes(user.role)) return <Navigate to="/my-work" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      {/* Public routes — redirect to welcome if already logged in */}
      <Route path="/login" element={user ? <Navigate to="/welcome" replace /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to="/welcome" replace /> : <RegisterPage />} />

      {/* Welcome splash — shown right after login */}
      <Route path="/welcome" element={
        <ProtectedRoute>
          <WelcomePage />
        </ProtectedRoute>
      } />
      <Route path="/face-unlock" element={
        <ProtectedRoute>
          <FaceUnlockPage />
        </ProtectedRoute>
      } />

      {/* App shell with sidebar */}
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/welcome" replace />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="messages" element={<PrivateChatPage />} />
        <Route path="attendance" element={<FaceAttendancePage />} />
        <Route path="my-work" element={<MyWorkPage />} />

        <Route path="work-assignments" element={
          <ProtectedRoute managerOnly>
            <WorkAssignmentsPage />
          </ProtectedRoute>
        } />

        <Route path="ghost-mode" element={
          <ProtectedRoute adminOnly>
            <GhostModePage />
          </ProtectedRoute>
        } />

        <Route path="attack-sim" element={
          <ProtectedRoute adminOnly>
            <AttackSimPage />
          </ProtectedRoute>
        } />

        <Route path="question-bank" element={
          <ProtectedRoute adminOnly>
            <QuestionBankPage />
          </ProtectedRoute>
        } />

        <Route path="dashboard" element={
          <ProtectedRoute adminOnly>
            <DashboardPage />
          </ProtectedRoute>
        } />
      </Route>

      <Route path="*" element={<Navigate to="/welcome" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <div className="noise">
        <AppRoutes />
      </div>
    </AuthProvider>
  )
}
