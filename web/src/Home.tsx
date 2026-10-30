import { useEffect, useState } from 'react'
import ExitIcon from './ExitIcon.tsx'
import View3D, { type Building, type Frame } from './View3D.tsx'

type Validation = { published_s: number; ours_s: number; error_pct: number }
type Wow = { building: string; blocked: string; people: number; nearest_s: number; nikaas_s: number; pct_saved: number; gap_s: number; lower_bound_s: number }
type Run = { frames: Frame[]; door_routes?: Record<string, string[][]>; bottleneck?: string; peak_queue?: number }

// Every number on this page is loaded from files generated out of runs/ (scripts/report.py,
// scripts/run_validation.py), so it cannot show a number we did not measure.
export default function Home() {
  const [val, setVal] = useState<Validation>()
  const [wow, setWow] = useState<Wow[]>([])
  const [building, setBuilding] = useState<Building>()
  const [run, setRun] = useState<Run>()
  const [i, setI] = useState(0)

  useEffect(() => {
    fetch('data/validation.json').then(r => r.json()).then(setVal).catch(() => {})
    fetch('data/wow.json').then(r => r.json()).then(setWow).catch(() => {})
    fetch('data/iit_kgp_museum.json').then(r => r.json()).then(setBuilding).catch(() => {})
    fetch('data/frames_iit_kgp_nikaas.json').then(r => r.json()).then(setRun).catch(() => {})
  }, [])
  useEffect(() => {
    if (!run) return
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) { setI(Math.floor(run.frames.length / 3)); return }
    const id = setInterval(() => setI(k => (k + 1) % run.frames.length), 160)
    return () => clearInterval(id)
  }, [run])

  const w = (b: string, blocked = '') => wow.find(x => x.building === b && x.blocked === blocked)
  const lab = w('lab_block.json'), iit = w('iit_kgp_museum.json'), iitB = w('iit_kgp_museum.json', 'MAIN')

  return (
    <div className="page">
      <section className="hero">
        <div className="hero-text">
          <div className="exit-sign">
            <ExitIcon />
            <h1>Photograph the exit map.<br />Get everyone out faster.</h1>
          </div>
          <p className="lede">
            Nikaas turns a photo of a building’s evacuation map into a working model of every room, door and stair.
            It times how long people take to get out, finds where they jam, and gives each room the exit that empties the
            building fastest, even when a stair is blocked.
          </p>
          <div className="cta-row">
            <a className="cta" href="#/twin">Block an exit and watch</a>
            <a className="cta quiet" href="#/challenge">Try to beat the plan</a>
          </div>
        </div>
        <figure className="model-stage" style={{ margin: 0 }}>
          {building && <View3D building={building} frame={run?.frames[i]} blocked={[]} routes={run?.door_routes}
            bottleneck={run?.bottleneck} peakQueue={run?.peak_queue} onExit={() => { location.hash = '#/twin' }} height={520} />}
          <figcaption className="model-caption">
            The Nehru Museum of Science & Technology floor at IIT Kharagpur, rebuilt from the floor plan on its wall.
            Orange figures follow the Nikaas plan along the green routes.
          </figcaption>
        </figure>
      </section>

      <section className="incidents" aria-label="Why this matters">
        <div><b>22</b><p>students died in the 2019 Surat coaching-centre fire after the escape stair burned.</p></div>
        <div><b>23</b><p>people died on one overloaded footbridge at Elphinstone Road, Mumbai, in 2017.</p></div>
        <div><b>11</b><p>people were killed outside Chinnaswamy Stadium, Bengaluru, on 4 June 2025.</p></div>
      </section>
      <p className="sources">Sources: Wikipedia articles on each incident; Hindustan Times; CNN; India Today.</p>

      <section style={{ marginTop: 72 }}>
        <h2>From a photo on the wall to a plan that holds up</h2>
        <ol className="steps">
          <li><h3>Photograph the map</h3><p>Any posted evacuation plan. A vision model reads rooms, corridors and exits from the photo.</p></li>
          <li><h3>Check the building</h3><p>A validator rejects a graph with a room that cannot reach an exit, before any number is trusted.</p></li>
          <li><h3>Simulate every person</h3><p>Doors, corridors and stairs pass only as many people per second as their width allows (SFPE method).</p></li>
          <li><h3>Plan and re-plan</h3><p>Each room gets an exit. Block a stair and the plan is rebuilt in seconds.</p></li>
        </ol>
      </section>

      <section style={{ marginTop: 72 }}>
        <h2>Measured, not promised</h2>
        <div className="proof">
          <div>
            <div className="big green">{lab ? `${lab.pct_saved}%` : '…'}</div>
            <p>{lab ? `faster movement out of a ${lab.people}-person lab block: ${lab.nearest_s} s with the nearest-exit rule, ${lab.nikaas_s} s with the Nikaas plan, ${lab.gap_s} s above the proven lower bound.` : ''}</p>
          </div>
          <div>
            <div className="big">{iit && iitB ? `${iitB.nikaas_s} s` : '…'}</div>
            <p>{iit && iitB ? `for the IIT Kharagpur floor with its main entrance blocked, down from ${iitB.nearest_s} s. All exits open: ${iit.nearest_s} s to ${iit.nikaas_s} s.` : ''}</p>
          </div>
          <div>
            <div className="big">{val ? `${val.ours_s} s` : '…'}</div>
            <p>{val ? `against ${val.published_s} s in the SFPE handbook’s worked example, a ${val.error_pct}% difference.` : ''}</p>
          </div>
        </div>
        <p className="sources">Times are movement times, the part an exit plan can change. Method and sources on the Evidence page.</p>
      </section>

      <section className="closing">
        <h2>Your building has a map on the wall.</h2>
        <a className="cta" href="#/twin">Open the twin</a>
      </section>
    </div>
  )
}
