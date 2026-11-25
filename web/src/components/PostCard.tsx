import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { api, timeAgo, type Photo, type Post } from '../api'
import { useAuth } from '../auth'

export function Carousel({ photos, full = false }: { photos: Photo[]; full?: boolean }) {
  const [i, setI] = useState(0)
  const photo = photos[i]
  if (!photo) return null
  return (
    <div className={`carousel ${full ? 'carousel-full' : ''}`}>
      <img
        src={full ? photo.url : photo.thumb_url}
        alt=""
        width={photo.width}
        height={photo.height}
        loading="lazy"
      />
      {photos.length > 1 && (
        <>
          <button
            className="carousel-btn prev"
            aria-label="Previous photo"
            disabled={i === 0}
            onClick={(e) => { e.preventDefault(); setI(i - 1) }}
          >‹</button>
          <button
            className="carousel-btn next"
            aria-label="Next photo"
            disabled={i === photos.length - 1}
            onClick={(e) => { e.preventDefault(); setI(i + 1) }}
          >›</button>
          <div className="dots">
            {photos.map((p, k) => <span key={p.id} className={k === i ? 'dot on' : 'dot'} />)}
          </div>
          <span className="count-badge">{i + 1}/{photos.length}</span>
        </>
      )}
    </div>
  )
}

export function LikeButton({ post, onChange }: { post: Post; onChange: (p: Post) => void }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  async function toggle() {
    if (!user) return navigate('/login')
    setBusy(true)
    try {
      const r = post.liked_by_me ? await api.unlike(post.id) : await api.like(post.id)
      onChange({ ...post, ...r })
    } finally {
      setBusy(false)
    }
  }

  return (
    <button className={`like ${post.liked_by_me ? 'liked' : ''}`} onClick={toggle} disabled={busy}
      aria-pressed={post.liked_by_me} aria-label={post.liked_by_me ? 'Unlike' : 'Like'}>
      <span aria-hidden>{post.liked_by_me ? '♥' : '♡'}</span> {post.like_count}
    </button>
  )
}

export function Byline({ post }: { post: Post }) {
  return (
    <div className="byline">
      <Link to={`/u/${post.author.username}`} className="avatar" aria-hidden>
        {post.author.display_name.charAt(0).toUpperCase()}
      </Link>
      <div>
        <Link to={`/u/${post.author.username}`} className="author">{post.author.display_name}</Link>
        <div className="muted small">
          @{post.author.username} · {timeAgo(post.created_at)}{post.updated_at ? ' · edited' : ''}
        </div>
      </div>
    </div>
  )
}

export default function PostCard({ post, onChange }: { post: Post; onChange: (p: Post) => void }) {
  return (
    <article className="card">
      <Byline post={post} />
      <Link to={`/p/${post.id}`}><Carousel photos={post.photos} /></Link>
      <div className="card-body">
        {post.caption && <p className="caption clamp">{post.caption}</p>}
        <div className="actions">
          <LikeButton post={post} onChange={onChange} />
          <Link to={`/p/${post.id}`} className="comments-link">💬 {post.comment_count}</Link>
        </div>
      </div>
    </article>
  )
}
