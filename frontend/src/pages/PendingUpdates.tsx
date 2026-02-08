import { useState, useEffect } from 'react'
import { authHeaders } from '../context/AuthContext'

type PendingUpdate = {
  id: string
  client_id: string
  subject: string
  body_html: string
  body_plain: string | null
  change_summary: string | null
  status: string
  created_at: string
  client_display_name: string | null
  client_email: string | null
}

export default function PendingUpdates() {
  const [list, setList] = useState<PendingUpdate[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editSubject, setEditSubject] = useState('')
  const [editBody, setEditBody] = useState('')

  const load = () => {
    fetch('/api/pending-updates', { headers: authHeaders() })
      .then((r) => r.json())
      .then(setList)
      .catch(() => setList([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const startEdit = (u: PendingUpdate) => {
    setEditingId(u.id)
    setEditSubject(u.subject)
    setEditBody(u.body_plain || u.body_html)
  }

  const saveEdit = () => {
    if (!editingId) return
    fetch(`/api/pending-updates/${editingId}`, {
      method: 'PATCH',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject: editSubject, body_plain: editBody, body_html: editBody }),
    })
      .then(() => {
        setEditingId(null)
        load()
      })
      .catch(() => {})
  }

  const deleteUpdate = (id: string) => {
    if (!confirm('Delete this draft?')) return
    fetch(`/api/pending-updates/${id}`, { method: 'DELETE', headers: authHeaders() }).then(() => load())
  }

  const sendUpdate = (id: string) => {
    fetch(`/api/pending-updates/${id}/send`, { method: 'POST', headers: authHeaders() }).then(() => load())
  }

  const pending = list.filter((u) => u.status === 'pending')

  if (loading) return <p className="text-primary-600">Loading…</p>

  return (
    <div>
      <h1 className="text-2xl font-semibold text-primary-900 mb-6">Pending Updates</h1>
      <p className="text-primary-600 text-sm mb-4">
        Review, edit, send, or delete drafts. Only pending items are shown for action.
      </p>
      {pending.length === 0 ? (
        <div className="bg-white rounded-xl border border-primary-200 p-8 text-center text-primary-600">
          No pending updates. Run the agent from the Dashboard to generate drafts.
        </div>
      ) : (
        <div className="space-y-6">
          {pending.map((u) => (
            <div
              key={u.id}
              className="bg-white rounded-xl border border-primary-200 p-6 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <p className="font-medium text-primary-900">{u.client_display_name ?? 'Client'}</p>
                  {u.client_email && (
                    <p className="text-sm text-primary-600">{u.client_email}</p>
                  )}
                  {u.change_summary && (
                    <p className="text-sm text-primary-600 mt-1">Changes: {u.change_summary}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => (editingId === u.id ? saveEdit() : startEdit(u))}
                    className="px-3 py-1.5 text-sm rounded-lg border border-primary-300 text-primary-700 hover:bg-primary-100"
                  >
                    {editingId === u.id ? 'Save' : 'Edit'}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteUpdate(u.id)}
                    className="px-3 py-1.5 text-sm rounded-lg border border-red-300 text-red-700 hover:bg-red-50"
                  >
                    Delete
                  </button>
                  <button
                    type="button"
                    onClick={() => sendUpdate(u.id)}
                    className="px-3 py-1.5 text-sm rounded-lg bg-accent-500 text-white hover:bg-accent-600"
                  >
                    Send
                  </button>
                </div>
              </div>
              {editingId === u.id ? (
                <div className="space-y-2">
                  <input
                    value={editSubject}
                    onChange={(e) => setEditSubject(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-primary-300"
                    placeholder="Subject"
                  />
                  <textarea
                    value={editBody}
                    onChange={(e) => setEditBody(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-primary-300 min-h-[120px]"
                    placeholder="Body"
                  />
                </div>
              ) : (
                <>
                  <p className="font-medium text-primary-800 text-sm">Subject: {u.subject}</p>
                  <div
                    className="mt-2 text-primary-700 text-sm prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: u.body_html }}
                  />
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
