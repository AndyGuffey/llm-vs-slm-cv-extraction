import { DownloadIcon, TrashIcon } from './icons'

function CvCard({ cv, status, error, onUpload, onDelete }) {
  const loading = status === 'loading'

  function handleFileChange(event) {
    const file = event.target.files[0]
    event.target.value = ''
    if (file) onUpload(file)
  }

  function handleDownload() {
    const url = URL.createObjectURL(cv.file)
    const link = document.createElement('a')
    link.href = url
    link.download = cv.name
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="card">
      <h2>CV</h2>
      <p className="card-hint">
        This CV will be available to add to your applications when you apply for a job.
        Employers can also download this CV when viewing your profile.
      </p>

      {status === 'error' && <p className="error">Couldn't extract that CV: {error}</p>}

      {cv ? (
        <div className="cv-row">
          <span className="cv-filename">{cv.name}</span>
          <div className="cv-actions">
            <button type="button" className="link-action" onClick={handleDownload}>
              <DownloadIcon /> Download
            </button>
            <button type="button" className="link-action" onClick={onDelete}>
              <TrashIcon /> Delete
            </button>
          </div>
        </div>
      ) : (
        <label className="upload-button">
          {loading ? 'Extracting…' : 'Upload CV'}
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            disabled={loading}
            hidden
          />
        </label>
      )}
    </section>
  )
}

export default CvCard
