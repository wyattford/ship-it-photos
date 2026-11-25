import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { api, type Profile } from '../api'
import PostGrid from '../components/PostGrid'

export default function ProfilePage() {
  const { username = '' } = useParams()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setProfile(null)
    setError('')
    api.user(username).then(setProfile).catch((e) => setError(e.message))
  }, [username])

  if (error) return <p className="error">{error}</p>
  if (!profile) return <p className="muted">Loading…</p>

  return (
    <>
      <section className="profile">
        <div className="avatar avatar-lg" aria-hidden>{profile.display_name.charAt(0).toUpperCase()}</div>
        <div>
          <h1>{profile.display_name}</h1>
          <p className="muted">@{profile.username} · joined {new Date(profile.joined_at).toLocaleDateString()}</p>
          {profile.bio && <p>{profile.bio}</p>}
          <p className="stats">
            <strong>{profile.post_count}</strong> posts · <strong>{profile.likes_received}</strong> likes received
          </p>
        </div>
      </section>
      <PostGrid key={username} user={username} emptyText="No posts yet." />
    </>
  )
}
