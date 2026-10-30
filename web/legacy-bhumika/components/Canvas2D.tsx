import { useRef, useEffect, useCallback } from 'react'
import type { Building, SimResult, Frame } from '../types'

const STATE_COLOR: Record<string, string> = {
  walking: '#FF8C00',
  queuing: '#FF3030',
  stairs: '#4488FF',
  inside: '#888888',
  out: 'transparent',
}

interface Props {
  building: Building
  sim: SimResult | null
  frame: Frame | null
  blocked: string[]
  onClickExit: (id: string) => void
  label?: string
}

function getBBox(b: Building) {
  let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity
  for (const n of b.nodes) {
    const hw = (n.w ?? 0) / 2, hd = (n.d ?? 0) / 2
    minX = Math.min(minX, n.x - hw)
    maxX = Math.max(maxX, n.x + hw)
    minZ = Math.min(minZ, n.z - hd)
    maxZ = Math.max(maxZ, n.z + hd)
  }
  return { minX, maxX, minZ, maxZ }
}

function makeTransform(
  bbox: ReturnType<typeof getBBox>, cw: number, ch: number, pad = 28
) {
  const sx = (cw - 2 * pad) / (bbox.maxX - bbox.minX)
  const sz = (ch - 2 * pad) / (bbox.maxZ - bbox.minZ)
  const s = Math.min(sx, sz)
  const ox = pad + (cw - 2 * pad - (bbox.maxX - bbox.minX) * s) / 2
  const oz = pad + (ch - 2 * pad - (bbox.maxZ - bbox.minZ) * s) / 2
  const toC = (x: number, z: number): [number, number] => [
    ox + (x - bbox.minX) * s,
    oz + (z - bbox.minZ) * s,
  ]
  const fromC = (cx: number, cy: number): [number, number] => [
    (cx - ox) / s + bbox.minX,
    (cy - oz) / s + bbox.minZ,
  ]
  return { toC, fromC, scale: s }
}

function edgeKey(from: string, to: string) {
  return `${from}-${to}`
}

