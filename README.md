# Metrology Scanner

**One project, both apps.** Software System to check compliance of Packaged
Commodities under the Legal Metrology (Packaged Commodities) Rules, 2011
(SIH Problem Statement 26034).

The FastAPI backend and the React frontend live **in the same folder, in the
same repository** - there is no separate `backend/` and `frontend/` project.
Only the *environment* is split, so each deployment target gets exactly the
values it needs:

| Part | Code | Env file | Deployed to |
|---|---|---|---|
| Backend (FastAPI + MongoDB) | `app/`, `scripts/`, `seed_admin.py`, `tests/` | `.env.backend` | **Render** (Docker, `render.yaml`) |
| Frontend (React + Vite) | `src/`, `public/`, `index.html` | `.env.frontend` | **Vercel** (`vercel.json`) |

```
metrology_scanner/
├── app/                      # BACKEND - FastAPI application
│   ├── main.py               #   app entrypoint, CORS, static mounts, startup
│   ├── config.py             #   settings (reads .env.backend)
│   ├── database.py           #   MongoDB client, collections, indexes
│   ├── models.py             #   document helpers, roles/status constants
│   ├── crud.py               #   every DB read/write + aggregation pipeline
│   ├── schemas.py            #   Pydantic request/response models
│   ├── auth.py               #   JWT auth + role-based access control
│   ├── routers/              #   auth, scans, dashboard, admin
│   ├── services/             #   OCR, OpenRouter AI, rule engine, dedupe, PDFs
│   ├── ml/label_classifier.h5#   trained Keras label classifier
│   ├── uploads/              #   captured product images (runtime)
│   └── reports/              #   generated PDF reports (runtime)
├── src/                      # FRONTEND - React + Vite + Tailwind
│   ├── App.jsx               #   shell, sidebar, routing between screens
│   ├── components/           #   Login, NewScan, ScanHistory, Reports, AdminPanel
│   ├── context/AuthContext.jsx
│   └── lib/api.js            #   every API call the UI makes
├── public/                   # static frontend assets
├── scripts/
│   ├── ocr_text.py           # CLI: OCR any image -> raw text
│   ├── ai_extract.py         # CLI: OCR + OpenRouter -> fixed JSON
│   └── migrate_sqlite_to_mongo.py  # one-off import of a legacy metrology.db
├── tests/test_api_smoke.py   # end-to-end API tests (in-memory MongoDB)
├── index.html                # Vite entry
├── package.json              # frontend deps + scripts
├── vite.config.js            # reads .env.frontend
├── vercel.json               # frontend deployment (Vercel)
├── requirements.txt          # backend deps
├── Dockerfile                # backend image (used by Render)
├── .dockerignore             # keeps the frontend out of the backend image
├── render.yaml               # backend deployment (Render)
├── seed_admin.py             # create an admin account manually
├── .env.backend.example      # backend env template
└── .env.frontend.example     # frontend env template
```

---

## 1. Run it locally

### Backend

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Install the Tesseract OCR **system** binary (not a pip package):

- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: <https://github.com/UB-Mannheim/tesseract/wiki>, then set
  `TESSERACT_CMD` in `.env.backend` to the full path of `tesseract.exe`.

Create the backend env file and point it at your database:

```bash
cp .env.backend.example .env.backend
```

```env
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=metrology
SECRET_KEY=<a long random string>
```

In MongoDB Atlas: **Database Access** needs a user, **Network Access** must
allow your IP (use `0.0.0.0/0` for the free tier, since Render's IPs are not
static).

Start the API (indexes are created and the first admin account is created
automatically when the database is empty):

```bash
uvicorn app.main:app --reload --port 8000     # or: npm run backend
```

Interactive docs: <http://localhost:8000/docs> · health: `/api/health`.

### Frontend

```bash
npm install
cp .env.frontend.example .env.frontend
npm run dev
```

`VITE_API_URL` in `.env.frontend` points at the backend
(`http://localhost:8000` by default). The dev server runs on
<http://localhost:5173> and the backend's `CORS_ORIGINS` already allows it.

> Run the two in separate terminals: `npm run dev` (UI) + `npm run backend` (API).

### Tests

