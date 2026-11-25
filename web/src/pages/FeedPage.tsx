import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import PostGrid from '../components/PostGrid'

export default function FeedPage() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const [text, setText] = useState(q)

  useEffect(() => setText(q), [q])

  // Search as you type (debounced), kept in the URL so results are shareable.
  useEffect(() => {
    const t = setTimeout(() => {
      if (text.trim() !== q) setParams(text.trim() ? { q: text.trim() } : {}, { replace: true })
    }, 300)
    return () => clearTimeout(t)
  }, [text, q, setParams])

  return (
    <div className="feed">
      <div className="search">
        <input
          type="search"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Search captions or photographers…"
          aria-label="Search posts"
          maxLength={100}
        />
      </div>
      {q && <p className="muted">Results for “{q}”</p>}
      <PostGrid key={q} q={q} layout="rows" emptyText={q ? 'No posts match that search.' : 'No posts yet. Be the first!'} />
    </div>
  )
}
