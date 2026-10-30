import { useEffect, useMemo, useRef, useState } from 'react'

type Node = { id: string; type: 'room' | 'corridor' | 'exit'; x: number; z: number; w?: number; d?: number; label?: string }
type Building = { name: string; nodes: Node[]; edges: { from: string; to: string; width: number }[] }
type Frame = { t: number; people: [number, number, string][] }
type Run = { total_time_s: number; per_exit: Record<string, number>; bottleneck: string; frames: Frame[] }

// 2D player (checkpoint build). Bhumika replaces the look and adds the 3D view on top.
const SCENARIOS = [
  { id: 'nearest', label: 'Today: nearest exit', file: 'data/frames_iit_kgp_nearest.json', blocked: '' },
  { id: 'blocked', label: 'Main entrance blocked', file: 'data/frames_iit_kgp_blockedMAIN.json', blocked: 'MAIN' },
]
const STATE_VAR: Record<string, string> = { walking: '--walk', queuing: '--queue', stairs: '--stairs', inside: '--inside' }
const LEGEND: [string, string, string][] = [
  ['out', 'Evacuated', '--ink'], ['stairs', 'On the stairs', '--stairs'], ['queuing', 'Queuing', '--queue'],
  ['walking', 'Walking', '--walk'], ['inside', 'Still inside', '--inside'],
]
const fmt = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`
const cssVar = (v: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim()

export default function App() {
  const [building, setBuilding] = useState<Building>()
  const [scenario, setScenario] = useState(SCENARIOS[0])
  const [run, setRun] = useState<Run>()
  const [i, setI] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(4)
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => { fetch('data/iit_kgp_museum.json').then(r => r.json()).then(setBuilding) }, [])
  useEffect(() => { setRun(undefined); setI(0); fetch(scenario.file).then(r => r.json()).then(setRun) }, [scenario])
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

  useEffect(() => {
    const c = canvas.current, g = c?.getContext('2d')
    if (!c || !g || !building || !view) return
    const s = Math.min(c.width / (view.x1 - view.x0), c.height / (view.z1 - view.z0))
    const P = (x: number, z: number): [number, number] => [(x - view.x0) * s, (z - view.z0) * s]
    const byId = Object.fromEntries(building.nodes.map(n => [n.id, n]))
    g.clearRect(0, 0, c.width, c.height)
    g.lineCap = 'round'
    for (const e of building.edges) {
      const [ax, az] = P(byId[e.from].x, byId[e.from].z), [bx, bz] = P(byId[e.to].x, byId[e.to].z)
      g.strokeStyle = '#e2e6ea'; g.lineWidth = Math.max(2, e.width * s)
      g.beginPath(); g.moveTo(ax, az); g.lineTo(bx, bz); g.stroke()
    }
    for (const n of building.nodes.filter(n => n.type === 'room')) {
      const w = n.w ?? 4, d = n.d ?? 4, [x, z] = P(n.x - w / 2, n.z - d / 2)
      g.fillStyle = '#fff'; g.strokeStyle = cssVar('--wall'); g.lineWidth = 2
      g.fillRect(x, z, w * s, d * s); g.strokeRect(x, z, w * s, d * s)
      g.fillStyle = cssVar('--muted'); g.font = '12px Segoe UI'; g.fillText(n.label ?? n.id, x + 4, z + 14, w * s - 8)
    }
    for (const n of building.nodes.filter(n => n.type === 'exit')) {
      const [x, z] = P(n.x, n.z), blocked = n.id === scenario.blocked
      g.fillStyle = cssVar(blocked ? '--queue' : '--accent'); g.beginPath(); g.arc(x, z, 9, 0, 7); g.fill()
      g.fillStyle = cssVar('--ink'); g.font = '600 12px Segoe UI'; g.fillText((blocked ? 'BLOCKED: ' : '') + (n.label ?? n.id), x + 12, z + 4)
    }
    const f = run?.frames[i]
    if (f) for (const [x, z, st] of f.people) {
      if (st === 'out') continue
      const [px, pz] = P(x, z)
      g.fillStyle = cssVar(STATE_VAR[st] ?? '--inside'); g.beginPath(); g.arc(px, pz, 2.6, 0, 7); g.fill()
    }
  }, [building, view, run, i, scenario])

  const f = run?.frames[i]
  const counts: Record<string, number> = {}
  for (const p of f?.people ?? []) counts[p[2]] = (counts[p[2]] ?? 0) + 1

  return (
    <main style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 16px' }}>
      <header style={{ display: 'flex', alignItems: 'baseline', gap: 16, flexWrap: 'wrap' }}>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: 44, margin: 0 }}>Nikaas</h1>
        <span style={{ color: 'var(--muted)' }}>Photograph the exit map. Get everyone out faster.</span>
      </header>
      <p style={{ color: 'var(--muted)', margin: '6px 0 16px' }}>{building?.name}</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        {SCENARIOS.map(s => <button key={s.id} className={s.id === scenario.id ? 'on' : ''} onClick={() => setScenario(s)}>{s.label}</button>)}
        <span style={{ flex: 1 }} />
        <button onClick={() => setPlaying(p => !p)}>{playing ? 'Pause' : 'Play'}</button>
        {[1, 2, 4, 8].map(v => <button key={v} className={v === speed ? 'on' : ''} onClick={() => setSpeed(v)}>{v}×</button>)}
        <button onClick={() => setI(0)}>Restart</button>
      </div>
      <div className="layout">
        <canvas ref={canvas} width={1000} height={560} style={{ width: '100%', background: 'var(--card)', border: '1px solid var(--line)' }} />
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
          <Stat label="Total evacuation" value={run ? `${run.total_time_s} s` : '…'} />
          <Stat label="Bottleneck" value={run?.bottleneck ?? '…'} />
          <Stat label="People per exit" value={run ? Object.entries(run.per_exit).map(([k, v]) => `${k} ${v}`).join(' · ') : '…'} />
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 12 }}>{f?.people.length ?? 0} people · Nikaas simulator output</div>
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
