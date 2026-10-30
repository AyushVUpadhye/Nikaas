// Running figure toward a doorway: our own drawing of the exit-sign idea (ISO 7010 style, not a copy)
export default function ExitIcon({ color = '#ffffff' }: { color?: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" fill={color}>
      <rect x="44" y="6" width="16" height="52" rx="1.5" fill="none" stroke={color} strokeWidth="4" />
      <circle cx="26" cy="11" r="6" />
      <path d="M22 20 L33 21 L39 30 L46 33 L44 38 L35 34 L31 29 L28 38 L36 45 L34 58 L28 57 L29 47 L21 41 L17 51 L8 53 L7 47 L14 45 L18 33 L13 35 L10 42 L5 40 L10 29 Z" />
    </svg>
  )
}
