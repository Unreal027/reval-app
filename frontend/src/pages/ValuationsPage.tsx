import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function ValuationsPage() {
  const [method, setMethod] = useState<'comparison'|'income'|'cost'>('comparison')
  const [subject, setSubject] = useState<any>({
    community:'示例小区', address:'', city:'', district:'', lng:'116.397', lat:'39.908',
    area:'80', floor:'5', total_floor:'18', orientation:'南', build_year:'2015', purpose:'住宅',
    monthly_rent:'', cap_rate:'0.03', vacancy_rate:'0.05', annual_cost_rate:'0.2',
    land_unit_price:'', replacement_unit_cost:'', depreciation_rate:'0.2', other_cost:'0'
  })
  const [radiusM, setRadiusM] = useState('2000')
  const [maxC, setMaxC] = useState('5')
  const [remark, setRemark] = useState('')
  const [tasks, setTasks] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [reports, setReports] = useState<any[]>([])
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  function setS(k: string, v: string) { setSubject((s:any)=>({...s,[k]:v})) }

  async function loadTasks() {
    try { const r = await api.listValuations(); setTasks(r.items||[]) } catch(e:any){ setErr(e.message) }
  }
  async function loadReports(taskId?: number) {
    try { const r = await api.listReports(taskId); setReports(r.items||[]) } catch(e:any){ /* ignore */ }
  }
  useEffect(()=>{ loadTasks() }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setMsg(''); setErr(''); setLoading(true)
    try {
      const si: any = {
        community: subject.community, address: subject.address, city: subject.city, district: subject.district,
        lng:+subject.lng, lat:+subject.lat, area:+subject.area, floor:+subject.floor||0, total_floor:+subject.total_floor||0,
        orientation: subject.orientation, build_year:+subject.build_year||0, purpose: subject.purpose,
      }
      if (method === 'income') {
        if (subject.monthly_rent) si.monthly_rent = +subject.monthly_rent
        if (subject.cap_rate) si.cap_rate = +subject.cap_rate
        if (subject.vacancy_rate) si.vacancy_rate = +subject.vacancy_rate
        if (subject.annual_cost_rate) si.annual_cost_rate = +subject.annual_cost_rate
      }
      if (method === 'cost') {
        if (subject.land_unit_price) si.land_unit_price = +subject.land_unit_price
        if (subject.replacement_unit_cost) si.replacement_unit_cost = +subject.replacement_unit_cost
        if (subject.depreciation_rate) si.depreciation_rate = +subject.depreciation_rate
        if (subject.other_cost) si.other_cost = +subject.other_cost
      }
      const body = { subject_info: si, method, remark, radius_m:+radiusM, max_comparables:+maxC }
      const task = await api.createValuation(body)
      setMsg(`估价任务 #${task.id} 已创建，状态：${task.status}，单价：${task.unit_price}，总价：${task.result_price}`)
      setSelected(task)
      await loadTasks(); await loadReports(task.id)
    } catch(e:any){ setErr(e.message) } finally { setLoading(false) }
  }

  async function viewTask(id: number) {
    setErr(''); try { const t = await api.getValuation(id); setSelected(t); await loadReports(id) } catch(e:any){ setErr(e.message) }
  }

  async function genReport(taskId: number) {
    setErr(''); setMsg('')
    try { const r = await api.generateReport(taskId); setMsg(`报告 #${r.id} 已生成`); await loadReports(taskId) }
    catch(e:any){ setErr(e.message) }
  }

  async function download(id: number, name: string) {
    setErr(''); try { await api.downloadReport(id, name) } catch(e:any){ setErr(e.message) }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>发起估价</h2>
        {msg && <div className="success">{msg}</div>}
        {err && <div className="error">{err}</div>}
        <form onSubmit={submit}>
          <div className="row">
            <div className="field" style={{maxWidth:220}}>
              <label>估价方法</label>
              <select value={method} onChange={e=>setMethod(e.target.value as any)}>
                <option value="comparison">市场比较法</option>
                <option value="income">收益法</option>
                <option value="cost">成本法</option>
              </select>
            </div>
            {method==='comparison' && <>
              <div className="field" style={{maxWidth:180}}><label>搜索半径(m)</label><input value={radiusM} onChange={e=>setRadiusM(e.target.value)} /></div>
              <div className="field" style={{maxWidth:180}}><label>最多可比案例数</label><input value={maxC} onChange={e=>setMaxC(e.target.value)} /></div>
            </>}
          </div>
          <h3>估价对象信息</h3>
          <div className="grid2">
            {[
              ['community','小区/项目'],['address','地址'],['city','城市'],['district','区域'],
              ['lng','经度'],['lat','纬度'],['area','面积(㎡)'],['floor','楼层'],['total_floor','总层'],
              ['orientation','朝向'],['build_year','建成年份'],['purpose','用途'],
            ].map(([k,label])=> <div className="field" key={k}><label>{label}</label><input value={subject[k]||''} onChange={e=>setS(k,e.target.value)} /></div>)}
          </div>
          {method==='income' && (
            <div className="card" style={{background:'#f9fafb'}}>
              <h3>收益法参数</h3>
              <div className="grid2">
                {[['monthly_rent','月租金(元/月)'],['cap_rate','资本化率/收益率'],['vacancy_rate','空置率'],['annual_cost_rate','年成本率']].map(([k,label])=> <div className="field" key={k}><label>{label}</label><input value={subject[k]||''} onChange={e=>setS(k,e.target.value)} /></div>)}
              </div>
            </div>
          )}
          {method==='cost' && (
            <div className="card" style={{background:'#f9fafb'}}>
              <h3>成本法参数</h3>
              <div className="grid2">
                {[['land_unit_price','土地单价(元/㎡)'],['replacement_unit_cost','重置单价(元/㎡)'],['depreciation_rate','折旧率(0~1)'],['other_cost','其他成本(元)']].map(([k,label])=> <div className="field" key={k}><label>{label}</label><input value={subject[k]||''} onChange={e=>setS(k,e.target.value)} /></div>)}
              </div>
            </div>
          )}
          <div className="field"><label>备注</label><textarea value={remark} onChange={e=>setRemark(e.target.value)} /></div>
          <button type="submit" disabled={loading}>{loading ? '计算中...' : '创建并计算估价'}</button>
        </form>
      </div>

      <div className="row" style={{alignItems:'flex-start'}}>
        <div className="card" style={{flex:1, minWidth:320}}>
          <h3>估价任务列表</h3>
          <table><thead><tr><th>ID</th><th>方法</th><th>状态</th><th>总价</th><th>操作</th></tr></thead>
          <tbody>{tasks.map(t=> (
            <tr key={t.id}>
              <td>{t.id}</td><td>{t.method}</td><td><span className="badge">{t.status}</span></td><td>{t.result_price}</td>
              <td className="actions"><button className="secondary" onClick={()=>viewTask(t.id)}>查看</button></td>
            </tr>
          ))}</tbody></table>
        </div>

        <div className="card" style={{flex:2, minWidth:360}}>
          <h3>任务详情与报告</h3>
          {!selected && <div className="muted">请选择一个任务查看详情。</div>}
          {selected && (
            <div>
              <div className="actions">
                <button onClick={()=>genReport(selected.id)}>生成 Docx 报告</button>
              </div>
              <p><b>任务 #{selected.id}</b> | 方法: {selected.method} | 状态: {selected.status}</p>
              <p>评估单价: {selected.unit_price} 元/㎡，评估总价: {selected.result_price} 元</p>
              <details><summary>估价对象与计算信息</summary><pre>{JSON.stringify(selected.subject_info, null, 2)}</pre></details>
              {selected.adjustments && selected.adjustments.length > 0 && (
                <>
                  <h4>可比案例修正明细</h4>
                  <table><thead><tr><th>案例ID</th><th>系数</th><th>修正后总价</th><th>权重</th></tr></thead>
                  <tbody>{selected.adjustments.map((a:any)=> (
                    <tr key={a.id}><td>{a.comparable_id}</td><td><pre style={{margin:0}}>{JSON.stringify(a.factor_scores)}</pre></td><td>{a.adjusted_price}</td><td>{a.weight}</td></tr>
                  ))}</tbody></table>
                </>
              )}
              <h4>报告列表</h4>
              {reports.length===0 ? <div className="muted">暂无报告</div> : (
                <table><thead><tr><th>ID</th><th>文件名</th><th>生成时间</th><th>操作</th></tr></thead>
                <tbody>{reports.map(r=> <tr key={r.id}><td>{r.id}</td><td>{r.file_name}</td><td>{r.generated_at}</td><td><button className="secondary" onClick={()=>download(r.id, r.file_name)}>下载</button></td></tr>)}</tbody></table>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
