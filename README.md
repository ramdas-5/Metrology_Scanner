# Metrology Scanner 

Metrology Scanner is a full-stack compliance platform for inspecting packaged commodities against the Legal Metrology (Packaged Commodities) Rules, 2011. It accepts a product-label image, extracts declarations with OCR, evaluates compliance, highlights violations, and generates a PDF report.

The project was developed for **Smart India Hackathon Problem Statement 26034** and is split into two independently runnable applications:

- **Backend:** FastAPI, SQLAlchemy, SQLite, OCR, optional AI extraction, classification, compliance rules, authentication, audit logs, and PDF reports.
- **Frontend:** React and Vite interface for authentication, scanning, scan history, reports, dashboard metrics, and administration.

## Contents

- [Product Capabilities](#product-capabilities)
- [Architecture](#architecture)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Scan Pipeline](#scan-pipeline)
- [API Overview](#api-overview)
- [Authentication and Roles](#authentication-and-roles)
- [OCR, AI, and Caching](#ocr-ai-and-caching)
- [Database and Generated Files](#database-and-generated-files)
- [Commands](#commands)
- [Deployment](#deployment)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Current Limitations](#current-limitations)

## Product Capabilities

### Inspector workflow

1. Sign in with an inspector or administrator account.
2. Capture a label using the camera or upload an image.
3. Extract declarations such as MRP, net quantity, manufacturer, dates, consumer-care details, country of origin, and unit sale price.
4. Evaluate the declarations against compliance rules.
5. Review status, score, confidence, and violations.
6. Correct extracted fields when necessary and re-evaluate the scan.
7. Download a generated PDF compliance report.

### Administration

Administrators can create and manage users, enable or disable accounts, review system health, and inspect audit logs. Dashboard endpoints provide inspection counts, compliance rates, and violation summaries.

## Architecture

```text
React + Vite frontend (localhost:5173)
		   |
	   JSON/REST + JWT
		   |
FastAPI backend (localhost:8000)
		   |
  OCR -> extraction -> cache -> AI/fallback -> rules -> report
		   |
	SQLite database and local files
```

The frontend and backend are separate applications. The frontend communicates with the backend through `VITE_API_URL`. The backend can operate without an OpenRouter key by using deterministic extraction and compliance rules.

## Repository Layout

```text
.
├── README.md
├── .gitignore
├── todo.md
├── metrology_backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application and middleware
│   │   ├── auth.py                 # JWT authentication and authorization
│   │   ├── config.py               # Environment-driven settings
│   │   ├── database.py             # SQLAlchemy engine and sessions
│   │   ├── db_migration.py         # Lightweight startup migrations
│   │   ├── models.py               # Database models
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── routers/                # Auth, scans, dashboard, and admin APIs
│   │   ├── services/               # OCR, AI, dedupe, classifier, rules, PDFs
│   │   ├── ml/label_classifier.h5  # Trained label classifier
│   │   ├── uploads/                # Uploaded label images
│   │   └── reports/                # Generated PDF reports
│   ├── scripts/                    # Standalone OCR and AI utilities
│   ├── seed_admin.py               # Initial administrator creation
│   ├── requirements.txt
│   ├── requirements-optional.txt   # Optional PaddleOCR dependencies
│   ├── Dockerfile
│   └── .env.example
└── metrology_frontend/
    ├── src/
    │   ├── App.jsx                 # Main application shell
    │   ├── components/             # Login, scan, reports, history, admin UI
    │   ├── context/AuthContext.jsx # Authentication state
    │   └── lib/api.js              # API client helpers
    ├── public/
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    └── .env.example
```

## Requirements

### Backend

- Python 3.10 or newer recommended
- A Python virtual environment
- Tesseract OCR installed as a system application
- SQLite for local development
- Optional OpenRouter API key for AI-assisted extraction
- Optional PaddleOCR for an alternative OCR engine

### Frontend

- Node.js and npm
- A modern browser
- Camera permission for live image capture
- A running or deployed backend API

Install Tesseract separately from Python packages:

- Windows: [UB Mannheim Tesseract builds](https://github.com/UB-Mannheim/tesseract/wiki)
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

## Quick Start

Open two terminals from the repository root.

### Terminal 1: backend

```powershell
cd metrology_backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
venv\Scripts\python.exe seed_admin.py
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

macOS/Linux activation is also supported:

```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed_admin.py
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: frontend

```powershell
cd metrology_frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the following URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

The backend reads `metrology_backend/.env`.

| Variable | Purpose | Typical value |
|---|---|---|
| `SECRET_KEY` | Signs JWT tokens | Long random private value |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `10080` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./metrology.db` |
| `CORS_ORIGINS` | Allowed browser origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `MODEL_PATH` | Keras classifier path | `app/ml/label_classifier.h5` |
| `MODEL_CLASS_NAMES` | Class names in model order | `Non-Compliant Label,Compliant Label` |
| `TESSERACT_CMD` | Optional executable path | Windows Tesseract path |
| `OCR_ENGINE` | OCR selection | `auto`, `paddle`, or `tesseract` |
| `OPENROUTER_API_KEY` | Optional AI key | Empty for fallback mode |
| `OPENROUTER_BASE_URL` | AI service endpoint | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | AI model identifier | `openai/gpt-4o-mini` |
| `AI_TIMEOUT_SECONDS` | AI request timeout | `90` |
| `SIMILARITY_THRESHOLD` | Cache match percentage | `80` |
| `SIMILARITY_SEARCH_LIMIT` | Recent scans searched | `500` |

The frontend reads `VITE_API_URL` from `metrology_frontend/.env`:

```dotenv
VITE_API_URL=http://localhost:8000
```

Never commit `.env` files or API keys. Use the checked-in `.env.example` files as templates.

## Scan Pipeline

The main endpoint is `POST /api/scans`:

1. The API accepts an image upload and product name.
2. OCR extracts visible text from the label.
3. The parser identifies mandatory declarations.
4. Recent scans are checked for similar OCR text.
5. If no cache match exists and an OpenRouter key is configured, AI extraction creates a structured result.
6. Without AI, the deterministic parser and compliance engine provide the fallback result.
7. The Keras classifier provides an additional label-quality signal.
8. The compliance engine calculates status, score, and violations.
9. The scan and extracted values are saved in SQLite.
10. A PDF report can be generated and downloaded.

## API Overview

Protected endpoints require:

```http
Authorization: Bearer <access-token>
```

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create a user |
| `POST` | `/api/auth/login` | Authenticate and return a token |
| `GET` | `/api/auth/me` | Return the current user |

### Scans

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scans` | Upload an image and create a scan |
| `GET` | `/api/scans` | Paginated scan history with filters |
| `GET` | `/api/scans/{id}` | Full scan details and violations |
| `PATCH` | `/api/scans/{id}` | Correct fields and re-evaluate |
| `DELETE` | `/api/scans/{id}` | Delete a scan; administrator only |
| `GET` | `/api/scans/{id}/report` | Download the PDF report |

The create endpoint receives a multipart `image` and `product_name`. History supports status, search, date, and page filters.

### Dashboard and administration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/stats?period=Daily` | Inspection and violation statistics |
| `GET` | `/api/dashboard/recent-activity` | Recent audit activity |
| `GET/POST` | `/api/admin/users` | List or create users |
| `PATCH` | `/api/admin/users/{id}/toggle-active` | Enable or disable a user |
| `DELETE` | `/api/admin/users/{id}` | Delete a user |
| `GET` | `/api/admin/system-health` | Check database, model, storage, and OCR |
| `GET` | `/api/admin/audit-logs` | Review the audit trail |

Supported dashboard periods are `Daily`, `Weekly`, `Monthly`, and `All`. The complete API contract is available at `/docs`.

## Authentication and Roles

The backend uses JWT bearer authentication. The login response includes an access token and user information. The frontend manages the session through `AuthContext` and attaches the token to protected requests.

The application supports inspector and administrator roles. Administrator-only actions include user management, scan deletion, system health, and audit-log access.

## OCR, AI, and Caching

`OCR_ENGINE=auto` uses PaddleOCR when installed and falls back to Tesseract. Set `OCR_ENGINE=tesseract` for a lighter setup or `OCR_ENGINE=paddle` to require PaddleOCR.

Install optional OCR dependencies with:

```bash
pip install -r requirements-optional.txt
```

When `OPENROUTER_API_KEY` is configured, the AI service converts OCR text into a stable JSON structure containing declarations, status, score, violations, confidence, and a summary. If the key is empty or the request fails, the deterministic path continues to provide a result.

Before calling AI, normalized OCR text is compared with recent scans. A match at or above `SIMILARITY_THRESHOLD` returns the existing result and avoids a duplicate row and AI request. `SIMILARITY_SEARCH_LIMIT` controls how many recent scans are compared.

Standalone utilities:

```bash
cd metrology_backend
python scripts/ocr_text.py path/to/label.jpg
python scripts/ai_extract.py path/to/label.jpg
```

These utilities print results and do not create database scans.

## Compliance and Classification

The deterministic compliance engine produces:

- Compliance status such as pass, fail, or pending
- Compliance score
- Violation list
- Supporting summary information

`app/ml/label_classifier.h5` is a MobileNetV2-backed binary classifier with a 224 x 224 x 3 input and two-class softmax output. Verify `MODEL_CLASS_NAMES` against the original training labels before relying on the classifier result.

AI and OCR are assistive signals. Critical declarations should be reviewed by an inspector, especially for blurred, rotated, reflective, or partially visible labels.

## Database and Generated Files

The backend creates the following runtime data:

- `metrology.db` - SQLite data for users, scans, violations, and audit logs.
- `app/uploads/` - uploaded label images.
- `app/reports/` - generated PDF reports.

These artifacts are ignored by Git. The `.gitkeep` files preserve empty directory structure. Production deployments need persistent database and file storage if containers can be recreated.

## Commands

### Backend

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt
python seed_admin.py
uvicorn app.main:app --reload --port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
npm install
npm run dev
npm run lint
npm run build
npm run preview
```

## Deployment

The backend includes a `Dockerfile` and can be deployed independently from the static frontend. A production deployment should:

1. Install Tesseract and required OCR system dependencies in the backend image.
2. Use persistent database and storage for scans, uploads, and reports.
3. Build the frontend with `npm run build` and host the generated `dist/` assets.
4. Set `VITE_API_URL` to the deployed backend URL at build time.
5. Set `CORS_ORIGINS` to the real frontend origin.
6. Supply secrets through the deployment platform.
7. Use HTTPS for both services.

SQLite is convenient for development but should be evaluated carefully for multi-instance production deployments. Uploaded images and reports may contain sensitive inspection data and need appropriate access controls.

## Security

- Never commit `.env`, API keys, passwords, tokens, or production databases.
- Rotate credentials immediately if they are exposed, even after removal from Git.
- Replace the example `SECRET_KEY` with a long random production value.
- Keep CORS origins narrow in production.
- Use HTTPS and deployment-managed secrets.
- Protect uploaded images and reports according to their data sensitivity.
- Review AI-generated results before treating them as final regulatory decisions.

## Troubleshooting

### Tesseract is not installed or is not in `PATH`

Install the system binary and set `TESSERACT_CMD` in `metrology_backend/.env` to the executable path. Restart the backend after changing it.

### Frontend cannot reach the API

Check that the backend is running on port 8000, `VITE_API_URL` is correct, and `CORS_ORIGINS` includes the frontend origin. Restart Vite after changing frontend environment values.

### AI extraction is unavailable

The backend falls back to deterministic extraction when the key is empty or an AI request fails. Check the key, model, network, and timeout only when AI extraction is required.

### Existing database is missing fields

Restart the backend so startup migrations can apply lightweight schema updates. Back up important data before production migrations.

### Port already in use

Run each service on another port and update the corresponding URL and CORS settings:

```bash
uvicorn app.main:app --reload --port 8001
npm run dev -- --port 5174
```

## Current Limitations

- SQLite is primarily intended for local development and small deployments.
- PaddleOCR is optional because it adds installation and runtime overhead.
- AI extraction depends on external provider availability when enabled.
- OCR and AI results require human review for low-quality images.
- Some dashboard and rule-management visualizations remain static or placeholder experiences while backend support is expanded.
- The classifier class names must be verified against the original training dataset.
- Historical trend data and custom rule editing do not yet have dedicated API endpoints.

## Detailed Documentation

- [Backend README](metrology_backend/README.md) - backend architecture, endpoint details, OCR/AI pipeline, and model notes.
- [Frontend README](metrology_frontend/README.md) - frontend setup, screen-to-endpoint mapping, and UI integration notes.
- [Project TODO](todo.md) - planned work and known follow-ups.
