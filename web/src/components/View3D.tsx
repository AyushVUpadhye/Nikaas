import { useRef, useEffect } from 'react'
import * as THREE from 'three'
import type { Building, SimResult, Frame } from '../types'

const STATE_COLOR3: Record<string, number> = {
  walking: 0xFF8C00,
  queuing: 0xFF3030,
  stairs: 0x4488FF,
  inside: 0x888888,
  out: 0x333333,
}

interface Props {
  building: Building
  sim: SimResult | null
  frame: Frame | null
  blocked: string[]
}

export default function View3D({ building, sim, frame, blocked }: Props) {
  const mountRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<{
    renderer: THREE.WebGLRenderer
    scene: THREE.Scene
    camera: THREE.PerspectiveCamera
    people: THREE.Mesh[]
    peopleMat: THREE.MeshStandardMaterial[]
    raf: number
  } | null>(null)

  // Init scene once
  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const w = mount.clientWidth, h = mount.clientHeight
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(w, h)
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.shadowMap.enabled = true
    mount.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0d0d0d)
    scene.fog = new THREE.Fog(0x0d0d0d, 60, 120)

    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 200)
    camera.position.set(0, 40, 50)
    camera.lookAt(0, 0, 10)

    // Ambient + directional light
    scene.add(new THREE.AmbientLight(0xffffff, 0.4))
    const dir = new THREE.DirectionalLight(0xffffff, 1.2)
    dir.position.set(10, 30, 20)
    dir.castShadow = true
    scene.add(dir)

    // Floor
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(120, 80),
      new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.9 })
    )
    floor.rotation.x = -Math.PI / 2
    floor.position.set(0, 0, 20)
    floor.receiveShadow = true
    scene.add(floor)

    const nodeMap = new Map(building.nodes.map(n => [n.id, n]))

    // Rooms as white boxes
    for (const n of building.nodes) {
      if (n.type !== 'room') continue
      const wallH = 2.8
      const geom = new THREE.BoxGeometry(n.w ?? 6, wallH, n.d ?? 6)
      const mat = new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: 0.6 })
      const mesh = new THREE.Mesh(geom, mat)
      mesh.position.set(n.x, wallH / 2, n.z)
      mesh.castShadow = true
      mesh.receiveShadow = true
      scene.add(mesh)
      // edges outline
      const edges = new THREE.EdgesGeometry(geom)
      const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 1 }))
      line.position.copy(mesh.position)
      scene.add(line)
    }

    // Route ribbons (green lines)
    if (sim?.routes) {
      for (const route of Object.values(sim.routes)) {
        if (route.length < 2) continue
        const pts: THREE.Vector3[] = []
        for (const nid of route) {
          const n = nodeMap.get(nid)
          if (n) pts.push(new THREE.Vector3(n.x, 0.15, n.z))
        }
        const geom = new THREE.BufferGeometry().setFromPoints(pts)
        const mat = new THREE.LineBasicMaterial({ color: 0x00DD66, linewidth: 2 })
        scene.add(new THREE.Line(geom, mat))
      }
    }

    // Exits
    for (const n of building.nodes) {
      if (n.type !== 'exit') continue
      const isBlocked = blocked.includes(n.id)
      const color = isBlocked ? 0xFF2020 : 0x00CC66
      const pillar = new THREE.Mesh(
        new THREE.CylinderGeometry(0.5, 0.5, 3, 8),
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.4 })
      )
      pillar.position.set(n.x, 1.5, n.z)
      scene.add(pillar)
      if (isBlocked) {
        // Cross on top
        for (const angle of [0, Math.PI / 2]) {
          const bar = new THREE.Mesh(
            new THREE.BoxGeometry(1.4, 0.2, 0.2),
            new THREE.MeshStandardMaterial({ color: 0xffffff })
          )
          bar.position.set(n.x, 3.2, n.z)
          bar.rotation.y = angle
          scene.add(bar)
        }
      }
    }

    // People (will be updated per frame)
    const maxPeople = building.nodes.reduce((s, n) => s + (n.people ?? 0), 0) + 50
    const sphereGeom = new THREE.SphereGeometry(0.25, 6, 6)
    const people: THREE.Mesh[] = []
    const peopleMat: THREE.MeshStandardMaterial[] = []
    for (let i = 0; i < maxPeople; i++) {
      const mat = new THREE.MeshStandardMaterial({ color: 0x888888 })
      const mesh = new THREE.Mesh(sphereGeom, mat)
      mesh.visible = false
      mesh.castShadow = true
      scene.add(mesh)
      people.push(mesh)
      peopleMat.push(mat)
    }

    // Simple orbit via mouse drag
    let dragging = false, prevX = 0, prevY = 0
    let theta = 0, phi = 0.5, radius = 65
    const onMouseDown = (e: MouseEvent) => { dragging = true; prevX = e.clientX; prevY = e.clientY }
    const onMouseUp = () => { dragging = false }
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging) return
      theta -= (e.clientX - prevX) * 0.005
      phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, phi + (e.clientY - prevY) * 0.005))
      prevX = e.clientX; prevY = e.clientY
      camera.position.set(
        radius * Math.sin(theta) * Math.sin(phi),
        radius * Math.cos(phi),
        radius * Math.cos(theta) * Math.sin(phi) + 10
      )
      camera.lookAt(0, 0, 10)
    }
    const onWheel = (e: WheelEvent) => {
      radius = Math.max(20, Math.min(100, radius + e.deltaY * 0.05))
      camera.position.set(
        radius * Math.sin(theta) * Math.sin(phi),
        radius * Math.cos(phi),
        radius * Math.cos(theta) * Math.sin(phi) + 10
      )
      camera.lookAt(0, 0, 10)
    }
    mount.addEventListener('mousedown', onMouseDown)
    window.addEventListener('mouseup', onMouseUp)
    window.addEventListener('mousemove', onMouseMove)
    mount.addEventListener('wheel', onWheel, { passive: true })

    // Resize
    const onResize = () => {
      const w = mount.clientWidth, h = mount.clientHeight
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    window.addEventListener('resize', onResize)

    const raf = requestAnimationFrame(function loop() {
      renderer.render(scene, camera)
      sceneRef.current!.raf = requestAnimationFrame(loop)
    })

    sceneRef.current = { renderer, scene, camera, people, peopleMat, raf }

    return () => {
      cancelAnimationFrame(raf)
      mount.removeEventListener('mousedown', onMouseDown)
      window.removeEventListener('mouseup', onMouseUp)
      window.removeEventListener('mousemove', onMouseMove)
      mount.removeEventListener('wheel', onWheel)
      window.removeEventListener('resize', onResize)
      renderer.dispose()
      mount.removeChild(renderer.domElement)
      sceneRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [building.name])

  // Update people each frame
  useEffect(() => {
    const s = sceneRef.current
    if (!s || !frame) return
    const { people, peopleMat } = s
    for (let i = 0; i < people.length; i++) {
      if (i < frame.people.length) {
        const [px, pz, st] = frame.people[i]
        if (st === 'out') { people[i].visible = false; continue }
        people[i].visible = true
        people[i].position.set(px, 0.5, pz)
        peopleMat[i].color.setHex(STATE_COLOR3[st] ?? 0x888888)
      } else {
        people[i].visible = false
      }
    }
  }, [frame])

  return (
    <div
      ref={mountRef}
      style={{ width: '100%', height: '100%', cursor: 'grab' }}
    />
  )
}
