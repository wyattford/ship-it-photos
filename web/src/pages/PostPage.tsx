import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, type Comment, type Post, type PostDetail } from '../api'
import { useAuth } from '../auth'
import Comments from '../components/Comments'
import { Byline, Carousel, LikeButton } from '../components/PostCard'

export default function PostPage() {
  const { id } = useParams()
  const postId = Number(id)
  const { user } = useAuth()
  const navigate = useNavigate()
  const [post, setPost] = useState<PostDetail | null>(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [caption, setCaption] = useState('')

  useEffect(() => {
    api.post(postId).then(setPost).catch((e) => setError(e.message))
  }, [postId])

  if (error) return <p className="error">{error}</p>
  if (!post) return <p className="muted">Loading…</p>

  const mine = user?.id === post.author.id
  const setComments = (fn: (c: Comment[]) => Comment[]) =>
    setPost((p) => {
      if (!p) return p
      const comments = fn(p.comments)
      return { ...p, comments, comment_count: comments.filter((c) => !c.deleted).length }
    })

  async function saveCaption() {
    const updated = await api.editPost(postId, caption)
    setPost((p) => (p ? { ...p, ...updated } : p))
    setEditing(false)
  }

  async function remove() {
    if (!confirm('Delete this post and all its photos and comments? This cannot be undone.')) return
    await api.deletePost(postId)
    navigate(`/u/${post!.author.username}`)
  }

  return (
    <div className="post-page">
      <div className="post-media"><Carousel photos={post.photos} full /></div>
      <div className="post-side">
        <Byline post={post} />
        {editing ? (
          <div className="comment-form">
            <textarea value={caption} onChange={(e) => setCaption(e.target.value)} rows={4} maxLength={2000} autoFocus />
            <div className="row">
              <button className="btn btn-primary btn-sm" onClick={saveCaption}>Save</button>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>Cancel</button>
            </div>
          </div>
        ) : (
          post.caption && <p className="caption">{post.caption}</p>
        )}
        <div className="actions">
          <LikeButton post={post} onChange={(p: Post) => setPost((d) => (d ? { ...d, ...p } : d))} />
          {mine && !editing && (
            <>
              <button className="link-btn" onClick={() => { setCaption(post.caption); setEditing(true) }}>Edit caption</button>
              <button className="link-btn danger" onClick={remove}>Delete post</button>
            </>
          )}
        </div>
        <Comments postId={post.id} comments={post.comments} setComments={setComments} />
      </div>
    </div>
  )
}
