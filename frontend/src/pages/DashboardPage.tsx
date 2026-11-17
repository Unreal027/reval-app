import React, { useState } from 'react'
import { api, type User } from '../api'

export default function DashboardPage({ user }: { user: User }) {
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function seed() {
    setMsg(''); setErr(''); setLoading(true)
    try {
      const r = await api.seedFactors()
      setMsg(`系数配置已就绪，共 ${r.total ?? (r.items?.length ?? 0)} 条。`)
    } catch (e: any) { setErr(e.message || '操作失败') }
    finally { setLoading(false) }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>系统概览</h2>
        <p>当前用户：<b>{user.name || user.phone}</b>（{user.role}）</p>
        <p className="muted">已实现：认证、可比案例 CRUD/半径检索/Excel 导入、比较法(系数可配置)/收益法/成本法估价任务、Docx 报告生成与下载。</p>
        <div className="actions">
          <button onClick={seed} disabled={loading || user.role !== 'admin'}>初始化默认比较法系数</button>
          <a href="/api/docs" target="_blank" rel="noreferrer"><button className="secondary">打开 API 文档</button></a>
        </div>
        {user.role !== 'admin' && <div className="muted">提示：初始化系数需管理员权限。</div>}
        {msg && <div className="success">{msg}</div>}
        {err && <div className="error">{err}</div>}
      </div>
      <div className="card">
        <h3>快速流程</h3>
        <ol>
          <li>管理员首次使用可点击“初始化默认比较法系数”。</li>
          <li>在“可比案例”页录入或导入案例（.xlsx）。</li>
          <li>在“估价与报告”页填写估价对象并发起估价。</li>
          <li>在任务详情中生成并下载 Docx 报告。</li>
        </ol>
      </div>
    </div>
  )
}
