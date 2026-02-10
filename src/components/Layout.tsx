import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { state, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 rounded-lg font-medium transition-colors ${isActive ? 'bg-primary-200 text-primary-900' : 'text-primary-700 hover:bg-primary-100'}`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-primary-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-primary-900">Client Update Agent</h1>
          <nav className="flex items-center gap-2">
            <NavLink to="/dashboard" className={navClass} end>Dashboard</NavLink>
            <NavLink to="/clients" className={navClass}>Clients</NavLink>
            <NavLink to="/pending-updates" className={navClass}>Pending Updates</NavLink>
            <span className="text-primary-600 text-sm ml-2">{state.user?.email}</span>
            <button
              type="button"
              onClick={handleLogout}
              className="ml-2 px-3 py-1.5 text-sm rounded-lg border border-primary-300 text-primary-700 hover:bg-primary-100"
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
