import { useEffect, useState } from 'react'

type Result = { building: string; blocked: string; total_time_s: number; people: number; bottleneck: string }
type Validation = { published_s: number; ours_s: number; error_pct: number }

// Landing section. Every number is loaded from data generated out of runs/ (scripts/report.py,
// scripts/run_validation.py), so the page cannot show a number we did not measure.
export default function Landing() {
  const [results, setResults] = useState<Result[]>([])
  const [val, setVal] = useState<Validation>()
  useEffect(() => {
    fetch('data/results.json').then(r => r.json()).then(setResults).catch(() => {})
    fetch('data/validation.json').then(r => r.json()).then(setVal).catch(() => {})
  }, [])
  const find = (b: string, blocked = '') => results.find(r => r.building === b && r.blocked === blocked)
  const iit = find('iit_kgp_museum.json'), iitMain = find('iit_kgp_museum.json', 'MAIN')
  const lab = find('lab_block.json'), labA = find('lab_block.json', 'A')

  return (
    <section className="landing">
      <div className="hero">
        <div>
          <p className="eyebrow">Evacuation digital twin · Theme 03</p>
          <h2 className="statement">Photograph the exit map.<br />Get everyone out faster.</h2>
          <p className="lede">
            Every building has an evacuation map on the wall. It says “go to the nearest exit”, so everyone
            runs to the same stair. Nikaas turns a photo of that map into a live model, finds the bottleneck,
            and shows what happens when an exit is blocked.
          </p>
          <a className="cta" href="#try">Try it: block an exit</a>
        </div>
        <figure className="mapshot">
          <img src="data/iit_kgp_nmst_block_b.jpg" alt="Posted floor-plan panel of the Nehru Museum of Science and Technology, IIT Kharagpur" />
          <figcaption>The map we started from: a posted floor plan at IIT Kharagpur. Photo: Biswarup Ganguly, CC BY 3.0, Wikimedia Commons.</figcaption>
        </figure>
      </div>

      <div className="incidents">
        <div><b>22</b> students died in the 2019 Surat coaching-centre fire when the escape stair burned.</div>
        <div><b>23</b> people died on one overloaded footbridge at Elphinstone Road, Mumbai, 2017.</div>
        <div><b>11</b> people were killed outside Chinnaswamy Stadium, Bengaluru, 4 June 2025.</div>
      </div>

      <div className="stats">
        <Stat big={val ? `${val.ours_s} s` : '…'} label={val ? `vs ${val.published_s} s in the SFPE handbook's worked example (${val.error_pct}% off)` : 'validation'} />
        <Stat big={iit ? `${iit.total_time_s} s` : '…'} label={iit ? `to evacuate ${iit.people} people from the IIT Kharagpur museum floor, nearest-exit rule` : ''} />
        <Stat big={iit && iitMain ? `+${(iitMain.total_time_s - iit.total_time_s).toFixed(1)} s` : '…'} label="if the main entrance is blocked" />
        <Stat big={lab && labA ? `${(labA.total_time_s - lab.total_time_s).toFixed(1)} s` : '…'} label={lab && labA ? `on a lab block, closing a stair beats the nearest-exit rule (${labA.total_time_s} s vs ${lab.total_time_s} s)` : ''} />
      </div>

      <div className="features">
        <div><h3>From a photo</h3><p>A posted exit map becomes a graph of rooms, doors, corridors and stairs, checked by a validator before any simulation.</p></div>
        <div><h3>Break it yourself</h3><p>Block any exit and the evacuation is re-simulated live on AWS, with the new bottleneck and the time it costs.</p></div>
        <div><h3>Physics you can check</h3><p>Flow limits per metre of door and stair width from the SFPE hydraulic model, reproduced against the handbook example.</p></div>
      </div>

      <details className="faq"><summary>Is the building real?</summary>
        <p>The floor plan is a real posted panel at IIT Kharagpur. Its scale, room occupancy and door widths are our assumptions, listed in the repository.</p></details>
      <details className="faq"><summary>How do we know the times are right?</summary>
        <p>The simulator reproduces the SFPE Engineering Guide's Example 1 hand calculation; the test runs on every change.</p></details>
    </section>
  )
}

function Stat({ big, label }: { big: string; label: string }) {
  return <div className="stat"><div className="big">{big}</div><div className="label">{label}</div></div>
}
