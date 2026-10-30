import React, { useEffect, useState } from 'react'
import ExitIcon from './ExitIcon.tsx'
import Home from './Home.tsx'
import App from './App.tsx'
import Challenge from './Challenge.tsx'
import Evidence from './Evidence.tsx'

// Hash routes so the site works from a plain S3 bucket with no server rewrites.
const PAGES: Record<string, { label: string; render: () => React.ReactElement }> = {
  '': { label: 'Home', render: () => <Home /> },
  twin: { label: 'Twin', render: () => <App /> },
  challenge: { label: 'Beat Nikaas', render: () => <Challenge /> },
  evidence: { label: 'Evidence', render: () => <Evidence /> },
}
const routeOf = () => location.hash.replace(/^#\/?/, '').split('?')[0]

export default function Shell() {
  const [route, setRoute] = useState(routeOf())
  useEffect(() => {
    const on = () => { setRoute(routeOf()); window.scrollTo(0, 0) }
    addEventListener('hashchange', on)
    return () => removeEventListener('hashchange', on)
  }, [])
  // ?demo=1 (the video story): Home for 4 s, then the twin plays the scripted story
  useEffect(() => {
    if (!new URLSearchParams(location.search).has('demo') || routeOf()) return
    const t = setTimeout(() => { location.hash = '#/twin' }, 4000)
    return () => clearTimeout(t)
  }, [])
  const page = PAGES[route] ?? PAGES['']
  return (
    <>
      <header className="nav">
        <a className="brand" href="#/"><ExitIcon color="var(--exit)" />Nikaas</a>
        <nav aria-label="Pages">
          {Object.entries(PAGES).map(([k, p]) => (
            <a key={k} href={`#/${k}`} aria-current={k === route ? 'page' : undefined}>{p.label}</a>
          ))}
        </nav>
      </header>
      <main>{page.render()}</main>
      <footer className="footer">
        <p>Nikaas, built at AfterHours 1.0 (DBIT) by TheGoodEngineers, team AH50: Ayush V U, Bhumika G, Abhijeet, Chirag R H.</p>
        <p>Floor-plan photo: Biswarup Ganguly, CC BY 3.0, Wikimedia Commons. Fonts: Big Shoulders Display and Atkinson Hyperlegible (SIL OFL). 3D: three.js (MIT).</p>
      </footer>
    </>
  )
}
