# 🏷️ Metrology Scanner — Complete Project Documentation

**Project Name:** Metrology Scanner (Legal Metrology Compliance Platform)
**Hackathon:** Smart India Hackathon (SIH)
**Problem Statement ID:** 26034
**Problem Statement Title:** *Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.*
**Organization:** Ministry of Consumer Affairs, Food & Public Distribution — Department of Consumer Affairs (DoCA)

---

## Table of Contents

1. [What is this project? (Simple explanation)](#1-what-is-this-project)
2. [The Problem We Are Solving](#2-the-problem-we-are-solving)
3. [Mandatory Declarations We Check](#3-mandatory-declarations-we-check)
4. [Our Solution — At a Glance](#4-our-solution)
5. [System Architecture](#5-system-architecture)
6. [Technology Stack](#6-technology-stack)
7. [How a Scan Works (Step by Step)](#7-how-a-scan-works)
8. [The Frontend (React + Vite)](#8-the-frontend)
9. [The Backend (FastAPI)](#9-the-backend)
10. [The Database (SQLite)](#10-the-database)
11. [The APIs (Complete List)](#11-the-apis)
12. [OCR — How Text Is Read](#12-ocr)
13. [AI Extraction (OpenRouter)](#13-ai-extraction)
14. [Compliance Rules Engine](#14-compliance-rules-engine)
15. [ML Label Classifier](#15-ml-label-classifier)
16. [Smart Cache / Dedupe System](#16-smart-cache)
17. [PDF Report Generation](#17-pdf-reports)
18. [Authentication, Roles & Security](#18-authentication-and-security)
19. [How to Run the Project](#19-how-to-run-the-project)
20. [Deployment](#20-deployment)
21. [Project Folder Structure](#21-folder-structure)
22. [Limitations & Future Scope](#22-limitations-and-future-scope)

---

## 1. What Is This Project?

Metrology Scanner is a **web application** that helps government inspectors check whether **packaged products** (biscuits, cold drinks, soaps, medicines, milk packets, etc.) follow Indian **Legal Metrology rules** or not.

**The simple idea:**

> 📸 Take a photo of a product label → the system reads the text → checks if all required declarations (MRP, quantity, manufacturer, date, etc.) are present and correct → gives a Pass / Fail result → generates a PDF report.

Before this system, inspectors had to **manually check every product label with their eyes** — which is slow, tiring, and human errors happen. Our system does this **automatically in seconds using OCR + AI**.

The project is split into **two separate applications** that talk to each other:

| Part | What it is | Like... |
|---|---|---|
| **Frontend** | React web app (what the inspector sees and clicks) | The "showroom" |
| **Backend** | FastAPI server (does all the smart work: OCR, AI, rules, database, PDFs) | The "factory" behind the showroom |

---

## 2. The Problem We Are Solving

In India, under the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011**, every packaged product **must** print certain information on its label. This is for:

- ✅ **Consumer protection** — buyers must know the real price, quantity, and who made the product.
- ✅ **Fair trade practices** — no company should cheat customers with wrong MRP or hidden quantity.
- ✅ **Transparency** — enforcement agencies can catch dishonest manufacturers.

**The real-world pain points:**
- 🛒 There are **crores of packaged products** in retail stores, supermarkets, and e-commerce sites.
- 👀 Checking every label **manually** takes a lot of time and manpower.
- ❌ Many products have **missing declarations, wrong MRP, tiny unreadable fonts**, etc.
- 📉 Enforcement agencies can inspect only a tiny fraction of products.

**Our goal:** Build a software system that can **scan a product label image** and automatically detect whether it complies with the rules — quickly, consistently, and at scale.

---

## 3. Mandatory Declarations We Check

Under **Rule 6(1)** of the LM(PC) Rules 2011, a package must declare (our system checks these):

| # | Declaration | What it means | Rule Reference |
|---|---|---|---|
| 1 | **Manufacturer / Packer / Importer details** | Name and complete address of who made/packed/imported the product | Rule 6(1)(a) |
| 2 | **Net Quantity** | How much product is inside (in standard units like g, kg, ml, l, pieces) | Rule 6(1)(b) / Rule 8 |
| 3 | **Consumer care details** | Phone number / email / website for complaints | Rule 6(1)(d) |
| 4 | **MRP (Maximum Retail Price)** | Price inclusive of all taxes, e.g. "MRP Rs. 10.00 (incl. of all taxes)" | Rule 6(1)(e) |
| 5 | **Month & Year of manufacture / packing / import** | e.g. "Mfg. Date: Jun 2024" | Rule 6(1)(f) |
| 6 | **Country of Origin** | Where the product comes from (for imports) | — |
| 7 | **Unit Sale Price** | For multi-piece packs | — |

**Also checked:**
- Whether the MRP is in a **valid format** (a proper positive number).
- Whether the quantity uses a **standard metric unit**.
- Whether the **font is readable / print quality is good** (using the AI image classifier).

---

## 4. Our Solution

```
┌────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Capture   │ →  │  Read text   │ →  │  Check rules │ →  │  Result +    │
│  Product   │    │  (OCR)       │    │  (Compliance)│    │  PDF Report  │
│  Label     │    │  + AI        │    │              │    │              │
└────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
   Camera /          Extract all       Compare with        Pass / Fail,
   Upload image      declarations      Legal Metrology     score, list of
                    from the label     Rules, 2011         violations, PDF
```

### Key Features (from the problem statement → our implementation)

| Problem Statement Requirement | Our Implementation |
|---|---|
| Image upload & product scanning | 📸 Live camera capture + file upload, single-side & **multi-side** scanning |
| Extraction of declarations | 🔍 OCR (Tesseract / PaddleOCR) + AI (OpenRouter GPT-4o-mini) |
| Font size & readability analysis | 🧠 Trained MobileNetV2 ML classifier flags unreadable/non-compliant labels |
| Detection of missing/misleading declarations | ⚖️ Rule-based compliance engine (9 rules) + AI verdict |
| Compliance / non-compliance reports | 📄 Auto-generated PDF reports |
| Photographs & supporting evidence | 🖼️ Uploaded label images are saved and attached to reports |
| Repository of scanned products & history | 🗄️ SQLite database + Scan History screen with search & filters |
| Role-based user access & secure auth | 🔐 JWT tokens, 3 roles (Admin / Inspector / Viewer), bcrypt passwords |
| Dashboard for monitoring | 📊 Live dashboard with stats, charts, audit logs, admin panel |
| Export reports to PDF & editable formats | 📥 PDF download + CSV export |

---

## 5. System Architecture

```
                    ┌─────────────────────────────────────┐
                    │        FRONTEND (React + Vite)      │
                    │  localhost:5173                     │
                    │  Login | Dashboard | New Scan |     │
                    │  Scan History | Reports | Admin     │
                    └──────────────┬──────────────────────┘
                                   │  JSON / REST + JWT token
                                   ▼
                    ┌─────────────────────────────────────┐
                    │        BACKEND (FastAPI)            │
                    │  localhost:8000                     │
                    │                                     │
                    │  Auth ─── Scans ─── Dashboard ──────│
                    │                     Admin           │
                    │                                     │
                    │  SERVICES:                          │
                    │   OCR ──► Cache ──► AI ──► Rules    │
                    │   └──► Classifier ──► PDF Report    │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │   SQLite Database (metrology.db)    │
                    │   users, scans, violations,         │
                    │   audit_logs                        │
                    └─────────────────────────────────────┘
```

**Data flow in simple words:**
1. The browser (React app) shows screens to the inspector.
2. When the inspector scans a product, the browser sends the image to the backend.
3. The backend does all the smart processing (OCR → cache check → AI → rules).
4. The result is saved in SQLite and sent back to the browser.
5. The browser shows the result and lets the user download a PDF.

---

## 6. Technology Stack

### Backend (`metrology_backend/`)
| Technology | Purpose |
|---|---|
| **Python 3.10+** | Main programming language |
| **FastAPI** | Web framework for building the API |
| **Uvicorn** | Server that runs the FastAPI app |
| **SQLAlchemy 2.0** | Object Relational Mapper — lets Python talk to the database |
| **SQLite** | Database (file-based, no server needed) |
| **Pydantic v2** | Validates data going in and out of the API |
| **Tesseract OCR** (pytesseract) | Reads text from images |
| **PaddleOCR** *(optional)* | Better-quality OCR engine (auto-used if installed) |
| **TensorFlow / Keras** | Runs the trained label classifier (`.h5` model) |
| **OpenRouter** (openai client) | AI service that converts OCR text into structured JSON |
| **ReportLab** | Generates PDF compliance reports |
| **python-jose + passlib/bcrypt** | JWT tokens + password hashing |
| **python-multipart** | Handles image file uploads |

### Frontend (`metrology_frontend/`)
| Technology | Purpose |
|---|---|
| **React 19** | JavaScript library for building the UI |
| **Vite 8** | Fast dev server and build tool |
| **Tailwind CSS 4** | Styling the interface |
| **lucide-react** | Icons |

### Environment / Config
- **`.env` files** hold configuration (API keys, secrets, settings) — never committed to Git.
- Backend reads `metrology_backend/.env`; frontend reads `metrology_frontend/.env`.

---

## 7. How a Scan Works (Step by Step)

This is the **heart of the project**. When an inspector uploads/captures a label image and clicks **SCAN**, the backend runs this pipeline (`POST /api/scans`):

```
 Image uploaded
      │
      ▼
 1. SAVE IMAGE ──► stored in app/uploads/
      │
      ▼
 2. OCR ──► read as much text as possible
      │      (PaddleOCR if installed, else Tesseract)
      │      returns raw_text + engine name
      ▼
 3. CACHE CHECK ──► is this text ≥80% similar to an old scan?
      │              YES ──► return saved result (cached: true, NO AI call)
      │              NO  ──► continue
      ▼
 4. CLASSIFIER ──► run the ML model on the image
      │            (extra signal: is the label readable/compliant-looking?)
      ▼
 5. AI EXTRACTION (if API key configured)
      │            OpenRouter turns raw text into a FIXED JSON:
      │            {mrp, net_quantity, manufacturer, mfg_date,
      │             consumer_care, country_of_origin, unit_sale_price,
      │             status, compliance_score, violations[],
      │             overall_confidence, summary}
      ▼
 6. FALLBACK (if no AI key / AI fails)
      │            Regex parser + rule-based compliance engine
      │            (works 100% offline)
      ▼
 7. SAVE ──► Scan + Violations + Audit Log saved in SQLite
      │
      ▼
 8. RESULT ──► JSON sent back to frontend
      │
      ▼
 9. PDF ──► report can be generated on demand (GET /api/scans/{id}/report)
```

**Why this design is smart:**
- 💰 **Cache check saves money** — scanning the same product twice doesn't call the paid AI again.
- 🛡️ **Fallback keeps it working** — even without internet/AI key, the system works with rules.
- ⚡ **Speed** — the classifier loads once at startup in the background, so the first scan isn't slow.

---

## 8. The Frontend

The frontend is a **single-page application** (one HTML page, JavaScript changes the screens). It has **6 screens**:

### 8.1 Login Screen (`Login.jsx`)
- Inspector enters **email + password**.
- Calls `POST /api/auth/login` → gets a **JWT token** back.
- The token is stored and attached to every future request.
- Account creation is done by the admin (Admin Panel) or `seed_admin.py` script.

### 8.2 Dashboard (`App.jsx` → `Dashboard`)
- Shows live statistics from the backend: **Total Scans Today, Violations Detected, Passed Inspections, Compliance Rate, Top Violation, Pending Review**.
- Big **"SCAN NEW PRODUCT"** button to jump into scanning.
- Data source: `GET /api/dashboard/stats?period=Daily`.

### 8.3 New Scan (`NewScan.jsx`) — the main screen
- 📷 Opens the **camera automatically** (mobile-friendly, uses rear camera).
- 📤 Also has an **UPLOAD** button to pick image files.
- 🧩 Supports **multi-side scanning** — capture/upload the front, back, sides; then press **SCAN ONCE** and the whole package is checked together (a declaration printed on the back satisfies the check even if missing on the front).
- Shows the result panel:
  - Extracted declarations (MRP, Net Quantity, Manufacturer, Mfg Date, Consumer Info, AI Label Classifier result)
  - **Compliance Score** with a progress bar
  - **Status badge** (Passed / Failed / Pending Review)
  - **List of violations** with rule references
  - **AI inspection report** (collapsible)
  - **"From cache • NN% similar"** purple chip when a repeat product is detected
  - OCR engine used + result source (AI vs rule engine)
  - **DOWNLOAD REPORT** button → PDF

### 8.4 Scan History (`ScanHistory.jsx`)
- Table of all previous scans with pagination (10 per page).
- **Filters:** search by product/MRP/inspector, status, from-date, to-date.
- **View** button opens a detail modal (all fields, violations, AI report).
- **Download** button fetches the PDF report.
- Shows which inspector performed each scan.

### 8.5 Reports (`Reports.jsx`)
- KPI cards: Total Inspections, Compliant, Violations.
- **Compliance Overview donut chart** (Passed / Violations / Pending proportions — real data).
- **Top 5 violations** bar analysis.
- **GENERATE PDF REPORT** → downloads an all-time system summary PDF from the backend.
- **EXPORT DATA** → downloads a CSV file (editable format ✅).
- Period selector: Daily / Weekly / Monthly.

### 8.6 Admin Panel (`AdminPanel.jsx`) — admin-only
- KPI cards: Total Users, Active Users, Total Inspections, Failed Scans, AI Scans, System Health.
- **Inspection Trend** line chart (last 14 days, real data).
- **Compliance Overview** donut chart.
- **Recent System Activities** (live audit log).
- **User Management** — add / enable / disable / delete inspectors.
- **Rule Management** — shows the 9 real compliance rules enforced by the engine.
- **Top Violations** list.
- **Backup Now** — creates a downloadable SQLite backup.
- **Generate System Report** — all-time analytics PDF.

### How the frontend talks to the backend
- `src/lib/api.js` — one central place with all API calls (auth, scans, dashboard, admin namespaces). It automatically adds the JWT token to every request.
- `src/context/AuthContext.jsx` — manages login state:
  - Stores token + user in `localStorage` (survives page refresh).
  - **Auto-refreshes the token every 12 hours** so sessions don't die.
  - If the backend is temporarily offline, it **keeps the user logged in** and shows a "Server offline — reconnecting…" banner instead of logging out.

---

## 9. The Backend

The backend is a **FastAPI** application. Structure:

```
metrology_backend/app/
├── main.py               # Creates the app, CORS, static files, startup
├── config.py             # Reads .env settings
├── database.py           # SQLAlchemy engine + sessions
├── models.py             # Database tables (User, Scan, Violation, AuditLog)
├── schemas.py            # Request/response data shapes (Pydantic)
├── auth.py               # JWT creation, password hashing, role checks
├── db_migration.py       # Adds new columns to old databases automatically
├── routers/              # API endpoints grouped by area
│   ├── auth.py           # /api/auth/*
│   ├── scans.py          # /api/scans/*   (the core scan pipeline)
│   ├── dashboard.py      # /api/dashboard/*
│   └── admin.py          # /api/admin/*
├── services/             # Business logic / intelligence
│   ├── ocr_service.py        # OCR engines + declaration parser
│   ├── ai_service.py         # OpenRouter AI structured extraction
│   ├── dedupe_service.py     # 80% similarity cache
│   ├── classifier_service.py # ML label classifier
│   ├── compliance_engine.py  # Legal Metrology rules + scoring
│   └── pdf_service.py        # PDF report generation
├── ml/label_classifier.h5 # Trained ML model
├── uploads/               # Saved label images
└── reports/               # Generated PDFs
```

### `main.py` — the app's front door
- Creates the FastAPI app titled **"Legal Metrology Compliance API"**.
- Enables **CORS** so the frontend (port 5173) can call it.
- Serves uploaded images at `/files/uploads/...` and PDFs at `/files/reports/...`.
- On startup, loads the ML model in the background (warmup) so scans are fast.
- Mounts all 4 routers (auth, scans, dashboard, admin).

### `config.py` — all settings in one place
Reads from `.env`: SECRET_KEY, DATABASE_URL, CORS_ORIGINS, MODEL_PATH, OCR_ENGINE, OPENROUTER_API_KEY/MODEL, SIMILARITY_THRESHOLD, etc.

### `auth.py` — security helpers
- `hash_password` / `verify_password` (bcrypt).
- `create_access_token` (JWT with expiry).
- `get_current_user` — checks the token on every protected request.
- `require_roles("admin", ...)` — blocks endpoints by role.

---

## 10. The Database

The database is **SQLite** — a single file (`metrology.db`) with 4 tables:

### Table 1: `users`
| Column | Type | Notes |
|---|---|---|
| id | String (UUID) | Primary key |
| name | String | Full name |
| email | String | Unique, used for login |
| hashed_password | String | bcrypt-hashed, never stored as plain text |
| role | Enum | `admin` / `inspector` / `viewer` |
| is_active | Boolean | Admin can disable accounts |
| created_at | DateTime | |

### Table 2: `scans` (one row per product inspection)
| Column | Type | Notes |
|---|---|---|
| id | String (UUID) | Primary key |
| inspector_id | FK → users.id | Who did the scan |
| product_name | String | Optional product name |
| image_path | String | Saved label image (or JSON list for multi-side) |
| mrp, net_quantity, manufacturer, mfg_date, consumer_care, country_of_origin, unit_sale_price | String | The 7 extracted declarations |
| ocr_raw_text | Text | Full text OCR read from the label |
| overall_confidence | Float | 0–100, how confident extraction is |
| label_classifier_result | String | e.g. "Compliant Label" |
| label_classifier_confidence | Float | 0–100 |
| ocr_engine | String | `paddle` or `tesseract` |
| ai_used | Boolean | Was AI used for this scan? |
| ai_model | String | Model name (e.g. openai/gpt-4o-mini) |
| ai_report | Text | AI-written inspection summary |
| ai_extracted_json | Text | Raw AI JSON (audit trail) |
| status | Enum | `Passed` / `Failed` / `Pending Review` |
| compliance_score | Float | 0–100 |
| created_at | DateTime | |

### Table 3: `violations` (problems found on a label)
| Column | Type | Notes |
|---|---|---|
| id | String (UUID) | Primary key |
| scan_id | FK → scans.id | Which scan |
| code | String | e.g. `MISSING_MRP` |
| label | String | Human-readable title |
| severity | String | `major` or `minor` |
| rule_reference | String | e.g. `Rule 6(1)(e)` |
| description | Text | Full explanation |

### Table 4: `audit_logs` (who did what, when)
| Column | Type | Notes |
|---|---|---|
| id | String (UUID) | Primary key |
| user_id | FK → users.id | |
| action | String | e.g. `SCAN_CREATED`, `SCAN_CACHE_HIT`, `USER_CREATED`, `BACKUP_CREATED` |
| details | Text | Extra info |
| created_at | DateTime | |

### Relationships (how tables connect)
```
users 1 ──── ∞ scans 1 ──── ∞ violations
  │                         
  └────── ∞ audit_logs
```

### Smart migration
`db_migration.py` — if the code adds a new column later, the backend **automatically adds it** to existing databases on startup (no manual SQL needed for SQLite).

---

## 11. The APIs

**Base URL:** `http://localhost:8000` (all endpoints start with `/api`)
**Authentication:** Almost all endpoints need header `Authorization: Bearer <token>`.

### 🔐 Auth APIs (`/api/auth`)
| Method | Endpoint | What it does | Who can call |
|---|---|---|---|
| POST | `/api/auth/register` | Create a user (name, email, password, role) | Anyone (used by admin/seed) |
| POST | `/api/auth/login` | Login → returns `{access_token, user}` | Anyone |
| GET | `/api/auth/me` | Get current logged-in user | Logged-in users |
| POST | `/api/auth/refresh` | Get a fresh token (keeps sessions alive) | Logged-in users |
| POST | `/api/auth/logout` | Log out (client clears token) | Logged-in users |

### 📸 Scan APIs (`/api/scans`)
| Method | Endpoint | What it does | Who can call |
|---|---|---|---|
| POST | `/api/scans` | **Upload image + scan** (multipart: `image`, optional `product_name`) — runs the full OCR→cache→AI→rules pipeline | Inspector/Admin |
| POST | `/api/scans/multi` | **Multi-side scan** — up to 6 images of one package in one request | Inspector/Admin |
| GET | `/api/scans` | List scans with filters: `status`, `search`, `from_date`, `to_date`, `page`, `page_size` | Inspector/Admin |
| GET | `/api/scans/{id}` | Full details of one scan + violations | Inspector/Admin |
| PATCH | `/api/scans/{id}` | Inspector corrects a field → compliance re-checked automatically | Inspector/Admin |
| DELETE | `/api/scans/{id}` | Delete a scan | Admin only |
| GET | `/api/scans/{id}/report` | Download the PDF compliance report | Inspector/Admin |

### 📊 Dashboard APIs (`/api/dashboard`)
| Method | Endpoint | What it does | Who can call |
|---|---|---|---|
| GET | `/api/dashboard/stats?period=Daily|Weekly|Monthly|All` | Total inspections, compliant count, violations, compliance rate, top violations | Inspector/Admin |
| GET | `/api/dashboard/recent-activity?limit=10` | Recent audit activity feed | Inspector/Admin |

### 🛠️ Admin APIs (`/api/admin`) — all Admin only
| Method | Endpoint | What it does |
|---|---|---|
| GET | `/api/admin/users` | List all users with scan counts |
| POST | `/api/admin/users` | Create a user |
| PATCH | `/api/admin/users/{id}/toggle-active` | Enable / disable a user |
| DELETE | `/api/admin/users/{id}` | Delete a user |
| GET | `/api/admin/system-health` | Check DB, ML model, storage, OCR, AI, cache status |
| GET | `/api/admin/audit-logs?limit=50` | Full audit trail |
| GET | `/api/admin/system-stats` | All-time KPIs (inspections, pass/fail/pending, AI scans, cache hits, averages) |
| GET | `/api/admin/trend?days=14` | Per-day inspection/violation counts for charts |
| GET | `/api/admin/rules` | The 9 compliance rules actually enforced |
| POST | `/api/admin/backup` | Create a SQLite backup file |
| GET | `/api/admin/backup-download?file=...` | Download a backup (filename validated against path traversal) |
| GET | `/api/admin/summary-report` | Generate the all-time system summary PDF |

### Other
- `GET /` → service status
- `GET /api/health` → health check
- `GET /files/uploads/{file}` → label images (static)
- `GET /files/reports/{file}` → generated PDFs (static)
- **Swagger UI** (interactive API docs): `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 12. OCR

**OCR = Optical Character Recognition** — the technology that "reads" text from a picture, like a scanner + translator.

### Two engines, one goal: get as much text as possible
| Engine | Quality | Install |
|---|---|---|
| **PaddleOCR** (preferred) | Best on printed labels/documents | `pip install -r requirements-optional.txt` (heavy, ~500MB) |
| **Tesseract** | Good, light, works everywhere | System binary (apt/brew/Windows installer) |

Setting `OCR_ENGINE=auto` (default) uses **PaddleOCR if installed, otherwise Tesseract** — and if Paddle fails or returns nothing, it automatically falls back to Tesseract. A scan never fails because of OCR.

### Image preparation (speed tricks)
1. Downscale huge camera photos to max 1600px on the long edge (faster, still legible).
2. Convert to **grayscale** (halves processing time).
3. Auto-contrast to sharpen text.

### Tesseract strategy
Runs **3 page-segmentation modes** (PSM 3, 6, 11) and merges unique lines:
- PSM 3 — fully automatic (normal labels)
- PSM 6 — uniform blocks (dense text)
- PSM 11 — sparse text (scattered small text)

💡 **Fast path:** if the first pass already reads ≥220 characters in ≥6 lines, the extra passes are skipped — a normal scan returns in a few seconds instead of ten.

### Declaration parser (`parse_declarations`)
Uses **regex patterns** to pull out of the raw text:
- MRP (looks for `MRP` / `M.R.P` / `Maximum Retail Price` + ₹/Rs + number)
- Net quantity (`Net Qty` / `Net Wt` + number + g/kg/ml/l/pcs)
- Manufacturer (`Mfd. by` / `Manufactured by` / `Packed by` / `Importer`)
- Mfg/Pkg date (month-year patterns)
- Consumer care (1800 toll-free numbers, emails)
- Country of origin (`Country of Origin` / `Made in`)
- Unit sale price (`USP`)

This parser is the **offline fallback** — it always works, even with no internet or AI key.

---

## 13. AI Extraction (OpenRouter)

When an `OPENROUTER_API_KEY` is configured, the raw OCR text is sent to an LLM (default `openai/gpt-4o-mini`) with a carefully written **system prompt**.

### What the AI returns (always the same shape)
```json
{
  "product_name": "Biscuit",
  "mrp": "14.00",
  "net_quantity": "70 g",
  "manufacturer": "ABC Foods Pvt Ltd, Mumbai",
  "mfg_date": "Jun 2024",
  "consumer_care": "1800-123-4567",
  "country_of_origin": "India",
  "unit_sale_price": null,
  "status": "Passed",
  "compliance_score": 95,
  "violations": [],
  "overall_confidence": 88,
  "summary": "The label contains all mandatory declarations..."
}
```

**Why "fixed shape" matters:** every key is always present (null when missing), so the backend, database, and UI can rely on one format no matter what the image contains.

### Quality controls in the code
- `temperature: 0` → consistent, non-random answers.
- `max_tokens: 900` → bounded response, no runaway output.
- Native **JSON mode** first; retries once without it if the model rejects the format (but never retries timeouts — that would double latency).
- **Normalizes** everything: status casing, severity values, score clamped 0–100, null/empty cleanup.
- If the AI call fails → **`AIExtractionError`** → the system silently falls back to the regex + rule engine. The app never breaks.

---

## 14. Compliance Rules Engine

`compliance_engine.py` implements a **codified version of the mandatory-declaration checks** under the LM(PC) Rules 2011.

### The 9 enforced rules
| Code | Check | Severity | Rule Ref |
|---|---|---|---|
| MISSING_MANUFACTURER | Manufacturer/Packer/Importer details missing | major | Rule 6(1)(a) |
| MISSING_NET_QUANTITY | Net quantity missing/invalid | major | Rule 6(1)(b) / Rule 8 |
| MISSING_MRP | MRP missing | major | Rule 6(1)(e) |
| MISSING_MFG_DATE | Month & year of manufacture/packing/import missing | major | Rule 6(1)(f) |
| MISSING_CONSUMER_CARE | Consumer care contact missing | minor | Rule 6(1)(d) |
| INVALID_MRP_FORMAT | MRP not a valid amount | minor | Rule 6(1)(e) |
| INVALID_MRP_VALUE | MRP not a positive number | major | Rule 6(1)(e) |
| NON_STANDARD_UNIT | Net quantity not in standard metric unit | minor | Rule 8 |
| AI_FLAGGED_LABEL | ML classifier flags label as non-compliant (font/print quality) | major | Rule 5 |

### Scoring formula
```
compliance_score = 100 − (15 × number of major violations) − (6 × number of minor violations)
(never below 0)
```

### Status decision
| Condition | Status |
|---|---|
| No violations | ✅ **Passed** |
| Any major violation | ❌ **Failed** |
| Only minor violations | ⏳ **Pending Review** |

### Summary report
The engine also writes a human-readable summary ("Rule-engine result: Failed with a compliance score of 55%. Not detected on the label: MISSING_MRP, MISSING_MFG_DATE. ...") used as the AI report when running in fallback mode.

---

## 15. ML Label Classifier

- **Model:** `app/ml/label_classifier.h5` — a **MobileNetV2-based** binary classifier.
- **Input:** image resized to **224×224×3** (RGB).
- **Output:** softmax over **2 classes** — by default `["Non-Compliant Label", "Compliant Label"]` (configurable via `MODEL_CLASS_NAMES`).
- **Purpose:** an extra "vision" signal for **label quality / print quality / format compliance** — e.g., tiny fonts, bad placement. If it predicts "Non-Compliant", the compliance engine adds the `AI_FLAGGED_LABEL` major violation.
- **Performance:** loaded **once at startup in a background thread** (warmup), so the first scan doesn't wait 10–20s for model loading.
- **Resilience:** if the model file is missing or TensorFlow fails, scans continue **without it** (best-effort signal, never blocks a scan).

---

## 16. Smart Cache / Dedupe System

**Problem:** Calling the AI for every scan costs money and time, and scanning the same product twice is common.

**Solution (`dedupe_service.py`):** Before calling the AI, the new OCR text is compared against the most recent saved scans.

1. **Normalize** the text (lowercase, remove punctuation, collapse spaces).
2. **Pre-filter** cheaply: reject if length ratio < 0.4 or token overlap < 0.35.
3. **Compare** with `difflib.SequenceMatcher` (character-level similarity, 0–100%).
4. If similarity **≥ 80%** (`SIMILARITY_THRESHOLD`) to an existing scan → **return the saved scan** with `cached: true` and the similarity %, and log a `SCAN_CACHE_HIT` audit entry. **No AI call, no duplicate row.**

**Tunable knobs (`.env`):**
- `SIMILARITY_THRESHOLD` (default 80) — higher = stricter cache.
- `SIMILARITY_SEARCH_LIMIT` (default 500) — how many recent scans to compare.

---

## 17. PDF Reports

Generated with **ReportLab** (`pdf_service.py`).

### Per-scan report (`generate_scan_report`)
A4 PDF containing:
1. **Header** — "Legal Metrology Compliance Report", Department of Consumer Affairs.
2. **Meta table** — Scan ID, Product, Inspected By (name + email), dates, Status, Compliance Score, OCR Engine, Result Source (AI vs rule engine).
3. **Captured product image** (attached evidence 🖼️).
4. **Extracted Mandatory Declarations table** — all 7 fields, "Not detected" when missing.
5. **Violations table** — code, description, severity, rule reference.
6. **Analysis Report** — AI narrative summary.
7. **Disclaimer** — report supports, not replaces, manual verification by an authorized officer.

### System summary report (`generate_summary_report`)
All-time analytics PDF: total/passed/failed/pending, compliance rate, top violations, inspector activity table.

### CSV export
The Reports screen also exports data as a **CSV file** (editable format requirement ✅).

---

## 18. Authentication and Security

### How login works
1. Inspector submits email + password → backend verifies against bcrypt hash.
2. Backend creates a **JWT token** signed with `SECRET_KEY` (HS256), valid **7 days** by default.
3. Token contains user id + role. Frontend stores it in `localStorage` and sends it as `Authorization: Bearer <token>` on every request.
4. Token auto-refreshes every 12 hours so sessions stay alive.

### Roles
| Role | Can do |
|---|---|
| **admin** | Everything + user management, delete scans, system health, audit logs, backups |
| **inspector** | Scan products, view history/reports, correct extracted fields |
| **viewer** | Read-only access |

Role checks are enforced **on the backend** (`require_roles`) — not just hidden in the UI — so users can't bypass by editing the frontend.

### Security practices implemented
- 🔒 Passwords hashed with **bcrypt** — never stored in plain text.
- 🔑 JWT signed with a secret from `.env` (never committed to Git).
- 🚪 CORS limited to configured frontend origins.
- 🛡️ Backup download validates filenames (no path traversal).
- 📋 Full **audit trail** of every action (scans, user changes, backups, cache hits).
- ⚠️ AI/OCR results are labeled as assistive — human review required for final regulatory decisions.
- 📄 `.gitignore` excludes `.env`, databases, uploads, and reports.

---

## 19. How to Run the Project

### Prerequisites
- **Python 3.10+**
- **Node.js + npm**
- **Tesseract OCR** installed as a system program
  - Windows: UB-Mannheim Tesseract builds (set `TESSERACT_CMD` in `.env`)
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

### Step 1 — Backend (Terminal 1)
```bash
cd metrology_backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
# or: source venv/bin/activate && pip install -r requirements.txt

# (optional, best OCR): pip install -r requirements-optional.txt

cp .env.example .env        # then edit .env (add SECRET_KEY, optional OPENROUTER_API_KEY)
python seed_admin.py        # create the first admin account
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Step 2 — Frontend (Terminal 2)
```bash
cd metrology_frontend
npm install
cp .env.example .env        # keep VITE_API_URL=http://localhost:8000
npm run dev
```

### Step 3 — Open
| What | URL |
|---|---|
| Frontend app | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger API docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

Login with the admin account created by `seed_admin.py`, then create inspector accounts from the Admin Panel.

### Try the pipeline standalone (no database writes)
```bash
cd metrology_backend
python scripts/ocr_text.py some_label.jpg     # step 1: raw OCR text
python scripts/ai_extract.py some_label.jpg   # step 2: fixed JSON from OpenRouter
```

---

## 20. Deployment

### Backend
- A **Dockerfile** is included (`python:3.11-slim` + Tesseract + requirements).
- Deploy as its own service (Docker on Render/Railway/AWS, etc.).

### Frontend
- Build static files: `npm run build` → produces `dist/`.
- Host on Vercel/Netlify/any static host.

### Production checklist
1. Set `VITE_API_URL` to the deployed backend URL **at build time**.
2. Set `CORS_ORIGINS` to the real frontend origin.
3. Use a **long random SECRET_KEY**.
4. Use **persistent storage** for the database, uploads, and reports (containers can be recreated).
5. Consider upgrading SQLite → **PostgreSQL** for multi-instance production.
6. Use **HTTPS** everywhere.
7. Supply secrets through the deployment platform (never in code).

---

## 21. Folder Structure

```
.
├── README.md
├── todo.md
├── Documentation/                    ← this documentation
├── metrology_backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app + middleware
│   │   ├── auth.py                   # JWT + roles
│   │   ├── config.py                 # .env settings
│   │   ├── database.py               # SQLAlchemy engine/session
│   │   ├── db_migration.py           # auto schema updates
│   │   ├── models.py                 # DB tables
│   │   ├── schemas.py                # Pydantic models
│   │   ├── routers/                  # auth, scans, dashboard, admin
│   │   ├── services/                 # ocr, ai, dedupe, classifier, compliance, pdf
│   │   ├── ml/label_classifier.h5    # trained ML model
│   │   ├── uploads/                  # label images
│   │   └── reports/                  # PDF reports
│   ├── scripts/                      # standalone OCR/AI utilities
│   ├── seed_admin.py                 # first admin account
│   ├── requirements.txt
│   ├── requirements-optional.txt     # PaddleOCR
│   ├── Dockerfile
│   └── .env.example
└── metrology_frontend/
    ├── src/
    │   ├── App.jsx                   # app shell + sidebar + routing
    │   ├── components/               # Login, NewScan, ScanHistory, Reports, AdminPanel
    │   ├── context/AuthContext.jsx   # session state
    │   └── lib/api.js                # all API calls
    ├── public/
    ├── package.json
    ├── vite.config.js
    └── .env.example
```

---

## 22. Limitations & Future Scope

### Current limitations (honest list)
- **SQLite** is for development/small deployments — needs PostgreSQL for large scale.
- **PaddleOCR** is optional because it's a heavy install.
- **AI depends on external provider** availability (has offline fallback).
- OCR/AI results need **human review** for low-quality images (blurred, rotated, reflective).
- Classifier class names must match the original training data labels.
- Some admin visualizations were simplified during the hackathon.

### Future scope / next steps
- 📱 **Mobile app** (Android/iOS) for field officers.
- 🔍 Perceptual image hashing for even faster duplicate detection.
- 🧠 Embedding-based semantic similarity instead of character diff.
- ⏳ Background AI queueing so scans return instantly and patch later.
- 📏 **Actual font-size measurement** from images (pixel-to-mm calibration) instead of ML-only proxy.
- 🌐 Multilingual label support (Hindi + regional languages).
- 🗄️ Alembic migrations + PostgreSQL.
- 🧪 Unit tests for the services.
- 🖥️ Offline-first mobile mode for no-network field inspections.

---

*Documentation prepared for Smart India Hackathon — Problem Statement 26034. See also: [Team Roles & Responsibilities](TEAM_ROLES_AND_RESPONSIBILITIES.md), [Presentation Speech](PRESENTATION_SPEECH.md), [Judge Q&A Guide](JUDGE_QA_GUIDE.md).*