import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [error, setError] = useState('')
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await register(email, password, fullName, tenantName)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-primary-100">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg border border-primary-200 p-8">
        <h1 className="text-2xl font-semibold text-primary-900 mb-2">Create account</h1>
        <p className="text-primary-600 mb-6">Client Update Agent</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-primary-700 mb-1">Organization name</label>
            <input
              type="text"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
              placeholder="Your company or team name"
              className="w-full px-4 py-2 rounded-lg border border-primary-300 focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-primary-700 mb-1">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-primary-300 focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
            />
          </div>
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
              autoComplete="new-password"
            />
          </div>
          <button
            type="submit"
            className="w-full py-2.5 rounded-lg bg-primary-800 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            Create account
          </button>
        </form>
        <p className="mt-6 text-center text-primary-600 text-sm">
          Already have an account?{' '}
          <Link to="/login" className="text-accent-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
