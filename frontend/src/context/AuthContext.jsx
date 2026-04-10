import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [faceVerified, setFaceVerified] = useState(() => sessionStorage.getItem('face_verified') === '1')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      api.get('/auth/me')
        .then(res => setUser(res.data.user))
        .catch(() => { setToken(null); localStorage.removeItem('token') })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = useCallback(async (username, loginCode) => {
    const res = await api.post('/auth/login', { username, login_code: loginCode })
    const { token: t, user: u } = res.data
    localStorage.setItem('token', t)
    sessionStorage.removeItem('face_verified')
    api.defaults.headers.common['Authorization'] = `Bearer ${t}`
    setToken(t)
    setUser(u)
    setFaceVerified(false)
    return u
  }, [])

  const markFaceVerified = useCallback(() => {
    sessionStorage.setItem('face_verified', '1')
    setFaceVerified(true)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    sessionStorage.removeItem('face_verified')
    delete api.defaults.headers.common['Authorization']
    setToken(null)
    setUser(null)
    setFaceVerified(false)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, faceVerified, markFaceVerified, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
