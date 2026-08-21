import { useState } from 'react'
import './App.css'
import NavBar from './components/NavBar'
import CvCard from './components/CvCard'
import ExperienceSection from './components/ExperienceSection'

const API_URL = 'http://localhost:8000'

function App() {
  const [cv, setCv] = useState(null)
  const [experience, setExperience] = useState([])
  const [status, setStatus] = useState('idle') // idle | loading | error
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null) // { type: 'warning' | 'info', message }

  async function handleUpload(file) {
    setStatus('loading')
    setError(null)
    setNotice(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/extract`, { method: 'POST', body: formData })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)

      const data = await res.json()
      const extracted = data.experience || []
      setCv({ file, name: file.name })
      setExperience(extracted.map((role) => ({ id: crypto.randomUUID(), location: '', ...role })))
      setStatus('idle')

      if (extracted.length === 0) {
        setNotice({
          type: 'warning',
          message: "We couldn't extract experience from this CV automatically — you can add it manually below.",
        })
      } else if (data.escalated) {
        setNotice({ type: 'info', message: 'Used enhanced extraction for this CV.' })
      }
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  function handleCvDelete() {
    setCv(null)
    setStatus('idle')
    setError(null)
    setNotice(null)
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
    <>
      <NavBar />
      <main className="app">
        <h1>My Profile</h1>

        <CvCard
          cv={cv}
          status={status}
          error={error}
          notice={notice}
          onUpload={handleUpload}
          onDelete={handleCvDelete}
        />

        <ExperienceSection
          experience={experience}
          onAdd={handleExperienceAdd}
          onSave={handleExperienceSave}
          onDelete={handleExperienceDelete}
        />
      </main>
    </>
  )
}

export default App