export default function Canvas2D({ building, sim, frame, blocked, onClickExit, label }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const transformRef = useRef<ReturnType<typeof makeTransform> | null>(null)

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const cw = canvas.width, ch = canvas.height
    ctx.clearRect(0, 0, cw, ch)

    const bbox = getBBox(building)
    const tr = makeTransform(bbox, cw, ch)
    transformRef.current = tr
    const { toC, scale } = tr

    const nodeMap = new Map(building.nodes.map(n => [n.id, n]))

    // edge load: max load for color scaling
    const loadMap = sim?.edge_load ?? {}
    const maxLoad = Math.max(1, ...Object.values(loadMap))

    // Draw edges
    for (const e of building.edges) {
      const from = nodeMap.get(e.from), to = nodeMap.get(e.to)
      if (!from || !to) continue
      const [x1, y1] = toC(from.x, from.z)
      const [x2, y2] = toC(to.x, to.z)
      const load = loadMap[edgeKey(e.from, e.to)] ?? loadMap[edgeKey(e.to, e.from)] ?? 0
      const t = load / maxLoad
      // color: green(0) → yellow(0.5) → red(1)
      const r = Math.round(255 * Math.min(1, t * 2))
      const g = Math.round(255 * Math.min(1, 2 - t * 2))
      const isStair = e.kind === 'stair'
      ctx.strokeStyle = isStair ? `rgba(100,160,255,0.9)` : `rgb(${r},${g},40)`
      ctx.lineWidth = Math.max(1.5, e.width * scale * 0.5)
      ctx.setLineDash(isStair ? [4, 3] : [])
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // Draw routes (green ribbons)
    if (sim?.routes) {
      for (const route of Object.values(sim.routes)) {
        if (route.length < 2) continue
        ctx.strokeStyle = 'rgba(0,220,100,0.35)'
        ctx.lineWidth = 3
        ctx.beginPath()
        let first = true
        for (const nid of route) {
          const n = nodeMap.get(nid)
          if (!n) continue
          const [cx, cy] = toC(n.x, n.z)
          if (first) { ctx.moveTo(cx, cy); first = false }
          else ctx.lineTo(cx, cy)
        }
        ctx.stroke()
      }
    }

    // Draw rooms
    for (const n of building.nodes) {
      if (n.type !== 'room') continue
      const [cx, cy] = toC(n.x, n.z)
      const w = (n.w ?? 6) * scale, d = (n.d ?? 6) * scale
      ctx.fillStyle = 'rgba(255,255,255,0.07)'
      ctx.strokeStyle = 'rgba(255,255,255,0.5)'
      ctx.lineWidth = 1
      ctx.fillRect(cx - w / 2, cy - d / 2, w, d)
      ctx.strokeRect(cx - w / 2, cy - d / 2, w, d)
      ctx.fillStyle = 'rgba(200,200,200,0.7)'
      ctx.font = `${Math.max(8, Math.min(11, scale * 1.2))}px system-ui`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(n.id, cx, cy)
    }

    // Draw corridor nodes
    for (const n of building.nodes) {
      if (n.type !== 'corridor') continue
      const [cx, cy] = toC(n.x, n.z)
      ctx.fillStyle = 'rgba(180,180,180,0.4)'
      ctx.beginPath()
      ctx.arc(cx, cy, 2, 0, Math.PI * 2)
      ctx.fill()
    }

    // Draw exits
    for (const n of building.nodes) {
      if (n.type !== 'exit') continue
      const [cx, cy] = toC(n.x, n.z)
      const isBlocked = blocked.includes(n.id)
      ctx.fillStyle = isBlocked ? '#FF2020' : '#00CC66'
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(cx, cy, 8, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
      if (isBlocked) {
        // draw X
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(cx - 4, cy - 4); ctx.lineTo(cx + 4, cy + 4)
        ctx.moveTo(cx + 4, cy - 4); ctx.lineTo(cx - 4, cy + 4)
        ctx.stroke()
      } else {
        ctx.fillStyle = '#fff'
        ctx.font = '9px system-ui'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(n.id, cx, cy)
      }
      // label below
      ctx.fillStyle = isBlocked ? '#FF8888' : '#88FFAA'
      ctx.font = '9px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(n.label ?? n.id, cx, cy + 14)
    }

    // Mark bottleneck edge
    if (sim?.bottleneck) {
      const parts = sim.bottleneck.split('-')
      // edge_load key is "from-to", try to find the edge
      const bEdge = building.edges.find(e =>
        edgeKey(e.from, e.to) === sim.bottleneck ||
        edgeKey(e.to, e.from) === sim.bottleneck
      )
      if (bEdge) {
        const from = nodeMap.get(bEdge.from), to = nodeMap.get(bEdge.to)
        if (from && to) {
          const [x1, y1] = toC(from.x, from.z)
          const [x2, y2] = toC(to.x, to.z)
          const mx = (x1 + x2) / 2, my = (y1 + y2) / 2
          ctx.fillStyle = '#FF4444'
          ctx.font = 'bold 10px system-ui'
          ctx.textAlign = 'center'
          ctx.fillText('⚠ bottleneck', mx, my - 6)
        }
      }
    }

    // Draw people
    if (frame) {
      const counts: Record<string, number> = {}
      for (const [px, pz, st] of frame.people) {
        if (st === 'out') { counts['out'] = (counts['out'] ?? 0) + 1; continue }
        const [cx, cy] = toC(px, pz)
        ctx.fillStyle = STATE_COLOR[st] ?? '#888'
        ctx.beginPath()
        ctx.arc(cx, cy, 2.5, 0, Math.PI * 2)
        ctx.fill()
        counts[st] = (counts[st] ?? 0) + 1
      }
    }

    // Label
    if (label) {
      ctx.fillStyle = 'rgba(255,255,255,0.6)'
      ctx.font = 'bold 11px system-ui'
      ctx.textAlign = 'left'
      ctx.fillText(label, 8, 16)
    }
  }, [building, sim, frame, blocked, label])

  useEffect(() => { draw() }, [draw])

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    const tr = transformRef.current
    if (!canvas || !tr) return
    const rect = canvas.getBoundingClientRect()
    const cx = (e.clientX - rect.left) * (canvas.width / rect.width)
    const cy = (e.clientY - rect.top) * (canvas.height / rect.height)
    const [wx, wz] = tr.fromC(cx, cy)
    // find nearest exit within 12 world-units
    let best: string | null = null, bestD = 12
    for (const n of building.nodes) {
      if (n.type !== 'exit') continue
      const d = Math.hypot(n.x - wx, n.z - wz)
      if (d < bestD) { bestD = d; best = n.id }
    }
    if (best) onClickExit(best)
  }, [building, onClickExit])

  return (
    <canvas
      ref={canvasRef}
      width={700}
      height={480}
      style={{ width: '100%', height: '100%', cursor: 'crosshair', display: 'block' }}
      onClick={handleClick}
    />
  )
}
