import { useState } from 'react'
import { PencilIcon, PlusIcon, TrashIcon } from './icons'

const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

function parseYearMonth(value) {
  const match = /^(\d{4})-(\d{2})$/.exec(String(value || '').trim())
  if (!match) return null
  return { year: Number(match[1]), month: Number(match[2]) }
}

function formatYearMonth({ year, month }) {
  return `${MONTHS[month - 1]} ${year}`
}

function formatDuration(start, end) {
  const months = (end.year - start.year) * 12 + (end.month - start.month)
  if (months < 0) return null
  const years = Math.floor(months / 12)
  const remainder = months % 12
  const parts = []
  if (years > 0) parts.push(`${years} year${years === 1 ? '' : 's'}`)
  if (remainder > 0 || years === 0) parts.push(`${remainder} month${remainder === 1 ? '' : 's'}`)
  return parts.join(', ')
}

function formatDateRange(start, end) {
  const startYm = parseYearMonth(start)
  const isPresent = String(end || '').trim().toLowerCase() === 'present'
  const endYm = isPresent
    ? { year: new Date().getFullYear(), month: new Date().getMonth() + 1 }
    : parseYearMonth(end)

  const startLabel = startYm ? formatYearMonth(startYm) : start || '?'
  const endLabel = isPresent ? 'Present' : endYm ? formatYearMonth(endYm) : end || '?'

  const duration = startYm && endYm ? formatDuration(startYm, endYm) : null
  return duration ? `${startLabel} - ${endLabel} (${duration})` : `${startLabel} - ${endLabel}`
}

function confidenceLabel(confidence) {
  if (confidence >= 0.8) return 'high'
  if (confidence >= 0.5) return 'medium'
  return 'low'
}

function ExperienceItem({ role, onEdit, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const companyLine = role.location ? `${role.company} in ${role.location}` : role.company

  return (
    <div className="experience-item">
      <div className="experience-item-header">
        <span className="experience-title">
          {role.confidence !== undefined && (
            <span
              className={`confidence-dot confidence-dot--${confidenceLabel(role.confidence)}`}
              title={`Confidence: ${Math.round(role.confidence * 100)}%`}
            />
          )}
          {role.title || '(untitled role)'}
        </span>
        <div className="experience-item-actions">
          <button type="button" className="link-action" onClick={onEdit}>
            <PencilIcon /> Edit
          </button>
          <button type="button" className="link-action" onClick={onDelete}>
            <TrashIcon />
          </button>
        </div>
      </div>

      {companyLine && <div className="experience-company">{companyLine}</div>}

      {role.description && (
        <>
          <p className={`experience-description ${expanded ? '' : 'experience-description--clamped'}`}>
            {role.description}
          </p>
          <button type="button" className="show-more" onClick={() => setExpanded((e) => !e)}>
            {expanded ? 'Show less' : 'Show full description'} <PlusIcon />
          </button>
        </>
      )}

      <div className="experience-dates">{formatDateRange(role.start, role.end)}</div>
    </div>
  )
}

function ExperienceForm({ role, onSave, onCancel }) {
  const [fields, setFields] = useState({
    title: role.title || '',
    company: role.company || '',
    location: role.location || '',
    start: role.start || '',
    end: role.end || '',
    description: role.description || '',
  })
  const isPresent = fields.end.trim().toLowerCase() === 'present'

  function update(key, value) {
    setFields((f) => ({ ...f, [key]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    onSave(fields)
  }

  return (
    <form className="experience-item experience-form" onSubmit={handleSubmit}>
      <label>
        Title
        <input value={fields.title} onChange={(e) => update('title', e.target.value)} required />
      </label>
      <label>
        Company
        <input value={fields.company} onChange={(e) => update('company', e.target.value)} required />
      </label>
      <label>
        Location
        <input value={fields.location} onChange={(e) => update('location', e.target.value)} />
      </label>
      <div className="form-row">
        <label>
          Start (YYYY-MM)
          <input
            value={fields.start}
            onChange={(e) => update('start', e.target.value)}
            placeholder="2022-11"
            required
          />
        </label>
        <label>
          End (YYYY-MM)
          <input
            value={isPresent ? '' : fields.end}
            onChange={(e) => update('end', e.target.value)}
            placeholder="2024-03"
            disabled={isPresent}
          />
        </label>
      </div>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={isPresent}
          onChange={(e) => update('end', e.target.checked ? 'Present' : '')}
        />
        Currently working here
      </label>
      <label>
        Description
        <textarea
          value={fields.description}
          onChange={(e) => update('description', e.target.value)}
          rows={4}
        />
      </label>
      <div className="form-actions">
        <button type="button" className="button-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="button-primary">
          Save
        </button>
      </div>
    </form>
  )
}

function ExperienceSection({ experience, onAdd, onSave, onDelete }) {
  const [editingId, setEditingId] = useState(null)
  const [newIds, setNewIds] = useState(() => new Set())

  function handleAddClick() {
    const id = crypto.randomUUID()
    onAdd({ id, title: '', company: '', location: '', start: '', end: '', description: '' })
    setNewIds((prev) => new Set(prev).add(id))
    setEditingId(id)
  }

  function handleCancel(id) {
    if (newIds.has(id)) {
      onDelete(id)
      setNewIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
    setEditingId(null)
  }

  function handleSave(id, fields) {
    onSave(id, fields)
    setNewIds((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    setEditingId(null)
  }

  return (
    <section className="card">
      <h2>Experience</h2>

      {experience.length === 0 && (
        <p className="card-hint">No experience yet — upload a CV above or add it manually.</p>
      )}

      <div className="experience-list">
        {experience.map((role) =>
          editingId === role.id ? (
            <ExperienceForm
              key={role.id}
              role={role}
              onSave={(fields) => handleSave(role.id, fields)}
              onCancel={() => handleCancel(role.id)}
            />
          ) : (
            <ExperienceItem
              key={role.id}
              role={role}
              onEdit={() => setEditingId(role.id)}
              onDelete={() => onDelete(role.id)}
            />
          ),
        )}
      </div>

      <button type="button" className="button-secondary add-experience" onClick={handleAddClick}>
        <PlusIcon /> Add experience
      </button>
    </section>
  )
}

export default ExperienceSection
