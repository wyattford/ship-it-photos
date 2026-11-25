import { useCallback, useEffect, useState } from 'react'
import { api, type Post } from '../api'
import PostCard from './PostCard'

// Loads posts page by page ("Load more") for the feed, search and profile pages.
export default function PostGrid({ q, user, emptyText }: { q?: string; user?: string; emptyText: string }) {
  const [posts, setPosts] = useState<Post[]>([])
  const [next, setNext] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(
    async (before: number | null) => {
      setLoading(true)
      setError('')
      try {
        const page = await api.posts({ q, user, before })
        setPosts((prev) => (before ? [...prev, ...page.posts] : page.posts))
        setNext(page.next_before)
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(false)
      }
    },
    [q, user],
  )

  useEffect(() => {
    load(null)
  }, [load])

  const update = (p: Post) => setPosts((list) => list.map((x) => (x.id === p.id ? p : x)))

  if (error) return <p className="error">{error}</p>
  if (!loading && posts.length === 0) return <p className="empty">{emptyText}</p>

  return (
    <>
      <div className="grid">
        {posts.map((p) => <PostCard key={p.id} post={p} onChange={update} />)}
      </div>
      <div className="center">
        {loading && <p className="muted">Loading…</p>}
        {!loading && next && <button className="btn" onClick={() => load(next)}>Load more</button>}
      </div>
    </>
  )
}
