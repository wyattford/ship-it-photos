import { useEffect, useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { api } from '../api'
import { useAuth } from '../auth'

const MAX_PHOTOS = 10
const MAX_BYTES = 10 * 1024 * 1024
const TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

export default function NewPostPage() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [caption, setCaption] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f))
    setPreviews(urls)
    return () => urls.forEach(URL.revokeObjectURL)
  }, [files])

  if (loading) return null
  if (!user) return <Navigate to="/login" replace />

  function addFiles(list: FileList | null) {
    if (!list) return
    setError('')
    const picked = [...list]
    const bad = picked.find((f) => !TYPES.includes(f.type) || f.size > MAX_BYTES)
    if (bad) return setError(`${bad.name}: must be JPEG, PNG, WebP or GIF and at most 10 MB.`)
    const next = [...files, ...picked]
    if (next.length > MAX_PHOTOS) return setError(`You can attach up to ${MAX_PHOTOS} photos.`)
    setFiles(next)
  }

  function move(i: number, d: number) {
    const next = [...files]
    ;[next[i], next[i + d]] = [next[i + d], next[i]]
    setFiles(next)
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (files.length === 0) return setError('Add at least one photo.')
    const form = new FormData()
    files.forEach((f) => form.append('photos', f))
    form.append('caption', caption)
    setBusy(true)
    setError('')
    try {
      const post = await api.createPost(form)
      navigate(`/p/${post.id}`)
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <form className="panel new-post" onSubmit={submit}>
      <h1>New post</h1>
      <label className="dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files) }}>
        <input type="file" accept={TYPES.join(',')} multiple hidden
          onChange={(e) => { addFiles(e.target.files); e.target.value = '' }} />
        <strong>Click or drop photos here</strong>
        <span className="muted small">Up to {MAX_PHOTOS} · JPEG, PNG, WebP, GIF · 10 MB each</span>
      </label>

      {previews.length > 0 && (
        <ol className="previews">
          {previews.map((src, i) => (
            <li key={src}>
              <img src={src} alt={`Photo ${i + 1}`} />
              <div className="preview-tools">
                <button type="button" disabled={i === 0} onClick={() => move(i, -1)} aria-label="Move earlier">←</button>
                <button type="button" onClick={() => setFiles(files.filter((_, k) => k !== i))} aria-label="Remove">✕</button>
                <button type="button" disabled={i === files.length - 1} onClick={() => move(i, 1)} aria-label="Move later">→</button>
              </div>
            </li>
          ))}
        </ol>
      )}

      <label className="field">
        Caption
        <textarea value={caption} onChange={(e) => setCaption(e.target.value)} rows={3} maxLength={2000}
          placeholder="Tell people about these photos…" />
      </label>
      {error && <p className="error">{error}</p>}
      <button className="btn btn-primary" disabled={busy || files.length === 0}>
        {busy ? 'Uploading…' : `Post ${files.length || ''} photo${files.length === 1 ? '' : 's'}`}
      </button>
    </form>
  )
}
