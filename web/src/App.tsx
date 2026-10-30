import { useState, useEffect, useRef, useCallback } from 'react'
import type { Building, SimResult, Frame } from './types'
import Canvas2D from './components/Canvas2D'
import View3D from './components/View3D'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const DEMO = new URLSearchParams(location.search).has('demo')

const STATE_COLORS: Record<string, string> = {
  walking: '#FF8C00',
  queuing: '#FF3030',
  stairs: '#4488FF',
  inside: '#888',
}

type Speed = 1 | 2 | 4
type View = '2d' | '3d' | 'side'

export default function App() {
  const [building, setBuilding] = useState<Building | null>(null)
  const [nearest, setNearest] = useState<SimResult | null>(null)
  const [blockedResult, setBlockedResult] = useState<SimResult | null>(null)
  const [optimise, setOptimise] = useState<SimResult | null>(null)

  const [blocked, setBlocked] = useState<string[]>([])
  const [frameIdx, setFrameIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState<Speed>(1)
  const [view, setView] = useState<View>('2d')
  const [loading, setLoading] = useState(true)
  const [apiLoading, setApiLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const rafRef = useRef<number | null>(null)
  const lastTimeRef = useRef<number | null>(null)
  const fracRef = useRef(0)

  // active sim: if blocked result available, show it; else nearest
  const activeSim = (blocked.length > 0 && blockedResult) ? blockedResult : nearest

  // Load building + nearest frames
  useEffect(() => {
    async function load() {
      try {
        const [bldResp, simResp] = await Promise.all([
          fetch('/lab_block.json'),
          fetch('/frames_lab_block_nearest.json'),
        ])
        const bld: Building = await bldResp.json()
        const sim: SimResult = await simResp.json()
        setBuilding(bld)
        setNearest(sim)
      } catch (e) {
        setError('Failed to load data files')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Animation loop
  useEffect(() => {
    if (!playing || !activeSim) return
    const frames = activeSim.frames
    const animate = (ts: number) => {
      if (lastTimeRef.current === null) lastTimeRef.current = ts
      const dt = (ts - lastTimeRef.current) / 1000
      lastTimeRef.current = ts
      fracRef.current += dt * speed
      if (fracRef.current >= 1) {
        const steps = Math.floor(fracRef.current)
        fracRef.current -= steps
        setFrameIdx(i => {
          const next = i + steps
          if (next >= frames.length - 1) { setPlaying(false); return frames.length - 1 }
          return next
        })
      }
      rafRef.current = requestAnimationFrame(animate)
    }
    rafRef.current = requestAnimationFrame(animate)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      lastTimeRef.current = null
      fracRef.current = 0
    }
  }, [playing, speed, activeSim])

  const currentFrame: Frame | null = activeSim?.frames[frameIdx] ?? null
  const totalFrames = activeSim?.frames.length ?? 1

  const togglePlay = () => {
    if (frameIdx >= totalFrames - 1) setFrameIdx(0)
    setPlaying(p => !p)
  }

  const handleClickExit = useCallback(async (exitId: string) => {
    if (blocked.includes(exitId)) {
      // unblock
      const newBlocked = blocked.filter(b => b !== exitId)
      setBlocked(newBlocked)
      if (newBlocked.length === 0) setBlockedResult(null)
      return
    }
    const newBlocked = [...blocked, exitId]
    setBlocked(newBlocked)

    if (DEMO) {
      // demo: load pre-saved blocked frames
      setApiLoading(true)
      try {
        const resp = await fetch('/frames_lab_block_blockedB.json')
        const sim: SimResult = await resp.json()
        setBlockedResult(sim)
      } catch {
        setError('Failed to load blocked frames')
      } finally {
        setApiLoading(false)
      }
      setFrameIdx(0)
      setPlaying(false)
      return
    }

    if (!building || !nearest) return
    setApiLoading(true)
    try {
      const body = { building, plan: null, blocked: newBlocked }
      const resp = await fetch(`${API_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!resp.ok) throw new Error(await resp.text())
      const sim: SimResult = await resp.json()
      setBlockedResult(sim)
      setFrameIdx(0)
      setPlaying(false)

      // Try optimise
      try {
        const oResp = await fetch(`${API_URL}/optimise`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        if (oResp.ok) setOptimise(await oResp.json())
      } catch { /* optimise optional */ }
    } catch (e: unknown) {
      setError(`API error: ${e instanceof Error ? e.message : e}`)
    } finally {
      setApiLoading(false)
    }
  }, [blocked, building, nearest])

  const stateCounts = currentFrame
    ? currentFrame.people.reduce<Record<string, number>>((acc, [,, st]) => {
        acc[st] = (acc[st] ?? 0) + 1
        return acc
      }, {})
    : {}

  if (loading) return (
    <div style={styles.center}>
      <div style={styles.spinner} />
      <div style={{ marginTop: 16, color: '#888' }}>Loading building data…</div>
    </div>
  )

  if (error && !building) return (
    <div style={styles.center}>
      <div style={{ color: '#FF6666' }}>{error}</div>
    </div>
  )

  if (!building || !nearest) return null

  const displaySim = activeSim
  const t = currentFrame?.t ?? 0
  const pct = Math.round((frameIdx / (totalFrames - 1)) * 100)

  return (
    <div style={styles.root}>
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.logo}>Nikaas</span>
        <span style={styles.subtitle}>Evacuation Simulator</span>
        {DEMO && <span style={styles.demoBadge}>DEMO</span>}
        <div style={{ flex: 1 }} />
        {/* View toggle */}
        <div style={styles.btnGroup}>
          {(['2d','3d','side'] as View[]).map(v => (
            <button key={v} style={view === v ? styles.btnActive : styles.btn}
              onClick={() => setView(v)}>
              {v === 'side' ? '2D+3D' : v.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div style={styles.main}>
        {/* Canvas area */}
        <div style={styles.canvasArea}>
          {view === '2d' && (
            <div style={styles.canvasWrap}>
              <Canvas2D building={building} sim={displaySim} frame={currentFrame}
                blocked={blocked} onClickExit={handleClickExit}
                label={blocked.length ? 'Blocked exit plan' : 'Nearest-exit plan'} />
            </div>
          )}
          {view === '3d' && (
            <div style={styles.canvasWrap}>
              <View3D building={building} sim={displaySim} frame={currentFrame} blocked={blocked} />
              <div style={styles.hint3d}>Drag to orbit · Scroll to zoom</div>
            </div>
          )}
          {view === 'side' && (
            <div style={styles.sideWrap}>
              <div style={styles.half}>
                <Canvas2D building={building} sim={nearest} frame={nearest.frames[frameIdx] ?? null}
                  blocked={[]} onClickExit={() => {}} label="Nearest-exit plan" />
              </div>
              <div style={styles.half}>
                {(blockedResult || optimise) ? (
                  <Canvas2D building={building}
                    sim={optimise ?? blockedResult}
                    frame={(optimise ?? blockedResult)!.frames[frameIdx] ?? null}
                    blocked={blocked} onClickExit={handleClickExit}
                    label={optimise ? 'Nikaas optimised' : 'Blocked exit plan'} />
                ) : (
                  <div style={styles.placeholder}>
                    {blocked.length ? 'Loading…' : 'Click an exit to block it and see the re-plan'}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div style={styles.panel}>
          {/* Clock */}
          <div style={styles.clock}>
            <span style={styles.clockTime}>T = {t.toFixed(1)} s</span>
            <span style={styles.clockTotal}>/ {displaySim?.total_time_s.toFixed(0)} s</span>
          </div>

          {/* Controls */}
          <div style={styles.controls}>
            <button style={styles.playBtn} onClick={togglePlay}>
              {playing ? '⏸' : '▶'}
            </button>
            <div style={styles.speedBtns}>
              {([1,2,4] as Speed[]).map(s => (
                <button key={s} style={speed === s ? styles.btnActive : styles.btn}
                  onClick={() => setSpeed(s)}>{s}×</button>
              ))}
            </div>
          </div>

          {/* Scrubber */}
          <input type="range" min={0} max={totalFrames - 1} value={frameIdx}
            style={styles.scrubber}
            onChange={e => { setFrameIdx(Number(e.target.value)); setPlaying(false) }} />
          <div style={styles.scrubberLabel}>{pct}%</div>

          {/* People dot grid */}
          <div style={styles.section}>
            <div style={styles.sectionTitle}>People grid</div>
            <DotGrid total={displaySim?.people ?? 528} counts={stateCounts} />
          </div>

          {/* Legend */}
          <div style={styles.section}>
            <div style={styles.sectionTitle}>Legend</div>
            {Object.entries(STATE_COLORS).map(([st, col]) => (
              <div key={st} style={styles.legendRow}>
                <span style={{ ...styles.dot, background: col }} />
                <span style={styles.legendLabel}>{st}</span>
                <span style={styles.legendCount}>{stateCounts[st] ?? 0}</span>
              </div>
            ))}
            <div style={styles.legendRow}>
              <span style={{ ...styles.dot, background: '#444' }} />
              <span style={styles.legendLabel}>out (evacuated)</span>
              <span style={styles.legendCount}>{stateCounts['out'] ?? 0}</span>
            </div>
          </div>

          {/* Per-exit counts */}
          {displaySim && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>Exits</div>
              {Object.entries(displaySim.per_exit).map(([exit, cnt]) => (
                <div key={exit} style={styles.exitRow}>
                  <span style={{
                    ...styles.exitBadge,
                    background: blocked.includes(exit) ? '#FF3030' : '#00CC66'
                  }}>{exit}</span>
                  <span style={styles.exitCount}>{cnt} people</span>
                  <button style={styles.blockBtn}
                    onClick={() => handleClickExit(exit)}>
                    {blocked.includes(exit) ? 'unblock' : 'block'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Bottleneck */}
          {displaySim?.bottleneck && (
            <div style={styles.bottleneck}>
              ⚠ Bottleneck: <b>{displaySim.bottleneck}</b>
              <br />Peak queue: {displaySim.peak_queue}
            </div>
          )}

          {/* Blocked exits */}
          {blocked.length > 0 && (
            <div style={styles.blockedInfo}>
              Blocked: {blocked.join(', ')}
              <button style={styles.clearBtn} onClick={() => { setBlocked([]); setBlockedResult(null); setOptimise(null) }}>
                clear
              </button>
            </div>
          )}

          {apiLoading && <div style={styles.apiLoading}>Re-simulating…</div>}
          {error && <div style={styles.errorBox}>{error}</div>}

          {optimise && (
            <div style={styles.optimiseBox}>
              <b>Nikaas optimised</b>
              <br />Total: {optimise.total_time_s.toFixed(1)} s
              {(optimise as SimResult & { lower_bound_s?: number }).lower_bound_s !== undefined && (
                <> · Lower bound: {(optimise as SimResult & { lower_bound_s?: number }).lower_bound_s!.toFixed(1)} s</>
              )}
            </div>
          )}

          <div style={styles.hint}>Click exits on the map to block/unblock them</div>
        </div>
      </div>
    </div>
  )
}

function DotGrid({ total, counts }: { total: number; counts: Record<string, number> }) {
  const cols = Math.ceil(Math.sqrt(total))
  const dots: string[] = []
  const order: [string, string][] = [
    ['walking', '#FF8C00'], ['queuing', '#FF3030'], ['stairs', '#4488FF'],
    ['inside', '#888'], ['out', '#222'],
  ]
  for (const [st, col] of order) {
    for (let i = 0; i < (counts[st] ?? 0); i++) dots.push(col)
  }
  while (dots.length < total) dots.push('#222')

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, maxWidth: 200 }}>
      {dots.map((col, i) => (
        <div key={i} style={{ width: 5, height: 5, borderRadius: '50%', background: col }} />
      ))}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  root: { display: 'flex', flexDirection: 'column', height: '100vh', background: '#0d0d0d', color: '#e8e8e8' },
  header: { display: 'flex', alignItems: 'center', gap: 12, padding: '8px 16px', borderBottom: '1px solid #222', flexShrink: 0 },
  logo: { fontWeight: 800, fontSize: 18, color: '#00CC66', letterSpacing: -0.5 },
  subtitle: { fontSize: 12, color: '#666' },
  demoBadge: { background: '#FF8C00', color: '#000', fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4 },
  btnGroup: { display: 'flex', gap: 4 },
  btn: { background: '#1a1a1a', border: '1px solid #333', color: '#aaa', borderRadius: 4, padding: '4px 10px', cursor: 'pointer', fontSize: 12 },
  btnActive: { background: '#00CC66', border: '1px solid #00CC66', color: '#000', borderRadius: 4, padding: '4px 10px', cursor: 'pointer', fontSize: 12, fontWeight: 700 },
  main: { display: 'flex', flex: 1, minHeight: 0 },
  canvasArea: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' },
  canvasWrap: { flex: 1, minHeight: 0, position: 'relative', background: '#0a0a0a' },
  sideWrap: { flex: 1, minHeight: 0, display: 'flex' },
  half: { flex: 1, minWidth: 0, position: 'relative', background: '#0a0a0a' },
  placeholder: { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#555', fontSize: 13, padding: 20, textAlign: 'center' },
  hint3d: { position: 'absolute', bottom: 8, left: 8, color: '#444', fontSize: 10, pointerEvents: 'none' },
  panel: { width: 220, borderLeft: '1px solid #1e1e1e', overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 12, flexShrink: 0, background: '#0f0f0f' },
  clock: { display: 'flex', alignItems: 'baseline', gap: 6 },
  clockTime: { fontSize: 22, fontWeight: 700, color: '#fff', fontVariantNumeric: 'tabular-nums' },
  clockTotal: { fontSize: 12, color: '#555' },
  controls: { display: 'flex', alignItems: 'center', gap: 8 },
  playBtn: { background: '#00CC66', border: 'none', color: '#000', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 16, fontWeight: 700 },
  speedBtns: { display: 'flex', gap: 3 },
  scrubber: { width: '100%', accentColor: '#00CC66', cursor: 'pointer' },
  scrubberLabel: { fontSize: 10, color: '#555', textAlign: 'right' },
  section: { display: 'flex', flexDirection: 'column', gap: 5 },
  sectionTitle: { fontSize: 10, fontWeight: 700, color: '#555', textTransform: 'uppercase', letterSpacing: 1 },
  legendRow: { display: 'flex', alignItems: 'center', gap: 6 },
  dot: { width: 10, height: 10, borderRadius: '50%', flexShrink: 0 },
  legendLabel: { flex: 1, fontSize: 12, color: '#aaa' },
  legendCount: { fontSize: 12, color: '#666', fontVariantNumeric: 'tabular-nums' },
  exitRow: { display: 'flex', alignItems: 'center', gap: 6 },
  exitBadge: { padding: '2px 6px', borderRadius: 4, color: '#000', fontSize: 11, fontWeight: 700, flexShrink: 0 },
  exitCount: { flex: 1, fontSize: 11, color: '#888' },
  blockBtn: { background: 'none', border: '1px solid #333', color: '#888', borderRadius: 3, padding: '2px 6px', cursor: 'pointer', fontSize: 10 },
  bottleneck: { background: '#1a0a0a', border: '1px solid #FF3030', borderRadius: 6, padding: '8px 10px', fontSize: 11, color: '#FF8888' },
  blockedInfo: { background: '#1a1000', border: '1px solid #FF8C00', borderRadius: 6, padding: '8px 10px', fontSize: 11, color: '#FFB800', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  clearBtn: { background: 'none', border: '1px solid #FF8C00', color: '#FF8C00', borderRadius: 3, padding: '2px 6px', cursor: 'pointer', fontSize: 10 },
  apiLoading: { color: '#888', fontSize: 11, fontStyle: 'italic' },
  errorBox: { background: '#1a0a0a', border: '1px solid #FF3030', borderRadius: 4, padding: '6px 8px', fontSize: 11, color: '#FF8888' },
  optimiseBox: { background: '#0a1a0a', border: '1px solid #00CC66', borderRadius: 6, padding: '8px 10px', fontSize: 11, color: '#88FF88' },
  hint: { fontSize: 10, color: '#333', marginTop: 'auto', paddingTop: 8 },
  center: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' },
  spinner: { width: 32, height: 32, border: '3px solid #1e1e1e', borderTop: '3px solid #00CC66', borderRadius: '50%', animation: 'spin 0.8s linear infinite' },
}
