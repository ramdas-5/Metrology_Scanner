# Legal Metrology Compliance API (Backend)

Backend for **SIH Problem Statement 26034** — Software System to check
compliance of Packaged Commodities under the Legal Metrology (Packaged
Commodities) Rules, 2011.

Built with **FastAPI + SQLite (SQLAlchemy) + Tesseract OCR + your trained
Keras label classifier (`label_classifier.h5`)**. Deployed **separately**
from the frontend, and talks to it purely over a JSON/REST API.

---

## 1. What this backend does

1. Accepts a scanned/uploaded product label image.
2. Runs OCR (Tesseract) and extracts the mandatory Legal Metrology
   declarations: MRP, Net Quantity, Manufacturer, Mfg/Pkg Date, Consumer
   Care details, Country of Origin, Unit Sale Price.
3. Runs your trained MobileNetV2-based `label_classifier.h5` model
   (224×224×3 input, 2-class softmax output) on the image as an extra
   signal for label print-quality / compliance.
4. Runs a rule-based compliance engine against the Legal Metrology
   (Packaged Commodities) Rules, 2011 and produces a violations list +
   compliance score + Pass/Fail/Pending status.
5. Persists every scan, generates PDF compliance reports, and exposes
   dashboard/report aggregation and admin/user-management endpoints.

---

## 2. Local setup

```bash
cd metrology_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Install the Tesseract OCR **system** binary (not a pip package):

- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and
  set `TESSERACT_CMD` in `.env` to the full path of `tesseract.exe`.

Copy the environment template and edit it:

```bash
cp .env.example .env
```

Create the first admin account:

```bash
python seed_admin.py
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are then available at `http://localhost:8000/docs`.

---

## 3. Folder structure

