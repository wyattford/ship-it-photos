import { Link, Route, Routes, useNavigate } from 'react-router'
import { api } from './api'
import { useAuth } from './auth'
import AuthPage from './pages/AuthPage'
import FeedPage from './pages/FeedPage'
import NewPostPage from './pages/NewPostPage'
import PostPage from './pages/PostPage'
import ProfilePage from './pages/ProfilePage'

function Header() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  async function logout() {
    await api.logout()
    setUser(null)
    navigate('/')
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Link to="/" className="brand">
          <span className="brand-mark" aria-hidden>◐</span> Ship It Photos
        </Link>
        <nav className="nav">
          {user ? (
            <>
              <Link to="/new" className="btn btn-primary">+ New post</Link>
              <Link to={`/u/${user.username}`} className="nav-user">@{user.username}</Link>
              <button className="btn btn-ghost" onClick={logout}>Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost">Log in</Link>
              <Link to="/signup" className="btn btn-primary">Sign up</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<FeedPage />} />
          <Route path="/p/:id" element={<PostPage />} />
          <Route path="/u/:username" element={<ProfilePage />} />
          <Route path="/new" element={<NewPostPage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/signup" element={<AuthPage mode="signup" />} />
          <Route path="*" element={<p className="empty">Page not found.</p>} />
        </Routes>
      </main>
    </>
  )
}