```bash
pip install pytest "httpx<0.28" mongomock
npm run test:backend          # or: python -m pytest tests -q
npm run build                 # frontend production build
```

`tests/test_api_smoke.py` boots the real API against an in-memory MongoDB and
covers login, the whole scan pipeline (with stubbed OCR), the 80% similarity
cache, manual corrections, dashboard/admin aggregations, the JSON backup
export and both PDF report endpoints.

### Importing old SQLite data (optional, once)

```bash
python scripts/migrate_sqlite_to_mongo.py --sqlite metrology.db --dry-run  # report only
python scripts/migrate_sqlite_to_mongo.py --sqlite metrology.db           # write
```

---

## 2. The environment split

Nothing is shared between the two halves, so a secret can never leak into the
browser bundle:

* **`.env.backend`** - database URI, `SECRET_KEY`, CORS origins, OCR/AI keys.
  Read by `app/config.py` (`env_file=(".env", ".env.backend")`).
  Real environment variables always win over the file.
* **`.env.frontend`** - only `VITE_API_URL` (and any other `VITE_*` value).
  Read by `vite.config.js`. Real environment variables win over the file too,
  which is what Vercel's dashboard provides.
* Both files are git-ignored; the committed `*.example` templates document
  every key.

Backend keys (`app/config.py`):

| Key | Required | Notes |
|---|---|---|
| `MONGODB_URI` | yes | Atlas connection string |
| `MONGODB_DB` | yes | defaults to `metrology` |
| `SECRET_KEY` | yes | JWT signing key - change it in production |
| `CORS_ORIGINS` | yes | deployed frontend origin(s), comma separated, no trailing slash |
| `CORS_ALLOW_VERCEL` | no | `true` (default) also accepts `*.vercel.app` previews |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | no | bootstrap admin, created only when the DB is empty |
| `OPENROUTER_API_KEY` | no | blank = deterministic rule engine only |
| `CLASSIFIER_ENABLED` | no | `false` on small instances (skips TensorFlow) |
| `OCR_ENGINE` | no | `auto` \| `paddle` \| `tesseract` |
| `SIMILARITY_THRESHOLD` | no | 80% cache threshold |
| `UPLOAD_DIR` / `REPORTS_DIR` | no | point at a mounted disk to persist files |

Frontend keys:

| Key | Required | Notes |
|---|---|---|
| `VITE_API_URL` | yes | backend base URL, no trailing slash; inlined at build time |

---

## 3. Deployment

### 3.1 MongoDB Atlas

1. Create a free M0 cluster at <https://cloud.mongodb.com>.
2. **Database Access** → add a user (remember the password).
3. **Network Access** → allow `0.0.0.0/0`.
4. **Connect → Drivers → Python** → copy the `mongodb+srv://...` string.

### 3.2 Backend on Render (from THIS repository root)

1. Push this repository to GitHub.
2. Render → **New + → Blueprint** → select the repo. `render.yaml` is read
   automatically and builds `Dockerfile` (which installs Tesseract).
   *Or* **New + → Web Service → Runtime: Docker**, Dockerfile path
   `./Dockerfile`, and leave **Root Directory** empty - the Dockerfile is at
   the repo root and `.dockerignore` keeps the frontend out of the image.
3. Fill in the env vars Render asks for (`MONGODB_URI`, `CORS_ORIGINS`,
   `ADMIN_PASSWORD`, `OPENROUTER_API_KEY`). The rest have defaults.
4. Wait for `https://<service>.onrender.com/api/health` to return
   `{"status": "healthy", "database": "connected"}`.

### 3.3 Frontend on Vercel (from THIS repository root)

1. Vercel → **Add New → Project** → import the same repository.
   `vercel.json` sets the framework (`vite`), `npm run build` and the output
   directory (`dist`), so no build settings need changing. Leave
   **Root Directory** empty.
2. Before the first deploy, add the environment variable:

   | Key | Value |
   |---|---|
   | `VITE_API_URL` | `https://<your-service>.onrender.com` (no trailing slash) |

3. Deploy, then copy the deployed URL (e.g.
   `https://metrology-scanner.vercel.app`) into the backend's `CORS_ORIGINS`
   on Render and let the service restart.

