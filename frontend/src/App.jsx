import { useState } from 'react'
import './App.css'
import CvCard from './components/CvCard'
import ExperienceSection from './components/ExperienceSection'

const API_URL = 'http://localhost:8000'

function App() {
  const [cv, setCv] = useState(null)
  const [experience, setExperience] = useState([])
  const [status, setStatus] = useState('idle') // idle | loading | error
  const [error, setError] = useState(null)

  async function handleUpload(file) {
    setStatus('loading')
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/extract`, { method: 'POST', body: formData })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)

      const data = await res.json()
      setCv({ file, name: file.name })
      setExperience(
        (data.experience || []).map((role) => ({ id: crypto.randomUUID(), location: '', ...role })),
      )
      setStatus('idle')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  function handleCvDelete() {
    setCv(null)
    setStatus('idle')
    setError(null)
  }

  function handleExperienceAdd(role) {
    setExperience((exp) => [...exp, role])
  }

  function handleExperienceSave(id, fields) {
    setExperience((exp) => exp.map((role) => (role.id === id ? { ...role, ...fields } : role)))
  }

  function handleExperienceDelete(id) {
    setExperience((exp) => exp.filter((role) => role.id !== id))
  }

  return (
    <main className="app">
      <h1>My Profile</h1>

      <CvCard cv={cv} status={status} error={error} onUpload={handleUpload} onDelete={handleCvDelete} />

      <ExperienceSection
        experience={experience}
        onAdd={handleExperienceAdd}
        onSave={handleExperienceSave}
        onDelete={handleExperienceDelete}
      />
    </main>
  )
}

export default App
