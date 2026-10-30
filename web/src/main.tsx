import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './theme.css'
import App from './App.tsx'
import Landing from './Landing.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Landing />
    <div id="try"><App /></div>
  </StrictMode>,
)
