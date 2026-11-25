import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { api, timeAgo, type Comment } from '../api'
import { useAuth } from '../auth'

const MAX_DEPTH = 4 // deeper replies are shown flat at this indent

function CommentForm({
  initial = '',
  placeholder,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial?: string
  placeholder: string
  submitLabel: string
  onSubmit: (text: string) => Promise<void>
  onCancel?: () => void
}) {
  const [text, setText] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError('')
    try {
      await onSubmit(text)
      setText('')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="comment-form" onSubmit={submit}>
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder}
        maxLength={2000} rows={2} autoFocus={!!onCancel} />
      {error && <p className="error small">{error}</p>}
      <div className="row">
        <button className="btn btn-primary btn-sm" disabled={busy || !text.trim()}>{submitLabel}</button>
        {onCancel && <button type="button" className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  )
}

function CommentNode({
  comment,
  childrenOf,
  depth,
  postId,
  onAdd,
  onUpdate,
  onRemove,
}: {
  comment: Comment
  childrenOf: Map<number | null, Comment[]>
  depth: number
  postId: number
  onAdd: (c: Comment) => void
  onUpdate: (c: Comment) => void
  onRemove: (id: number) => void
}) {
  const { user } = useAuth()
  const [replying, setReplying] = useState(false)
  const [editing, setEditing] = useState(false)
  const kids = childrenOf.get(comment.id) ?? []
  const mine = !!user && comment.author?.id === user.id

  async function remove() {
    if (!confirm('Delete this comment?')) return
    const r = await api.deleteComment(comment.id)
    if (r.soft) onUpdate({ ...comment, deleted: true, body: null, author: null })
    else onRemove(comment.id)
  }

  return (
    <li className="comment">
      <div className="comment-head">
        {comment.author ? (
          <Link to={`/u/${comment.author.username}`} className="author">{comment.author.display_name}</Link>
        ) : (
          <span className="muted">[deleted]</span>
        )}
        <span className="muted small">
          {timeAgo(comment.created_at)}{comment.updated_at && !comment.deleted ? ' · edited' : ''}
        </span>
      </div>

      {editing ? (
        <CommentForm
          initial={comment.body ?? ''}
          placeholder="Edit your comment"
          submitLabel="Save"
          onCancel={() => setEditing(false)}
          onSubmit={async (text) => {
            const r = await api.editComment(comment.id, text)
            onUpdate({ ...comment, body: r.body, updated_at: r.updated_at })
            setEditing(false)
          }}
        />
      ) : (
        <p className={`comment-body ${comment.deleted ? 'muted' : ''}`}>
          {comment.deleted ? 'This comment was deleted.' : comment.body}
        </p>
      )}

      {!comment.deleted && !editing && (
        <div className="comment-actions">
          {user && <button className="link-btn" onClick={() => setReplying((r) => !r)}>Reply</button>}
          {mine && <button className="link-btn" onClick={() => setEditing(true)}>Edit</button>}
          {mine && <button className="link-btn danger" onClick={remove}>Delete</button>}
        </div>
      )}

      {replying && (
        <CommentForm
          placeholder={`Reply to ${comment.author?.display_name ?? 'comment'}`}
          submitLabel="Reply"
          onCancel={() => setReplying(false)}
          onSubmit={async (text) => {
            onAdd(await api.addComment(postId, text, comment.id))
            setReplying(false)
          }}
        />
      )}

      {kids.length > 0 && (
        <ul className={depth < MAX_DEPTH ? 'replies' : 'replies flat'}>
          {kids.map((k) => (
            <CommentNode key={k.id} comment={k} childrenOf={childrenOf} depth={depth + 1} postId={postId}
              onAdd={onAdd} onUpdate={onUpdate} onRemove={onRemove} />
          ))}
        </ul>
      )}
    </li>
  )
}

export default function Comments({
  postId,
  comments,
  setComments,
}: {
  postId: number
  comments: Comment[]
  setComments: (fn: (c: Comment[]) => Comment[]) => void
}) {
  const { user } = useAuth()
  const childrenOf = useMemo(() => {
    const m = new Map<number | null, Comment[]>()
    for (const c of comments) {
      const list = m.get(c.parent_id) ?? []
      list.push(c)
      m.set(c.parent_id, list)
    }
    return m
  }, [comments])

  const onAdd = (c: Comment) => setComments((list) => [...list, c])
  const onUpdate = (c: Comment) => setComments((list) => list.map((x) => (x.id === c.id ? c : x)))
  const onRemove = (id: number) => setComments((list) => list.filter((x) => x.id !== id))
  const visible = comments.filter((c) => !c.deleted).length

  return (
    <section className="comments">
      <h2>{visible} comment{visible === 1 ? '' : 's'}</h2>
      {user ? (
        <CommentForm placeholder="Add a comment…" submitLabel="Comment"
          onSubmit={async (text) => onAdd(await api.addComment(postId, text, null))} />
      ) : (
        <p className="muted"><Link to="/login">Log in</Link> to comment.</p>
      )}
      <ul className="thread">
        {(childrenOf.get(null) ?? []).map((c) => (
          <CommentNode key={c.id} comment={c} childrenOf={childrenOf} depth={0} postId={postId}
            onAdd={onAdd} onUpdate={onUpdate} onRemove={onRemove} />
        ))}
      </ul>
    </section>
  )
}
