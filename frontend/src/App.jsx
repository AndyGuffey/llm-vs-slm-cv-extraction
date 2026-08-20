import { useState } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

function confidenceLabel(confidence) {
  if (confidence >= 0.8) return 'high'
  if (confidence >= 0.5) return 'medium'
  return 'low'
}

function ExperienceRole({ role }) {
  return (
    <div className={`role role--${confidenceLabel(role.confidence)}`}>
      <div className="role-header">
        <span className="role-title">{role.title || '(missing title)'}</span>
        <span className="confidence-badge">{Math.round(role.confidence * 100)}%</span>
      </div>
      <div className="role-company">{role.company}</div>
      <div className="role-dates">{role.start} — {role.end}</div>
      <p className="role-description">{role.description}</p>
    </div>
  )
}

function App() {
  const [file, setFile] = useState(null)
  const [experience, setExperience] = useState(null)
  const [latency, setLatency] = useState(null)
  const [status, setStatus] = useState('idle') // idle | loading | error
  const [error, setError] = useState(null)

  async function handleUpload(event) {
    event.preventDefault()
    if (!file) return

    setStatus('loading')
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/extract`, { method: 'POST', body: formData })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)

      const data = await res.json()
      setExperience(data.experience)
      setLatency(data.latency)
      setStatus('idle')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <main className="app">
      <h1>CV Experience Extractor</h1>
      <p className="subtitle">Upload a CV (PDF or DOCX) to auto-fill the experience section.</p>

      <form onSubmit={handleUpload} className="upload-form">
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button type="submit" disabled={!file || status === 'loading'}>
          {status === 'loading' ? 'Extracting…' : 'Extract'}
        </button>
      </form>

      {status === 'error' && <p className="error">Error: {error}</p>}

      {latency !== null && (
        <p className="latency">Extraction took {latency}s</p>
      )}

      {experience && (
        <section className="experience-list">
          {experience.length === 0 ? (
            <p>No roles extracted.</p>
          ) : (
            experience.map((role, i) => <ExperienceRole role={role} key={i} />)
          )}
        </section>
      )}
    </main>
  )
}

export default App
