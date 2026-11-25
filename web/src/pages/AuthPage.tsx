import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api'
import { useAuth } from '../auth'

export default function AuthPage({ mode }: { mode: 'login' | 'signup' }) {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const signup = mode === 'signup'

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const u = signup ? await api.signup(username, displayName, password) : await api.login(username, password)
      setUser(u)
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="panel auth" onSubmit={submit}>
      <h1>{signup ? 'Create your account' : 'Welcome back'}</h1>
      <label className="field">
        Username
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username"
          required minLength={3} maxLength={30} pattern="[A-Za-z0-9._]+" autoFocus />
      </label>
      {signup && (
        <label className="field">
          Display name
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoComplete="name"
            required maxLength={60} />
        </label>
      )}
      <label className="field">
        Password
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
          autoComplete={signup ? 'new-password' : 'current-password'} required minLength={signup ? 8 : 1} />
      </label>
      {error && <p className="error">{error}</p>}
      <button className="btn btn-primary" disabled={busy}>{signup ? 'Sign up' : 'Log in'}</button>
      <p className="muted small">
        {signup ? <>Already have an account? <Link to="/login">Log in</Link></> : <>New here? <Link to="/signup">Sign up</Link></>}
      </p>
    </form>
  )
}
