import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import View3D from './View3D.tsx'

type Node = { id: string; type: 'room' | 'corridor' | 'exit'; x: number; z: number; w?: number; d?: number; label?: string }
type Building = { name: string; nodes: Node[]; edges: { from: string; to: string; width: number }[] }
type Frame = { t: number; people: [number, number, string][] }
type Run = {
  total_time_s: number; per_exit: Record<string, number>; bottleneck: string; peak_queue: number
  frames: Frame[]; door_routes?: Record<string, string[][]>
}

// Live API (AWS). Without it the page falls back to saved runs, so ?demo=1 and offline demos still work.
const API = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? ''
const DEMO = new URLSearchParams(location.search).has('demo')
const SAVED: Record<string, string> = { '': 'data/frames_iit_kgp_nearest.json', MAIN: 'data/frames_iit_kgp_blockedMAIN.json' }

const STATE_VAR: Record<string, string> = { walking: '--walk', queuing: '--queue', stairs: '--stairs', inside: '--inside' }
const LEGEND: [string, string, string][] = [
  ['out', 'Evacuated', '--ink'], ['stairs', 'On the stairs', '--stairs'], ['queuing', 'Queuing', '--queue'],
  ['walking', 'Walking', '--walk'], ['inside', 'Still inside', '--inside'],
]
const fmt = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`
const cssVar = (v: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim()

async function fetchRun(building: Building, blocked: string[]): Promise<Run> {
  const key = blocked.slice().sort().join('+')
  if ((!API || DEMO) && key in SAVED) return (await fetch(SAVED[key])).json()
  if (!API) throw new Error('This scenario needs the live API (set VITE_API_URL).')
  const r = await fetch(`${API}/simulate`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ building, blocked }),
  })
  if (!r.ok) throw new Error(`Simulator error ${r.status}`)
  return r.json()
}

export default function App() {
  const [building, setBuilding] = useState<Building>()
  const [blocked, setBlocked] = useState<string[]>([])
  const [run, setRun] = useState<Run>()
  const [baseline, setBaseline] = useState<number>()
  const [error, setError] = useState('')
  const [i, setI] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(4)
  const [mode3d, setMode3d] = useState(true)
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => { fetch('data/iit_kgp_museum.json').then(r => r.json()).then(setBuilding) }, [])
  useEffect(() => {
    if (!building) return
    let live = true
    setRun(undefined); setError(''); setI(0)
    fetchRun(building, blocked)
      .then(r => { if (live) { setRun(r); if (!blocked.length) setBaseline(r.total_time_s) } })
      .catch(e => live && setError(String(e.message ?? e)))
    return () => { live = false }
  }, [building, blocked])
  useEffect(() => {
    if (!run || !playing) return
    const id = setInterval(() => setI(k => Math.min(k + 1, run.frames.length - 1)), 1000 / speed)
    return () => clearInterval(id)
  }, [run, playing, speed])

  const view = useMemo(() => {
    if (!building) return undefined
    const xs = building.nodes.map(n => n.x), zs = building.nodes.map(n => n.z)
    return { x0: Math.min(...xs) - 6, z0: Math.min(...zs) - 6, x1: Math.max(...xs) + 6, z1: Math.max(...zs) + 6 }
  }, [building])
  const scale = (c: HTMLCanvasElement) => view ? Math.min(c.width / (view.x1 - view.x0), c.height / (view.z1 - view.z0)) : 1
  const exits = building?.nodes.filter(n => n.type === 'exit') ?? []
  const f = run?.frames[i]

  const toggleExit = useCallback((id: string) => {
    setBlocked(b => {
      if (b.includes(id)) return b.filter(x => x !== id)
      if (b.length + 1 >= exits.length) { setError('At least one exit must stay open.'); return b }
      return [...b, id]
    })
  }, [exits.length])

  function onCanvasClick(ev: React.MouseEvent<HTMLCanvasElement>) {
    const c = canvas.current
    if (!c || !view) return
    const rect = c.getBoundingClientRect(), s = scale(c)
    const px = (ev.clientX - rect.left) * (c.width / rect.width), pz = (ev.clientY - rect.top) * (c.height / rect.height)
    const hit = exits.find(n => Math.hypot((n.x - view.x0) * s - px, (n.z - view.z0) * s - pz) < 22)
    if (hit) toggleExit(hit.id)
  }

  useEffect(() => {
    const c = canvas.current, g = c?.getContext('2d')
    if (!c || !g || !building || !view) return
    const s = scale(c)
    const P = (x: number, z: number): [number, number] => [(x - view.x0) * s, (z - view.z0) * s]
    const byId = Object.fromEntries(building.nodes.map(n => [n.id, n]))
    g.clearRect(0, 0, c.width, c.height)
    g.lineCap = 'round'; g.lineJoin = 'round'
    for (const e of building.edges) {
      const [ax, az] = P(byId[e.from].x, byId[e.from].z), [bx, bz] = P(byId[e.to].x, byId[e.to].z)
      g.strokeStyle = '#e2e6ea'; g.lineWidth = Math.max(2, e.width * s)
      g.beginPath(); g.moveTo(ax, az); g.lineTo(bx, bz); g.stroke()
    }
    // escape routes: one ribbon per door of each room, to its assigned exit
    g.strokeStyle = cssVar('--route'); g.globalAlpha = 0.55; g.lineWidth = 3
    for (const paths of Object.values(run?.door_routes ?? {})) for (const path of paths) {
      g.beginPath(); path.forEach((id, k) => { const [x, z] = P(byId[id].x, byId[id].z); if (k) g.lineTo(x, z); else g.moveTo(x, z) }); g.stroke()
    }
    g.globalAlpha = 1
    for (const n of building.nodes.filter(n => n.type === 'room')) {
      const w = n.w ?? 4, d = n.d ?? 4, [x, z] = P(n.x - w / 2, n.z - d / 2)
      g.fillStyle = '#fff'; g.strokeStyle = cssVar('--wall'); g.lineWidth = 2
      g.fillRect(x, z, w * s, d * s); g.strokeRect(x, z, w * s, d * s)
      g.fillStyle = cssVar('--muted'); g.font = '12px Segoe UI'; g.fillText(n.label ?? n.id, x + 4, z + 14, w * s - 8)
    }
    for (const n of exits) {
      const [x, z] = P(n.x, n.z), off = blocked.includes(n.id)
      g.fillStyle = cssVar(off ? '--queue' : '--accent'); g.beginPath(); g.arc(x, z, 11, 0, 7); g.fill()
      if (off) { g.strokeStyle = '#fff'; g.lineWidth = 3; g.beginPath(); g.moveTo(x - 6, z - 6); g.lineTo(x + 6, z + 6); g.moveTo(x + 6, z - 6); g.lineTo(x - 6, z + 6); g.stroke() }
      g.fillStyle = cssVar('--ink'); g.font = '600 12px Segoe UI'; g.textAlign = x > c.width * 0.8 ? 'right' : 'left'
      g.fillText((off ? 'BLOCKED: ' : '') + (n.label ?? n.id), x + (g.textAlign === 'right' ? -16 : 16), z + 4); g.textAlign = 'left'
    }
    const f = run?.frames[i]
    if (f) for (const [x, z, st] of f.people) {
      if (st === 'out') continue
      const [px, pz] = P(x, z)
      g.fillStyle = cssVar(STATE_VAR[st] ?? '--inside'); g.beginPath(); g.arc(px, pz, 2.6, 0, 7); g.fill()
    }
  }, [building, view, run, i, blocked, mode3d])

  const counts: Record<string, number> = {}
  for (const p of f?.people ?? []) counts[p[2]] = (counts[p[2]] ?? 0) + 1
  const delta = run && baseline !== undefined && blocked.length ? run.total_time_s - baseline : undefined

  return (
    <main style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 16px' }}>
      <header style={{ display: 'flex', alignItems: 'baseline', gap: 16, flexWrap: 'wrap' }}>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: 44, margin: 0 }}>Nikaas</h1>
        <span style={{ color: 'var(--muted)' }}>Photograph the exit map. Get everyone out faster.</span>
      </header>
      <p style={{ color: 'var(--muted)', margin: '6px 0 16px' }}>{building?.name}</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: 'var(--muted)' }}>Block an exit (tap it on the map):</span>
        {exits.map(n => <button key={n.id} className={blocked.includes(n.id) ? 'on' : ''} onClick={() => toggleExit(n.id)}>{n.label ?? n.id}</button>)}
        {blocked.length > 0 && <button onClick={() => setBlocked([])}>Reset</button>}
        <span style={{ flex: 1 }} />
        <button className={mode3d ? 'on' : ''} onClick={() => setMode3d(true)}>3D</button>
        <button className={mode3d ? '' : 'on'} onClick={() => setMode3d(false)}>2D</button>
        <button onClick={() => setPlaying(p => !p)}>{playing ? 'Pause' : 'Play'}</button>
        {[1, 2, 4, 8].map(v => <button key={v} className={v === speed ? 'on' : ''} onClick={() => setSpeed(v)}>{v}×</button>)}
        <button onClick={() => setI(0)}>Restart</button>
      </div>
      {error && <div role="alert" style={{ background: '#fdecec', border: '1px solid var(--queue)', padding: '8px 12px', marginBottom: 12 }}>{error}</div>}
      <div className="layout">
        <div style={{ position: 'relative' }}>
          {mode3d && building
            ? <View3D building={building} frame={f} blocked={blocked} routes={run?.door_routes} onExit={toggleExit} />
            : <canvas ref={canvas} width={1000} height={560} onClick={onCanvasClick}
                style={{ width: '100%', background: 'var(--card)', border: '1px solid var(--line)', cursor: 'pointer' }} />}
          {!run && !error && <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: 'var(--muted)' }}>Simulating 507 people…</div>}
        </div>
        <aside style={{ background: 'var(--card)', border: '1px solid var(--line)', padding: 16 }}>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 56, lineHeight: 1 }}>{fmt(f?.t ?? 0)}</div>
          <div style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>simulated time</div>
          {LEGEND.map(([k, label, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--mono)', fontSize: 14, padding: '3px 0' }}>
              <span style={{ fontFamily: 'var(--sans)' }}><b style={{ display: 'inline-block', width: 10, height: 10, background: `var(${v})`, marginRight: 8 }} />{label}</span>
              <span>{counts[k] ?? 0}</span>
            </div>
          ))}
          <hr style={{ border: 0, borderTop: '1px solid var(--line)' }} />
          <Stat label="Total evacuation" value={run ? `${run.total_time_s} s${delta !== undefined ? `  (${delta >= 0 ? '+' : ''}${delta.toFixed(1)} s vs all exits open)` : ''}` : '…'} />
          <Stat label="Bottleneck (peak queue)" value={run ? `${run.bottleneck} (${run.peak_queue})` : '…'} />
          <Stat label="People per exit" value={run ? Object.entries(run.per_exit).map(([k, v]) => `${k} ${v}`).join(' · ') : '…'} />
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 12 }}>
            {API && !DEMO ? 'Live: simulated on AWS for every change.' : 'Saved runs (demo mode).'} Simulator validated against the SFPE handbook example.
          </div>
        </aside>
      </div>
    </main>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 13, color: 'var(--muted)' }}>{label}</div>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 15 }}>{value}</div>
    </div>
  )
}
