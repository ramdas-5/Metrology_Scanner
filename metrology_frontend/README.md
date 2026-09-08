# Metrology Scanner — Frontend

React + Vite frontend for the Legal Metrology (Packaged Commodities) Rules,
2011 compliance-scanning platform (SIH Problem Statement 26034).

This app is wired to talk to the separate FastAPI backend
(`metrology_backend`) — see `src/lib/api.js` for every API call the UI
makes, and `src/context/AuthContext.jsx` for how login/session state is
handled.

## Setup

```bash
npm install
cp .env.example .env      # set VITE_API_URL to your backend's URL
npm run dev
```

By default `VITE_API_URL=http://localhost:8000`. Point this at your
deployed backend's URL when you deploy the frontend separately (e.g. to
Vercel/Netlify), and make sure that backend's `CORS_ORIGINS` includes
this frontend's deployed origin.

## What's connected

| Screen | Talks to |
|---|---|
| **Login** | `POST /api/auth/login`, session restored via `GET /api/auth/me` |
| **Dashboard** | `GET /api/dashboard/stats` |
| **New Scan** | `POST /api/scans` - capture from the live camera **or upload any image file**. The backend runs max-text OCR (PaddleOCR/Tesseract), an 80% similarity cache check (repeat labels return the saved result without an AI call), OpenRouter AI structured extraction and stores the scan. The screen shows the AI report, OCR engine, and a "From cache" chip when a repeat scan is detected. |
| **Scan History** | `GET /api/scans` (filters/pagination), `GET /api/scans/{id}` (detail modal), `GET /api/scans/{id}/report` (PDF download) |
| **Reports** | `GET /api/dashboard/stats?period=...` |
| **Admin Panel** | `GET/POST /api/admin/users`, `PATCH /api/admin/users/{id}/toggle-active`, `GET /api/admin/system-health`, `GET /api/admin/audit-logs` |

### AI extraction pipeline

The backend's `POST /api/scans` endpoint is the whole pipeline in one call:

1. OCR the image - extract as much text as possible.
2. If the text is ≥80% similar to a previously saved scan, the saved result
   is returned from the DB (`cached: true`, no AI call).
3. Otherwise OpenRouter converts the text into the fixed JSON
   (declarations + AI compliance score/violations + report) which is saved.
4. Without an OpenRouter key the backend falls back to the deterministic
   rule engine, so the UI works either way.

See `metrology_backend/README.md` §6 for the full flow, `.env` keys and
run instructions.

Accounts are created either via the backend's `seed_admin.py` script (for
the first admin) or from the Admin Panel's "Add New Inspector" quick
action (admin-only).

Rule Management and the historical trend chart in the Admin Panel remain
static placeholders — there's no backend endpoint for custom rule
editing or historical time-series data yet.
