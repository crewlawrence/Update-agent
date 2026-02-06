import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-primary-100">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg border border-primary-200 p-8">
        <h1 className="text-2xl font-semibold text-primary-900 mb-2">Sign in</h1>
        <p className="text-primary-600 mb-6">Client Update Agent</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-primary-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-primary-300 focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              required
              autoComplete="email"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-primary-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-primary-300 focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              required
              autoComplete="current-password"
            />
          </div>
          <button
            type="submit"
            className="w-full py-2.5 rounded-lg bg-primary-800 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            Sign in
          </button>
        </form>
        <p className="mt-6 text-center text-primary-600 text-sm">
          Don’t have an account?{' '}
          <Link to="/register" className="text-accent-600 hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  )
}
