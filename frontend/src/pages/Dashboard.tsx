import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { authHeaders } from '../context/AuthContext'
import { Link } from 'react-router-dom'

type QBStatus = { connected: boolean; realm_id: string | null }

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [qbStatus, setQbStatus] = useState<QBStatus | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [running, setRunning] = useState(false)
  const [lastRun, setLastRun] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/qb/status', { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : null))
      .then(setQbStatus)
      .catch(() => setQbStatus(null))
  }, [])

  // After QB OAuth redirect, refresh status and clear query
  useEffect(() => {
    if (searchParams.get('qb') === 'connected') {
      setSearchParams({})
      fetch('/api/qb/status', { headers: authHeaders() })
        .then((r) => (r.ok ? r.json() : null))
        .then(setQbStatus)
    }
  }, [searchParams, setSearchParams])

  const openConnect = () => {
    setConnecting(true)
    fetch('/api/qb/connect-url', { headers: authHeaders() })
      .then((r) => r.json())
      .then((d) => {
        window.location.href = d.url
      })
      .catch(() => setConnecting(false))
  }

  const runAgent = () => {
    setRunning(true)
    fetch('/api/agent/run', { method: 'POST', headers: authHeaders() })
      .then((r) => r.json())
      .then(() => setLastRun(Date.now()))
      .finally(() => setRunning(false))
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-primary-900 mb-6">Dashboard</h1>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-white rounded-xl border border-primary-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium text-primary-800 mb-2">QuickBooks</h2>
          <p className="text-primary-600 text-sm mb-4">
            Connect your QuickBooks account so the agent can read invoices and customers.
          </p>
          {qbStatus?.connected ? (
            <p className="text-accent-600 font-medium">Connected</p>
          ) : (
            <button
              type="button"
              onClick={openConnect}
              disabled={connecting}
              className="px-4 py-2 rounded-lg bg-accent-500 text-white font-medium hover:bg-accent-600 disabled:opacity-50"
            >
              {connecting ? 'Redirecting…' : 'Connect QuickBooks'}
            </button>
          )}
        </div>

        <div className="bg-white rounded-xl border border-primary-200 p-6 shadow-sm">
          <h2 className="text-lg font-medium text-primary-800 mb-2">Run agent</h2>
          <p className="text-primary-600 text-sm mb-4">
            Check for changes and draft client update emails. New drafts appear in Pending updates.
          </p>
          <button
            type="button"
            onClick={runAgent}
            disabled={running || !qbStatus?.connected}
            className="px-4 py-2 rounded-lg bg-primary-800 text-white font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {running ? 'Running…' : 'Run agent now'}
          </button>
          {lastRun && (
            <p className="mt-2 text-primary-600 text-sm">Last run completed.</p>
          )}
        </div>
      </div>

      <div className="mt-8 flex gap-4">
        <Link
          to="/clients"
          className="text-accent-600 hover:underline font-medium"
        >
          View clients →
        </Link>
        <Link
          to="/pending-updates"
          className="text-accent-600 hover:underline font-medium"
        >
          Pending updates →
        </Link>
      </div>
    </div>
  )
}