```
metrology_backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, static file mounts
│   ├── config.py             # env-driven settings
│   ├── database.py           # SQLAlchemy engine/session
│   ├── models.py             # ORM tables: User, Scan, Violation, AuditLog
│   ├── schemas.py            # Pydantic request/response models
│   ├── auth.py                # JWT auth + role-based access control
│   ├── routers/
│   │   ├── auth.py            # /api/auth/*
│   │   ├── scans.py           # /api/scans/*  (the core scan/compliance flow)
│   │   ├── dashboard.py       # /api/dashboard/*
│   │   └── admin.py           # /api/admin/*
│   ├── services/
│   │   ├── ocr_service.py         # OCR: PaddleOCR-first, Tesseract fallback + declaration parsing
│   │   ├── ai_service.py          # OpenRouter -> fixed-shape JSON (fields + verdict + report)
│   │   ├── dedupe_service.py      # 80% similarity cache lookup (saves AI calls)
│   │   ├── classifier_service.py  # loads & runs label_classifier.h5
│   │   ├── compliance_engine.py   # Legal Metrology rule checks (fallback scorer)
│   │   └── pdf_service.py         # PDF report generation (reportlab)
│   ├── db_migration.py            # adds new Scan columns to existing SQLite DBs
│   ├── uploads/                   # captured product images
│   └── reports/                   # generated PDF reports
├── scripts/
│   ├── ocr_text.py                # CLI: OCR any image -> raw text (pipeline step 1)
│   └── ai_extract.py              # CLI: OCR + OpenRouter -> fixed JSON (pipeline step 2)
├── seed_admin.py
├── requirements.txt
├── requirements-optional.txt      # PaddleOCR (optional, heavy)
├── .env.example
├── Dockerfile
└── README.md
│   ├── ml/label_classifier.h5     # your trained model (already copied in)
│   ├── uploads/                   # captured product images
│   └── reports/                   # generated PDF reports
├── seed_admin.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## 4. API reference (matches the existing UI screens)

All endpoints are prefixed `/api` and (except `/api/auth/*`) require
`Authorization: Bearer <token>`.

### Auth
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create a user (name, email, password, role) |
| POST | `/api/auth/login` | Returns `{ access_token, user }` |
| GET | `/api/auth/me` | Current logged-in user |

### Scans — powers **New Scan** & **Scan History**
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/scans` (multipart: `image`, `product_name`) | Upload a captured image → OCR + AI classify + compliance check → stored `Scan` |
| GET | `/api/scans?status=&search=&from_date=&to_date=&page=` | Paginated scan history (filters match the ScanHistory screen) |
| GET | `/api/scans/{id}` | Full scan detail incl. violations |
| PATCH | `/api/scans/{id}` | Inspector corrects a field → compliance re-evaluated |
| DELETE | `/api/scans/{id}` | Admin-only |
| GET | `/api/scans/{id}/report` | Streams a generated PDF compliance report |

### Dashboard / Reports — powers **Reports** screen & main dashboard
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/dashboard/stats?period=Daily\|Weekly\|Monthly\|All` | Inspections/compliant/violations/rate + top violation types |
| GET | `/api/dashboard/recent-activity` | Recent audit log feed |

### Admin — powers **Admin Panel**
| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/admin/users` | List / create inspector & admin accounts |
| PATCH | `/api/admin/users/{id}/toggle-active` | Enable/disable a user |
| DELETE | `/api/admin/users/{id}` | Remove a user |
| GET | `/api/admin/system-health` | Live status of DB / model / storage / OCR |
| GET | `/api/admin/audit-logs` | Full audit trail |

---

## 5. Connecting the separate frontend

The frontend (`metrology_frontend`) currently renders **mock/hardcoded
data** on every screen (`NewScan.jsx` simulates OCR with `setTimeout`,
`Reports.jsx` and `ScanHistory.jsx` use hardcoded arrays). To wire it up:

1. Set an API base URL in the frontend, e.g. via a `.env`:
   ```
   VITE_API_URL=http://localhost:8000
   ```
2. Replace the `setTimeout` mock in `NewScan.jsx`'s `handleCapture` with
   an actual `POST` of the captured canvas image (as a Blob) to
   `POST /api/scans`, then render the fields the API returns instead of
   the hardcoded `"14.00"`, `"70 g"`, etc.
3. Replace the hardcoded arrays in `ScanHistory.jsx` and `Reports.jsx`
   with `fetch(`${VITE_API_URL}/api/scans...`)` / `/api/dashboard/stats`
   calls, sending the JWT from login in the `Authorization` header.
4. Store the JWT (e.g. in memory + `sessionStorage`) after
   `POST /api/auth/login` and attach it to every subsequent request.

Because CORS is already enabled for the frontend's dev origin
(`CORS_ORIGINS` in `.env`), the two apps can be developed and deployed
completely independently — the frontend as a static Vite build (e.g. on
Vercel/Netlify) and this backend as its own service (e.g. Docker on
Render/Railway/AWS), as required by the SIH deployment expectations.

---

## 6. AI extraction pipeline (OpenRouter) + dedupe cache

`POST /api/scans` now runs the pipeline you described end-to-end:

1. **OCR - any image, max text.** The image is read by PaddleOCR when it is
   installed (see `requirements-optional.txt`) and otherwise by Tesseract
   with several page-segmentation modes merged, so sparse and dense text
   both get captured. Engine chosen via `OCR_ENGINE` (`auto` default).
2. **Cache check before the expensive step.** The extracted text is compared
   (character similarity over normalized text) against the most recent
   saved scans. If it is `>= SIMILARITY_THRESHOLD` (default **80%**) similar
   to an existing scan, the saved result is returned straight from the DB -
   no OpenRouter call, no duplicate row. The response includes
   `"cached": true, "similarity": 93.2` so the UI can show it.
3. **AI structured extraction.** With `OPENROUTER_API_KEY` set, one
   OpenRouter call turns the raw text into **one fixed JSON shape**
   (always the same keys, `null` when a value is absent): the seven
   declarations (`mrp`, `net_quantity`, `manufacturer`, `mfg_date`,
   `consumer_care`, `country_of_origin`, `unit_sale_price`) plus the AI
   verdict (`status`, `compliance_score`, `violations[]`, `overall_confidence`)
   and a narrative `summary` report. All of it is stored on the `Scan`.
4. **Fallback.** Without an API key (or if the call fails) the old regex
   parser + deterministic rule engine runs instead, so offline operation is
   unchanged. `Scan.ai_used` records which path produced the result.

New `Scan` columns: `ocr_engine`, `ai_used`, `ai_model`, `ai_report`,
`ai_extracted_json`. Existing SQLite databases are migrated automatically on
startup (see `app/db_migration.py`).

### What to run where

```bash
cd metrology_backend
cp .env.example .env          # then add OPENROUTER_API_KEY=sk-or-... (https://openrouter.ai/keys)

# optional: install PaddleOCR for the best OCR quality (large download)
pip install -r requirements-optional.txt
# or, if you already installed core requirements before this feature:
pip install -r requirements.txt        # adds the openai client for OpenRouter

# try the two pipeline steps standalone:
python scripts/ocr_text.py some_label.jpg      # step 1: raw OCR text
python scripts/ai_extract.py some_label.jpg    # step 2: fixed JSON from OpenRouter

# run the API (which adds the cache check + persistence):
uvicorn app.main:app --reload --port 8000
```

Upload an image to `POST /api/scans` (multipart `image`) exactly as before -
now the scan also carries the AI report, `ocr_engine`, `ai_model`, and on a
repeat scan the `cached`/`similarity` flags. Demo scripts only print results;
they do not save to the database.

### Cost control knobs (`.env`)

- `SIMILARITY_THRESHOLD` - raise it (e.g. 90) for stricter cache hits, lower
  it to cache more aggressively.
- `SIMILARITY_SEARCH_LIMIT` - how many recent scans are compared.
- `OPENROUTER_MODEL` - any OpenRouter model id; the output format stays the
  same regardless of model.

---

## 7. Notes on the trained model

`app/ml/label_classifier.h5` is a MobileNetV2-backed binary classifier
(224×224×3 input, softmax over 2 classes). The class **names** it was
actually trained on aren't embedded in the file, so `MODEL_CLASS_NAMES`
in `.env` defaults to `Non-Compliant Label,Compliant Label` in that
index order — **update this to match your actual training labels**
before relying on `label_classifier_result` in reports.
