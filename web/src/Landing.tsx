import { useEffect, useState } from 'react'

type Validation = { published_s: number; ours_s: number; error_pct: number }
type Wow = { building: string; blocked: string; nearest_s: number; nikaas_s: number; pct_saved: number; gap_s: number }

// Landing section. Every number is loaded from data generated out of runs/ (scripts/report.py,
// scripts/run_validation.py), so the page cannot show a number we did not measure.
export default function Landing() {
  const [val, setVal] = useState<Validation>()
  const [wow, setWow] = useState<Wow[]>([])
  useEffect(() => {
    fetch('data/validation.json').then(r => r.json()).then(setVal).catch(() => {})
    fetch('data/wow.json').then(r => r.json()).then(setWow).catch(() => {})
  }, [])
  const w = (b: string, blocked = '') => wow.find(x => x.building === b && x.blocked === blocked)
  const labW = w('lab_block.json'), iitW = w('iit_kgp_museum.json'), iitWB = w('iit_kgp_museum.json', 'MAIN')

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
        <Stat big={labW ? `${labW.pct_saved}% faster` : '…'} label={labW ? `Nikaas plan on a 528-person lab block: ${labW.nearest_s} s → ${labW.nikaas_s} s, within ${labW.gap_s} s of the proven fastest possible` : ''} />
        <Stat big={iitW ? `${iitW.nearest_s} → ${iitW.nikaas_s} s` : '…'} label="IIT Kharagpur museum floor, nearest-exit rule vs Nikaas plan" />
        <Stat big={iitWB ? `${iitWB.nearest_s} → ${iitWB.nikaas_s} s` : '…'} label="same floor with the main entrance blocked, Nikaas re-plans" />
        <Stat big={val ? `${val.ours_s} s` : '…'} label={val ? `vs ${val.published_s} s in the SFPE handbook's worked example (${val.error_pct}% off)` : 'validation'} />
      </div>

      <div className="features">
        <div><h3>From a photo</h3><p>A posted exit map becomes a graph of rooms, doors, corridors and stairs, checked by a validator before any simulation.</p></div>
        <div><h3>Break it yourself</h3><p>Block any exit and the evacuation is re-simulated live on AWS, with the new bottleneck and the time it costs.</p></div>
        <div><h3>Physics you can check</h3><p>Flow limits per metre of door and stair width from the SFPE hydraulic model, reproduced against the handbook example.</p></div>
      </div>

      <details className="faq"><summary>Is the building real?</summary>
        <p>The floor plan is a real posted panel at IIT Kharagpur. Its scale, room occupancy and door widths are our assumptions, listed in the repository.</p></details>
      <details className="faq"><summary>Is this the full evacuation time?</summary>
        <p>No. Our times are movement times, the part an exit plan can change. A full escape time also includes detection,
          alarm and the time people take to react before moving (SFPE Handbook; BSI PD 7974-6), which the plan does not change,
          so we leave them out instead of guessing. Details: docs/METHOD.md.</p></details>
      <details className="faq"><summary>How do we know the times are right?</summary>
        <p>The simulator reproduces the SFPE Engineering Guide's Example 1 hand calculation; the test runs on every change.</p></details>
    </section>
  )
}

function Stat({ big, label }: { big: string; label: string }) {
  return <div className="stat"><div className="big">{big}</div><div className="label">{label}</div></div>
}
