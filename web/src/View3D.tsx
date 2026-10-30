/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from './vendor/three/OrbitControls.js'

type Node = { id: string; type: 'room' | 'corridor' | 'exit'; x: number; z: number; w?: number; d?: number; label?: string }
export type Building = { name: string; nodes: Node[]; edges: { from: string; to: string; width: number; kind?: string }[] }
export type Frame = { t: number; people: [number, number, string][] }

type Props = {
  building: Building
  frame?: Frame
  blocked: string[]
  routes?: Record<string, string[][]>
  edgeLoad?: Record<string, number>
  bottleneck?: string
  peakQueue?: number
  onExit: (id: string) => void
}

// Look rules: docs/VISUAL_STYLE.md. White architectural model on a dark floor; colour only on
// people (state), escape routes (green) and danger (red).
const WALL_H = 1.3, WALL_T = 0.18
const STATE_COLOR: Record<string, string> = { walking: '#f26a2e', queuing: '#c81e1e', stairs: '#2563eb', inside: '#8a939b' }

export default function View3D({ building, frame, blocked, routes, edgeLoad, bottleneck, peakQueue, onExit }: Props) {
  const host = useRef<HTMLDivElement>(null)
  const api = useRef<any>({})

  // build the static scene once per building
  useEffect(() => {
    const el = host.current
    if (!el) return
    const W = el.clientWidth, H = 560
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio))
    renderer.setSize(W, H)
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.outputColorSpace = THREE.SRGBColorSpace
    el.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#e8ecef')
    const xs = building.nodes.map(n => n.x), zs = building.nodes.map(n => n.z)
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cz = (Math.min(...zs) + Math.max(...zs)) / 2
    const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...zs) - Math.min(...zs)) + 14
    scene.fog = new THREE.Fog('#e8ecef', span * 1.4, span * 3)

    scene.add(new THREE.HemisphereLight('#ffffff', '#9aa3ab', 1.2))
    const sun = new THREE.DirectionalLight('#fff7ee', 2.0)
    sun.position.set(cx - span * 0.4, span, cz + span * 0.5)
    sun.target.position.set(cx, 0, cz)
    sun.castShadow = true
    sun.shadow.mapSize.set(2048, 2048)
    Object.assign(sun.shadow.camera, { left: -span, right: span, top: span, bottom: -span, near: 1, far: span * 4 })
    scene.add(sun, sun.target)

    const mat = (c: string) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85 })
    const white = mat('#f3f4f5'), floorMat = mat('#3b3f45'), walkMat = mat('#4a4f56')
    const box = (w: number, h: number, d: number, m: any, x: number, y: number, z: number) => {
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m)
      b.position.set(x, y, z); b.castShadow = true; b.receiveShadow = true; scene.add(b); return b
    }
    const slab = new THREE.Mesh(new THREE.PlaneGeometry(span + 10, span * 0.75 + 10), floorMat)
    slab.rotation.x = -Math.PI / 2; slab.position.set(cx, 0, cz); slab.receiveShadow = true; scene.add(slab)

    const byId = Object.fromEntries(building.nodes.map(n => [n.id, n]))
    // walkways between corridor / exit points, as slightly lighter floor strips (one material each: jams turn red)
    const strips: Record<string, any> = {}
    for (const e of building.edges) {
      const a = byId[e.from], b = byId[e.to]
      if (a.type === 'room' || b.type === 'room') continue
      const len = Math.hypot(b.x - a.x, b.z - a.z)
      if (len < 0.01) continue
      const strip = new THREE.Mesh(new THREE.PlaneGeometry(len + e.width, e.width), walkMat.clone())
      strips[`${e.from}-${e.to}`] = strip; strips[`${e.to}-${e.from}`] = strip
      strip.rotation.x = -Math.PI / 2; strip.rotation.z = -Math.atan2(b.z - a.z, b.x - a.x)
      strip.position.set((a.x + b.x) / 2, 0.01, (a.z + b.z) / 2); strip.receiveShadow = true; scene.add(strip)
    }
    // rooms: four low white walls, with a gap on the side facing each door
    const label = (text: string, x: number, z: number, size = 1.1) => {
      const c = document.createElement('canvas'); c.width = 512; c.height = 96
      const g = c.getContext('2d')!; g.fillStyle = '#c9ced3'; g.font = '600 44px Segoe UI'; g.textAlign = 'center'; g.fillText(text, 256, 62, 500)
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace
      const m = new THREE.Mesh(new THREE.PlaneGeometry(size * 5.3, size), new THREE.MeshBasicMaterial({ map: t, transparent: true }))
      m.rotation.x = -Math.PI / 2; m.position.set(x, 0.03, z); scene.add(m)
    }
    for (const r of building.nodes.filter(n => n.type === 'room')) {
      const w = r.w ?? 4, d = r.d ?? 4, x0 = r.x - w / 2, x1 = r.x + w / 2, z0 = r.z - d / 2, z1 = r.z + d / 2
      const gaps: Record<string, [number, number][]> = { N: [], S: [], W: [], E: [] }
      for (const e of building.edges) {
        const other = e.from === r.id ? byId[e.to] : e.to === r.id ? byId[e.from] : undefined
        if (!other) continue
        const dx = (other.x - r.x) / w, dz = (other.z - r.z) / d
        const side = Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 'E' : 'W') : (dz > 0 ? 'S' : 'N')
        const along = side === 'E' || side === 'W' ? Math.min(z1 - 0.6, Math.max(z0 + 0.6, other.z)) : Math.min(x1 - 0.6, Math.max(x0 + 0.6, other.x))
        gaps[side].push([along - e.width / 2 - 0.2, along + e.width / 2 + 0.2])
      }
      const wall = (a: number, b: number, fixed: number, horiz: boolean, cuts: [number, number][]) => {
        let s = a
        for (const [g0, g1] of cuts.sort((p, q) => p[0] - q[0])) {
          if (g0 > s) horiz ? box(g0 - s, WALL_H, WALL_T, white, (s + g0) / 2, WALL_H / 2, fixed) : box(WALL_T, WALL_H, g0 - s, white, fixed, WALL_H / 2, (s + g0) / 2)
          s = Math.max(s, g1)
        }
        if (b > s) horiz ? box(b - s, WALL_H, WALL_T, white, (s + b) / 2, WALL_H / 2, fixed) : box(WALL_T, WALL_H, b - s, white, fixed, WALL_H / 2, (s + b) / 2)
      }
      wall(x0, x1, z0, true, gaps.N); wall(x0, x1, z1, true, gaps.S); wall(z0, z1, x0, false, gaps.W); wall(z0, z1, x1, false, gaps.E)
      const fl = new THREE.Mesh(new THREE.PlaneGeometry(w, d), mat('#454a51'))
      fl.rotation.x = -Math.PI / 2; fl.position.set(r.x, 0.015, r.z); fl.receiveShadow = true; scene.add(fl)
      label(r.label ?? r.id, r.x, r.z - d / 2 + 0.9, Math.min(1.1, w / 5.6))
    }
    // exits: a post with a sign, clickable
    const exitMeshes: any[] = []
    for (const x of building.nodes.filter(n => n.type === 'exit')) {
      const sign = box(1.8, 0.7, 0.15, new THREE.MeshStandardMaterial({ color: '#16a34a', emissive: '#16a34a', emissiveIntensity: 0.35 }), x.x, 2.2, x.z)
      box(0.15, 2.0, 0.15, white, x.x, 1.0, x.z)
      const pad = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 0.06, 32), new THREE.MeshStandardMaterial({ color: '#16a34a', transparent: true, opacity: 0.6 }))
      pad.position.set(x.x, 0.04, x.z); scene.add(pad)
      sign.userData.exit = x.id; pad.userData.exit = x.id
      exitMeshes.push(sign, pad)
      label(x.label ?? x.id, x.x, x.z + 2.2, 1.0)
    }

    // people: simple human figures (body + head), instanced
    const N = Math.max(1, building.nodes.reduce((s, n: any) => s + (n.people ?? 0), 0))
    const body = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.17, 0.22, 1.15, 8), new THREE.MeshStandardMaterial({ roughness: 0.6 }), N)
    const head = new THREE.InstancedMesh(new THREE.SphereGeometry(0.15, 10, 8), mat('#d9a17c'), N)
    body.castShadow = head.castShadow = true
    body.frustumCulled = head.frustumCulled = false // instances move far from the origin; default culling hides them
    scene.add(body, head)

    const routeGroup = new THREE.Group(); scene.add(routeGroup)
    // bottleneck marker: pulsing red ring on the floor + a floating label, moved to the worst jam per run
    const marker = new THREE.Group(); marker.visible = false; scene.add(marker)
    const ring = new THREE.Mesh(new THREE.RingGeometry(2.2, 2.7, 48), new THREE.MeshBasicMaterial({ color: '#c81e1e', transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false }))
    ring.rotation.x = -Math.PI / 2; ring.position.y = 0.07; marker.add(ring)
    const tagCanvas = document.createElement('canvas'); tagCanvas.width = 512; tagCanvas.height = 128
    const tagTex = new THREE.CanvasTexture(tagCanvas); tagTex.colorSpace = THREE.SRGBColorSpace
    const tag = new THREE.Sprite(new THREE.SpriteMaterial({ map: tagTex, depthTest: false })); tag.scale.set(13, 3.25, 1); tag.position.y = 5.5; marker.add(tag)

    const camera = new THREE.PerspectiveCamera(35, W / H, 0.5, span * 6)
    camera.position.set(cx + span * 0.05, span * 0.8, cz + span * 0.95)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.target.set(cx, 0, cz); controls.enableDamping = true; controls.maxPolarAngle = Math.PI * 0.45; controls.update()

    const ray = new THREE.Raycaster(), mouse = new THREE.Vector2()
    let downAt = 0
    renderer.domElement.addEventListener('pointerdown', () => { downAt = performance.now() })
    renderer.domElement.addEventListener('pointerup', (ev: PointerEvent) => {
      if (performance.now() - downAt > 250) return // a drag to orbit, not a click
      const r = renderer.domElement.getBoundingClientRect()
      mouse.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1)
      ray.setFromCamera(mouse, camera)
      const hit = ray.intersectObjects(exitMeshes)[0]
      if (hit) api.current.onExit?.(hit.object.userData.exit)
    })

    let raf = 0
    // smooth motion: every render frame, people glide toward their latest simulated position
    const M = new THREE.Matrix4(), hide = new THREE.Matrix4().makeScale(0, 0, 0)
    let last = performance.now()
    const loop = () => {
      const now = performance.now(), dt = Math.min(0.1, (now - last) / 1000); last = now
      const a = api.current, k = 1 - Math.exp(-dt * 6)
      if (a.target) {
        for (let n = 0; n < N; n++) {
          const tg = a.target[n]
          if (!tg) { body.setMatrixAt(n, hide); head.setMatrixAt(n, hide); continue }
          const c = a.cur[n] ?? (a.cur[n] = [tg[0], tg[1]])
          const jump = Math.hypot(tg[0] - c[0], tg[1] - c[1]) > 25 // new run or restart: snap, do not slide across the map
          c[0] = jump ? tg[0] : c[0] + (tg[0] - c[0]) * k; c[1] = jump ? tg[1] : c[1] + (tg[1] - c[1]) * k
          const moving = tg[2] === 'walking' || tg[2] === 'stairs'
          const bob = moving ? Math.abs(Math.sin(now / 140 + n)) * 0.05 : 0
          body.setMatrixAt(n, M.makeTranslation(c[0], 0.58 + bob, c[1]))
          head.setMatrixAt(n, M.makeTranslation(c[0], 1.3 + bob, c[1]))
        }
        body.instanceMatrix.needsUpdate = true; head.instanceMatrix.needsUpdate = true
      }
      if (marker.visible) { const k = 1 + 0.12 * Math.sin(now / 250); ring.scale.set(k, k, k) }
      controls.update(); renderer.render(scene, camera); raf = requestAnimationFrame(loop)
    }
    loop()
    const ro = new ResizeObserver(() => {
      const w = el.clientWidth; renderer.setSize(w, H); camera.aspect = w / H; camera.updateProjectionMatrix()
    })
    ro.observe(el)

    api.current = { ...api.current, scene, body, head, exitMeshes, routeGroup, byId, N, strips, marker, tagCanvas, tagTex, cur: [], target: undefined }
    return () => { cancelAnimationFrame(raf); ro.disconnect(); renderer.dispose(); el.removeChild(renderer.domElement) }
  }, [building])

  useEffect(() => { api.current.onExit = onExit }, [onExit])

  // blocked exits turn red
  useEffect(() => {
    for (const m of api.current.exitMeshes ?? []) {
      const off = blocked.includes(m.userData.exit)
      m.material.color.set(off ? '#c81e1e' : '#16a34a')
      if (m.material.emissive) m.material.emissive.set(off ? '#c81e1e' : '#16a34a')
    }
  }, [blocked, building])

  // escape routes: green ribbons from each door to its exit
  useEffect(() => {
    const { routeGroup, byId } = api.current
    if (!routeGroup) return
    routeGroup.clear()
    const m = new THREE.MeshBasicMaterial({ color: '#22c55e', transparent: true, opacity: 0.7, depthWrite: false })
    for (const paths of Object.values(routes ?? {})) for (const path of paths) {
      for (let k = 1; k < path.length; k++) {
        const a = byId[path[k - 1]], b = byId[path[k]]
        if (!a || !b) continue // run from another building: skip
        const len = Math.hypot(b.x - a.x, b.z - a.z)
        if (len < 0.01) continue
        const r = new THREE.Mesh(new THREE.PlaneGeometry(len, 0.35), m)
        r.rotation.x = -Math.PI / 2; r.rotation.z = -Math.atan2(b.z - a.z, b.x - a.x)
        r.position.set((a.x + b.x) / 2, 0.05, (a.z + b.z) / 2); routeGroup.add(r)
      }
    }
  }, [routes, building])

  // jammed walkways glow red by their peak queue (same rule as the 2D view)
  useEffect(() => {
    const strips = api.current.strips as Record<string, any> | undefined
    if (!strips) return
    const peak = Math.max(1, ...Object.values(edgeLoad ?? {}))
    const base = new THREE.Color('#4a4f56'), red = new THREE.Color('#c81e1e')
    for (const [key, m] of Object.entries(strips)) {
      const jam = Math.min(1, (edgeLoad?.[key] ?? 0) / peak)
      m.material.color.copy(base).lerp(red, jam > 0.15 ? 0.3 + 0.7 * jam : 0)
    }
  }, [edgeLoad, building])

  useEffect(() => {
    const { marker, tagCanvas, tagTex, byId } = api.current
    if (!marker) return
    const [a, b] = (bottleneck ?? '').split('-').length === 2 ? (bottleneck as string).split('-') : [undefined, undefined]
    const na = a && byId[a], nb = b && byId[b]
    // node ids can contain '-' (e.g. m-34); fall back to matching edge keys
    let A = na, B = nb
    if (!(A && B) && bottleneck) for (const id of Object.keys(byId)) if (bottleneck.startsWith(id + '-') && byId[bottleneck.slice(id.length + 1)]) { A = byId[id]; B = byId[bottleneck.slice(id.length + 1)] }
    if (!A || !B) { marker.visible = false; return }
    marker.position.set((A.x + B.x) / 2, 0, (A.z + B.z) / 2); marker.visible = true
    const g = tagCanvas.getContext('2d')!
    g.clearRect(0, 0, 512, 128); g.fillStyle = 'rgba(200,30,30,0.92)'; g.fillRect(0, 16, 512, 96)
    g.fillStyle = '#fff'; g.font = '600 46px Segoe UI'; g.textAlign = 'center'; g.fillText(`Bottleneck · queue ${peakQueue ?? ''}`, 256, 80)
    tagTex.needsUpdate = true
  }, [bottleneck, peakQueue, building])

  // latest simulated positions and colours; the render loop glides people toward them
  useEffect(() => {
    const { body, N } = api.current
    if (!body) return
    const C = new THREE.Color(), ppl = frame?.people ?? []
    const target: ([number, number, string] | undefined)[] = new Array(N)
    for (let k = 0; k < N; k++) {
      const p = ppl[k]
      if (!p || p[2] === 'out') { api.current.cur[k] = undefined; continue }
      target[k] = p
      body.setColorAt(k, C.set(STATE_COLOR[p[2]] ?? '#8a939b'))
    }
    api.current.target = target
    if (body.instanceColor) body.instanceColor.needsUpdate = true
  }, [frame])

  return <div ref={host} style={{ width: '100%', height: 560, background: '#e8ecef', border: '1px solid var(--line)', cursor: 'grab' }} />
}