> `VITE_*` values are inlined at build time, so changing `VITE_API_URL` later
> requires a **Redeploy** on Vercel.

### 3.4 Deployment notes

* **Two services, one repo.** Render runs `Dockerfile` for the API; Vercel
  builds the Vite app. Neither reads the other's env file.
* **Storage.** Render's filesystem is ephemeral: uploaded images and generated
  PDFs are lost on redeploy (the scans themselves live in Atlas). To keep them,
  mount a disk and set `UPLOAD_DIR` / `REPORTS_DIR` to it - both are commented
  out in `render.yaml`.
* **`CLASSIFIER_ENABLED=false`** in `render.yaml` because the free 512MB
  instance cannot host TensorFlow. Scans still run OCR + OpenRouter AI + the
  rule engine; only the extra label-classifier signal is skipped. Raise the
  instance size and set it to `true` to bring it back.
* **Free-tier cold starts.** A Render free service sleeps after ~15 minutes of
  inactivity; the first request afterwards can take ~50s. The UI keeps the
  session and shows an "offline" chip instead of logging you out.

---

## 4. API reference

All endpoints are prefixed `/api` and (except `/api/auth/*`) require
`Authorization: Bearer <token>`.

### Auth
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create a user (name, email, password, role) |
| POST | `/api/auth/login` | Returns `{ access_token, user }` |
| GET | `/api/auth/me` | Current logged-in user |
| POST | `/api/auth/refresh` | Exchange the token for a fresh one |

### Scans — **New Scan** & **Scan History**
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/scans` (multipart `image`, `product_name`) | Full pipeline: OCR → cache → AI/rules → stored scan |
| POST | `/api/scans/multi` (multipart `images`) | Every side of one package graded in one pass |
| GET | `/api/scans?status=&search=&from_date=&to_date=&page=&page_size=` | Paginated history |
| GET | `/api/scans/{id}` | Full scan detail with violations |
| PATCH | `/api/scans/{id}` | Inspector corrects a field → compliance re-evaluated |
| DELETE | `/api/scans/{id}` | Admin only |
| GET | `/api/scans/{id}/report` | Streams a generated PDF compliance report |

### Dashboard / Reports
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/dashboard/stats?period=Daily\|Weekly\|Monthly\|All` | Counts, compliance rate, top violations |
| GET | `/api/dashboard/recent-activity` | Audit log feed |

### Admin — **Admin Panel**
| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/admin/users` | List / create accounts (with scan counts) |
| PATCH | `/api/admin/users/{id}/toggle-active` | Enable / disable a user |
| DELETE | `/api/admin/users/{id}` | Remove a user |
| GET | `/api/admin/system-health` | Live status of DB / model / storage / OCR / AI |
| GET | `/api/admin/system-stats` | All-time KPI figures |
| GET | `/api/admin/trend?days=14` | Daily inspections/violations series |
| GET | `/api/admin/audit-logs` | Full audit trail |
| GET | `/api/admin/rules` | Rule set enforced by the engine |
| POST | `/api/admin/backup` + `/api/admin/backup-download` | Export every collection to JSON |

---

## 5. How the scan pipeline works

1. **OCR** - as much text as possible from any image (PaddleOCR when
   installed, otherwise Tesseract with several page-segmentation modes merged).
2. **Cache** - if the text is ≥ `SIMILARITY_THRESHOLD`% (default 80) similar to
   a saved scan, that saved result is returned (`cached: true`) with no AI call
   and no duplicate document.
3. **AI extraction** - with `OPENROUTER_API_KEY` set, one OpenRouter call turns
   the raw text into a fixed-shape JSON: the seven declarations (MRP, net
   quantity, manufacturer, mfg date, consumer care, country of origin, unit
   sale price) plus compliance score/status/violations and a narrative report.
   The score is always recomputed from the violations, so the number can never
   disagree with the list shown next to it.
4. **Fallback** - without a key (or if the call fails) the regex parser +
   deterministic Legal Metrology rule engine runs instead, so the app works
   offline. `ai_used` records which path produced the result.

Data lives in three MongoDB collections: `users`, `scans` (with its
`violations` embedded) and `audit_logs`.
