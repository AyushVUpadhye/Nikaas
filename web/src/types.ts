export interface BNode {
  id: string
  type: 'room' | 'corridor' | 'exit'
  x: number
  z: number
  w?: number
  d?: number
  people?: number
  label?: string
}

export interface BEdge {
  from: string
  to: string
  width: number
  kind?: 'door' | 'corridor' | 'stair'
}

export interface Building {
  name: string
  nodes: BNode[]
  edges: BEdge[]
}

export type PState = 'inside' | 'walking' | 'queuing' | 'stairs' | 'out'

export interface Frame {
  t: number
  people: [number, number, PState][]
}

export interface SimResult {
  total_time_s: number
  completed: boolean
  people: number
  per_exit: Record<string, number>
  bottleneck: string
  peak_queue: number
  edge_load: Record<string, number>
  routes: Record<string, string[]>
  plan: Record<string, string>
  frames: Frame[]
}
