import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
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

function ProtectedRoute({ children, adminOnly = false, allowWithoutFace = false }) {
  const { user, loading, faceVerified } = useAuth()
  const location = useLocation()
  if (loading) return (
    <div className="flex h-full items-center justify-center bg-bg-900">
      <div className="flex gap-2">
        {[0,1,2].map(i => (
          <div key={i} className="typing-dot" style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  if (!allowWithoutFace && !faceVerified) {
    return <Navigate to="/face-unlock" replace state={{ from: location.pathname }} />
  }
  if (adminOnly && user.role !== 'admin') return <Navigate to="/chat" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      {/* Public routes — redirect to welcome if already logged in */}
      <Route path="/login"    element={user ? <Navigate to="/welcome" replace /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to="/welcome" replace /> : <RegisterPage />} />

      {/* Welcome splash — shown right after login */}
      <Route path="/welcome" element={
        <ProtectedRoute>
          <WelcomePage />
        </ProtectedRoute>
      } />
      <Route path="/face-unlock" element={
        <ProtectedRoute allowWithoutFace>
          <FaceUnlockPage />
        </ProtectedRoute>
      } />

      {/* App shell with sidebar */}
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/welcome" replace />} />
        <Route path="chat"     element={<ChatPage />} />
        <Route path="messages" element={<PrivateChatPage />} />
        <Route path="attendance" element={<FaceAttendancePage />} />
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
