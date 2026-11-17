import React, { useEffect, useState } from 'react'
import { api, type User } from '../api'

const empty = { community:'', address:'', city:'', district:'', lng:'116.397', lat:'39.908', area:'80', floor:'5', total_floor:'18', orientation:'南', build_year:'2015', deal_price:'5000000', deal_date:'2024-06-01', source:'', remark:'' }

export default function ComparablesPage({ user }: { user: User }) {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [size] = useState(20)
  const [filters, setFilters] = useState({ city: '', district: '', keyword: '' })
  const [form, setForm] = useState<any>(empty)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  const [nearby, setNearby] = useState({ lng:'116.397', lat:'39.908', radius_m:'2000' })
  const [nearbyItems, setNearbyItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const canEdit = user.role === 'admin' || user.role === 'appraiser'
  const canDelete = user.role === 'admin'

  async function load(p = page) {
    setLoading(true); setErr('')
    try {
      const r = await api.listComparables({ page: p, size, ...filters })
      setItems(r.items || []); setTotal(r.total || 0); setPage(p)
    } catch(e:any){ setErr(e.message) } finally { setLoading(false) }
  }
  useEffect(()=>{ load(1) }, []) // eslint-disable-line

  function set(k: string, v: string) { setForm((f:any)=>({...f,[k]:v})) }
  function setF(k: string, v: string) { setFilters((f:any)=>({...f,[k]:v})) }

  function toPayload(f: any) {
    return { ...f, lng:+f.lng, lat:+f.lat, area:+f.area, floor:+(f.floor||0), total_floor:+(f.total_floor||0), build_year:+(f.build_year||0), deal_price:+f.deal_price }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setMsg(''); setErr('')
    if (!form.community || !form.deal_date) { setErr('请填写小区/项目和成交日期'); return }
    if (!(+form.area > 0) || !(+form.deal_price > 0)) { setErr('面积和成交价必须大于0'); return }
    try {
      const payload = toPayload(form)
      if (editingId) {
        await api.updateComparable(editingId, payload)
        setMsg(`案例 #${editingId} 已更新`)
      } else {
        await api.createComparable(payload)
        setMsg('案例已创建')
      }
      setForm(empty); setEditingId(null); await load(1)
    } catch(e:any){ setErr(e.message) }
  }

  function startEdit(c: any) {
    setEditingId(c.id)
    setForm({
      community: c.community||'', address: c.address||'', city: c.city||'', district: c.district||'',
      lng: String(c.lng??''), lat: String(c.lat??''), area: String(c.area??''), floor: String(c.floor??0),
      total_floor: String(c.total_floor??0), orientation: c.orientation||'', build_year: String(c.build_year??0),
      deal_price: String(c.deal_price??''), deal_date: c.deal_date||'', source: c.source||'', remark: c.remark||''
    })
    setMsg(''); setErr('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  function cancelEdit() { setEditingId(null); setForm(empty) }

  async function remove(id: number) {
    if (!window.confirm(`确认删除案例 #${id}？`)) return
    setMsg(''); setErr('')
    try { await api.deleteComparable(id); setMsg(`案例 #${id} 已删除`); await load(page) }
    catch(e:any){ setErr(e.message) }
  }

  async function doImport() {
    if (!file) return; setMsg(''); setErr('')
    try { const r = await api.importComparables(file); setMsg(`导入完成：成功 ${r.inserted}，跳过 ${r.skipped}${r.errors?.length?`；错误示例：${r.errors.slice(0,3).join(' | ')}`:''}`); setFile(null); await load(1) }
    catch(e:any){ setErr(e.message) }
  }

  async function doNearby() {
    setMsg(''); setErr('')
    try { const r = await api.nearbyComparables({ lng:+nearby.lng, lat:+nearby.lat, radius_m:+nearby.radius_m, limit:20 }); setNearbyItems(r.items||[]) }
    catch(e:any){ setErr(e.message) }
  }

  const totalPages = Math.max(1, Math.ceil(total / size))

  return (
    <div className="container">
      <div className="card">
        <h2>可比案例管理</h2>
        {msg && <div className="success">{msg}</div>}
        {err && <div className="error">{err}</div>}

        <h3>{editingId ? `编辑案例 #${editingId}` : '新增案例'}</h3>
        {!canEdit && <div className="muted">当前角色无新增/编辑权限（需估价师或管理员）。</div>}
        <form onSubmit={submit}>
          <div className="grid2">
            {[
              ['community','小区/项目*','text'],['address','地址','text'],['city','城市','text'],['district','区域','text'],
              ['lng','经度*','number'],['lat','纬度*','number'],['area','面积(㎡)*','number'],['floor','楼层','number'],['total_floor','总层','number'],
              ['orientation','朝向','text'],['build_year','建成年份','number'],['deal_price','成交总价(元)*','number'],['deal_date','成交日期*','date'],['source','来源','text'],
            ].map(([k,label,type])=> (
              <div className="field" key={k}><label>{label}</label><input type={type} value={form[k] ?? ''} onChange={e=>set(k,e.target.value)} disabled={!canEdit} step={type==='number'?'any':undefined} /></div>
            ))}
          </div>
          <div className="field"><label>备注</label><textarea value={form.remark || ''} onChange={e=>set('remark',e.target.value)} disabled={!canEdit} /></div>
          <div className="actions">
            <button type="submit" disabled={!canEdit}>{editingId ? '保存修改' : '保存案例'}</button>
            {editingId && <button type="button" className="secondary" onClick={cancelEdit}>取消编辑</button>}
          </div>
        </form>
      </div>

      <div className="card">
        <h3>Excel 导入 (.xlsx)</h3>
        <p className="muted">必需列：community,lng,lat,area,deal_price,deal_date；可选：address,city,district,floor,total_floor,orientation,build_year,source,remark。</p>
        <div className="actions">
          <input type="file" accept=".xlsx" onChange={e=>setFile(e.target.files?.[0]||null)} disabled={!canEdit} />
          <button onClick={doImport} disabled={!file || !canEdit}>上传导入</button>
        </div>
      </div>

      <div className="card">
        <h3>半径检索</h3>
        <div className="row">
          <div className="field"><label>经度</label><input value={nearby.lng} onChange={e=>setNearby({...nearby,lng:e.target.value})} /></div>
          <div className="field"><label>纬度</label><input value={nearby.lat} onChange={e=>setNearby({...nearby,lat:e.target.value})} /></div>
          <div className="field"><label>半径(m)</label><input value={nearby.radius_m} onChange={e=>setNearby({...nearby,radius_m:e.target.value})} /></div>
        </div>
        <button onClick={doNearby}>查询附近案例</button>
        {nearbyItems.length>0 && (
          <table style={{marginTop:12}}><thead><tr><th>ID</th><th>小区</th><th>单价(元/㎡)</th><th>成交价</th><th>日期</th></tr></thead>
          <tbody>{nearbyItems.map(c=> <tr key={c.id}><td>{c.id}</td><td>{c.community}</td><td>{c.area? (c.deal_price/c.area).toFixed(0):'-'}</td><td>{c.deal_price}</td><td>{c.deal_date}</td></tr>)}</tbody></table>
        )}
      </div>

      <div className="card">
        <h3>案例列表</h3>
        <div className="row" style={{marginBottom:8}}>
          <div className="field"><label>城市</label><input value={filters.city} onChange={e=>setF('city',e.target.value)} /></div>
          <div className="field"><label>区域</label><input value={filters.district} onChange={e=>setF('district',e.target.value)} /></div>
          <div className="field"><label>关键词(小区)</label><input value={filters.keyword} onChange={e=>setF('keyword',e.target.value)} /></div>
          <div className="field" style={{justifyContent:'flex-end'}}><label>&nbsp;</label><button className="secondary" onClick={()=>load(1)} disabled={loading}>{loading?'查询中...':'查询'}</button></div>
        </div>
        <div className="muted">共 {total} 条，第 {page}/{totalPages} 页</div>
        <table><thead><tr><th>ID</th><th>小区</th><th>区域</th><th>面积</th><th>成交价</th><th>日期</th><th>操作</th></tr></thead>
        <tbody>{items.map(c=> (
          <tr key={c.id}>
            <td>{c.id}</td><td>{c.community}</td><td>{c.city} {c.district}</td><td>{c.area}</td><td>{c.deal_price}</td><td>{c.deal_date}</td>
            <td className="actions">
              <button className="secondary" onClick={()=>startEdit(c)} disabled={!canEdit}>编辑</button>
              <button className="danger" onClick={()=>remove(c.id)} disabled={!canDelete}>删除</button>
            </td>
          </tr>
        ))}</tbody></table>
        <div className="actions" style={{marginTop:8}}>
          <button className="secondary" onClick={()=>load(Math.max(1,page-1))} disabled={page<=1 || loading}>上一页</button>
          <button className="secondary" onClick={()=>load(Math.min(totalPages,page+1))} disabled={page>=totalPages || loading}>下一页</button>
        </div>
      </div>
    </div>
  )
}
