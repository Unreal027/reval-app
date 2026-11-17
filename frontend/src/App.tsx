import React, { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, Navigate, useNavigate } from 'react-router-dom'
import { api, clearTokens, getToken, setTokens, type User } from './api'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ComparablesPage from './pages/ComparablesPage'
import ValuationsPage from './pages/ValuationsPage'

function RequireAuth({ user, loading, children }: { user: User | null; loading: boolean; children: React.ReactNode }) {
  if (loading) return <div className="container"><div className="card">加载中...</div></div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  useEffect(() => {
    (async () => {
      if (!getToken()) { setLoading(false); return }
      try { setUser(await api.me()) } catch { clearTokens(); setUser(null) }
      setLoading(false)
    })()
  }, [])

  async function onLogin(phone: string, password: string) {
    const t = await api.login(phone, password)
    setTokens(t.access_token, t.refresh_token)
    const me = await api.me()
    setUser(me)
    nav('/')
  }
  function logout() { clearTokens(); setUser(null); nav('/login') }

  return (
    <div>
      {user && (
        <div className="nav">
          <div className="nav-inner">
            <Link to="/" style={{fontWeight:700,color:'#fff'}}>ReVal 估价系统</Link>
            <NavLink to="/" end>概览</NavLink>
            <NavLink to="/comparables">可比案例</NavLink>
            <NavLink to="/valuations">估价与报告</NavLink>
            <span className="spacer" />
            <span className="muted" style={{color:'#9ca3af'}}>{user.name || user.phone} ({user.role})</span>
            <button className="secondary" onClick={logout}>退出</button>
          </div>
        </div>
      )}
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage onLogin={onLogin} />} />
        <Route path="/" element={<RequireAuth user={user} loading={loading}><DashboardPage user={user!} /></RequireAuth>} />
        <Route path="/comparables" element={<RequireAuth user={user} loading={loading}><ComparablesPage user={user!} /></RequireAuth>} />
        <Route path="/valuations" element={<RequireAuth user={user} loading={loading}><ValuationsPage /></RequireAuth>} />
        <Route path="*" element={<Navigate to={user ? '/' : '/login'} replace />} />
      </Routes>
    </div>
  )
}
