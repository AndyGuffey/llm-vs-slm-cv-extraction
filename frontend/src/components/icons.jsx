const base = {
  width: 16,
  height: 16,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export function DownloadIcon() {
  return (
    <svg {...base}>
      <path d="M12 3v12" />
      <path d="m7 10 5 5 5-5" />
      <path d="M5 21h14" />
    </svg>
  )
}

export function TrashIcon() {
  return (
    <svg {...base}>
      <path d="M4 7h16" />
      <path d="M6 7v13a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V7" />
      <path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3" />
    </svg>
  )
}

export function PencilIcon() {
  return (
    <svg {...base}>
      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
    </svg>
  )
}

export function PlusIcon() {
  return (
    <svg {...base}>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </svg>
  )
}

export function SearchIcon() {
  return (
    <svg {...base}>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  )
}

export function GridIcon() {
  return (
    <svg {...base}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  )
}

export function BellIcon() {
  return (
    <svg {...base}>
      <path d="M6 8a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6" />
      <path d="M10 21a2 2 0 0 0 4 0" />
    </svg>
  )
}

export function BookmarkIcon() {
  return (
    <svg {...base}>
      <path d="M6 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17l-6-4-6 4Z" />
    </svg>
  )
}

export function HeartIcon() {
  return (
    <svg {...base}>
      <path d="M19.5 12.6 12 20l-7.5-7.4a4.7 4.7 0 0 1 0-6.7 4.8 4.8 0 0 1 6.8 0L12 6.6l.7-.7a4.8 4.8 0 0 1 6.8 0 4.7 4.7 0 0 1 0 6.7Z" />
    </svg>
  )
}

export function UserCircleIcon() {
  return (
    <svg {...base}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c1.8-3.6 5-5 8-5s6.2 1.4 8 5" />
    </svg>
  )
}
