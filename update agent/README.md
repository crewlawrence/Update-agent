# Client Update Agent

Multi-tenant AI agent that connects to buyers’ QuickBooks via OAuth, detects meaningful changes (e.g. new invoices), and drafts brief client email updates. Updates go to a **pending** section for the buyer to approve, edit, or delete before sending. Built with the **Agno** framework.

## Features

- **Multi-tenant**: Each buyer organization is a tenant; data is isolated by `tenant_id`.
- **QuickBooks OAuth**: Buyers connect their QuickBooks account once; the app uses the token to read customers and invoices.
- **Change detection**: Per-client snapshots of invoice state; the agent runs periodically (or on demand) and detects new invoices (and can be extended for milestones).
- **AI drafts**: Agno agent drafts a short, professional email per client when there are meaningful changes.
- **Pending updates**: Drafts appear in a Pending section. Buyers can **Edit**, **Delete**, or **Approve (Send)**. Sent updates are recorded to avoid duplicate sends.
- **Client organization**: Clients are synced from QuickBooks and kept per tenant; each update is tied to one client so the right person gets the right email.

## Stack

- **Backend**: FastAPI, SQLAlchemy, JWT auth, Agno (OpenAI), intuit-oauth for QuickBooks.
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, React Router.
- **DB**: SQLite by default (set `DATABASE_URL` for PostgreSQL).

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create `backend/.env` (see `backend/.env.example`):

```env
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
# QuickBooks (create an app at developer.intuit.com)
QB_CLIENT_ID=...
QB_CLIENT_SECRET=...
QB_REDIRECT_URI=http://localhost:8000/api/qb/callback
QB_ENVIRONMENT=sandbox
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. QuickBooks Developer

1. Go to [developer.intuit.com](https://developer.intuit.com).
2. Create an app and enable **QuickBooks Online Accounting**.
3. Under Keys & credentials, copy Client ID and Client Secret.
4. Under Redirect URIs, add: `http://localhost:8000/api/qb/callback` (for production, use your real backend URL).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Register a new account (creates a tenant), then:

1. **Dashboard** → Connect QuickBooks (OAuth). After connecting you’re redirected back to the dashboard.
2. **Run agent now** to sync clients from QuickBooks and generate drafts for any client with new invoice activity.
3. **Pending updates** → Review, edit, delete, or send each draft.
4. **Clients** → View synced clients (from QuickBooks).

## API Overview

- `POST /api/auth/register` – Register (creates tenant + user).
- `POST /api/auth/login` – Login (returns JWT).
- `GET /api/qb/connect-url` – Get QuickBooks OAuth URL (requires auth).
- `GET /api/qb/callback` – OAuth callback (state = tenant_id).
- `GET /api/qb/status` – Whether QuickBooks is connected.
- `POST /api/qb/sync-clients` – Sync clients from QuickBooks.
- `GET /api/clients` – List clients for current tenant.
- `GET /api/pending-updates` – List pending/sent updates.
- `PATCH /api/pending-updates/{id}` – Edit draft.
- `DELETE /api/pending-updates/{id}` – Reject/delete draft.
- `POST /api/pending-updates/{id}/send` – Mark as sent and record in history.
- `POST /api/agent/run` – Run the agent (sync, detect changes, create drafts).

## Design

- **Clean, modern UI**: Inter font, neutral primary palette, teal accent. Simple layout with header nav and card-based content.
- **Robustness**: Token refresh for QuickBooks, per-tenant isolation, and update history to prevent duplicate sends.

## Extending

- **Milestones**: Add a “milestones” snapshot type and QB or external data source; extend `detect_invoice_changes` (or add `detect_milestone_changes`) and the agent prompt.
- **Email sending**: In `approve_and_send`, integrate SendGrid/Mailgun to send the email and store the result.
- **Scheduling**: Add APScheduler or a cron job to call `POST /api/agent/run` per tenant on a schedule.
