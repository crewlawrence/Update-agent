import { useState, useEffect } from 'react'
import { authHeaders } from '../context/AuthContext'

type Client = {
  id: string
  display_name: string
  email: string | null
  company_name: string | null
  qb_customer_id: string
}

export default function Clients() {
  const [list, setList] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/clients', { headers: authHeaders() })
      .then((r) => r.json())
      .then(setList)
      .catch(() => setList([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-primary-600">Loading clients…</p>

  return (
    <div>
      <h1 className="text-2xl font-semibold text-primary-900 mb-6">Clients</h1>
      <p className="text-primary-600 text-sm mb-4">
        Clients are synced from QuickBooks. Connect QuickBooks and run the agent or sync from the Dashboard.
      </p>
      {list.length === 0 ? (
        <div className="bg-white rounded-xl border border-primary-200 p-8 text-center text-primary-600">
          No clients yet. Connect QuickBooks and run the agent to sync.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-primary-200 overflow-hidden shadow-sm">
          <table className="w-full">
            <thead className="bg-primary-50 border-b border-primary-200">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-primary-800">Name</th>
                <th className="text-left py-3 px-4 font-medium text-primary-800">Email</th>
                <th className="text-left py-3 px-4 font-medium text-primary-800">Company</th>
              </tr>
            </thead>
            <tbody>
              {list.map((c) => (
                <tr key={c.id} className="border-b border-primary-100 last:border-0">
                  <td className="py-3 px-4 text-primary-900">{c.display_name}</td>
                  <td className="py-3 px-4 text-primary-600">{c.email || '—'}</td>
                  <td className="py-3 px-4 text-primary-600">{c.company_name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
