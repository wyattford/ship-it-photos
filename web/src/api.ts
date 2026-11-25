// Typed wrappers around this app's own /api routes. The page never talks to the database.

export interface User {
  id: number
  username: string
  display_name: string
}

export interface Photo {
  id: number
  url: string
  thumb_url: string
  width: number
  height: number
}

export interface Post {
  id: number
  caption: string
  created_at: string
  updated_at: string | null
  author: User
  like_count: number
  comment_count: number
  liked_by_me: boolean
  photos: Photo[]
}

export interface Comment {
  id: number
  parent_id: number | null
  body: string | null
  deleted: boolean
  created_at: string
  updated_at: string | null
  author: User | null
}

export interface PostDetail extends Post {
  comments: Comment[]
}

export interface Profile extends User {
  bio: string | null
  joined_at: string
  post_count: number
  likes_received: number
}

export interface Page {
  posts: Post[]
  next_before: number | null
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method, credentials: 'same-origin' }
  if (body instanceof FormData) {
    init.body = body
  } else if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers = { 'Content-Type': 'application/json' }
  }
  const res = await fetch(url, init)
  const data = res.headers.get('content-type')?.includes('json') ? await res.json() : null
  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    if (typeof data?.detail === 'string') msg = data.detail
    else if (Array.isArray(data?.detail) && data.detail[0]?.msg) msg = data.detail[0].msg
    throw new ApiError(res.status, msg)
  }
  return data as T
}

export const api = {
  me: () => request<User | null>('GET', '/api/auth/me'),
  signup: (username: string, display_name: string, password: string) =>
    request<User>('POST', '/api/auth/signup', { username, display_name, password }),
  login: (username: string, password: string) => request<User>('POST', '/api/auth/login', { username, password }),
  logout: () => request<{ ok: boolean }>('POST', '/api/auth/logout'),

  posts: (opts: { q?: string; user?: string; before?: number | null }) => {
    const p = new URLSearchParams()
    if (opts.q) p.set('q', opts.q)
    if (opts.user) p.set('user', opts.user)
    if (opts.before) p.set('before', String(opts.before))
    return request<Page>('GET', `/api/posts?${p}`)
  },
  post: (id: number) => request<PostDetail>('GET', `/api/posts/${id}`),
  createPost: (form: FormData) => request<Post>('POST', '/api/posts', form),
  editPost: (id: number, caption: string) => request<Post>('PATCH', `/api/posts/${id}`, { caption }),
  deletePost: (id: number) => request<{ ok: boolean }>('DELETE', `/api/posts/${id}`),

  like: (id: number) => request<{ liked_by_me: boolean; like_count: number }>('PUT', `/api/posts/${id}/like`),
  unlike: (id: number) => request<{ liked_by_me: boolean; like_count: number }>('DELETE', `/api/posts/${id}/like`),

  addComment: (postId: number, body: string, parent_id: number | null) =>
    request<Comment>('POST', `/api/posts/${postId}/comments`, { body, parent_id }),
  editComment: (id: number, body: string) =>
    request<{ id: number; body: string; updated_at: string }>('PATCH', `/api/comments/${id}`, { body }),
  deleteComment: (id: number) => request<{ ok: boolean; soft: boolean }>('DELETE', `/api/comments/${id}`),

  user: (username: string) => request<Profile>('GET', `/api/users/${encodeURIComponent(username)}`),
}

export function timeAgo(iso: string): string {
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (s < 60) return 'just now'
  const units: [number, string][] = [
    [60, 'minute'],
    [3600, 'hour'],
    [86400, 'day'],
    [604800, 'week'],
    [2629800, 'month'],
    [31557600, 'year'],
  ]
  let label = ''
  for (const [size, name] of units) {
    if (s >= size) {
      const n = Math.floor(s / size)
      label = `${n} ${name}${n === 1 ? '' : 's'} ago`
    }
  }
  return label
}
