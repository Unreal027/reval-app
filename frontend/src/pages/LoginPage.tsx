import React, { useState } from 'react'

export default function LoginPage({ onLogin }: { onLogin: (phone: string, password: string) => Promise<void> }) {
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr(''); setLoading(true)
    try { await onLogin(phone.trim(), password) }
    catch (e: any) { setErr(e.message || '登录失败') }
    finally { setLoading(false) }
  }

  return (
    <div className="login-wrap">
      <div className="card">
        <h2>登录 ReVal</h2>
        <p className="muted">使用管理员或估价师账号登录（由 .env 首次迁移创建管理员）。</p>
        <form onSubmit={submit}>
          <div className="field">
            <label>手机号</label>
            <input value={phone} onChange={e=>setPhone(e.target.value)} placeholder="13800000000" required />
          </div>
          <div className="field">
            <label>密码</label>
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
          </div>
          {err && <div className="error">{err}</div>}
          <button type="submit" disabled={loading}>{loading ? '登录中...' : '登录'}</button>
        </form>
      </div>
    </div>
  )
}
