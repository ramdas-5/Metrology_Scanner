# AI Image → Data Pipeline — Step-by-Step Todo

Goal: give the scanner **any image**, extract **as much text as possible**
(OCR), turn it into a **fixed-format JSON** via **OpenRouter**, compute the
metrics + report from the AI, **save it to the database**, and when a new
image is **≥ 80% similar** to an already-saved one, **return the saved value
from the DB** (no duplicate AI call).

```
 image ──► 1. OCR (max text) ──► 2. 80% cache check ──► hit? ──yes──► return saved Scan from DB
              PaddleOCR / Tesseract         (normalized text   (cached:true, similarity:XX)
              ("any image")                  vs saved scans)        └── NO AI CALL ──┘
                                                     │ miss
                                                     ▼
                              3. OpenRouter ─► fixed JSON (same keys, always)
                                 │  fields: mrp, net_quantity, manufacturer, mfg_date,
                                 │          consumer_care, country_of_origin, unit_sale_price
                                 │  + AI metrics/report: status, compliance_score,
                                 │    violations[], overall_confidence, summary
                                 ▼
                    4. save Scan + Violations + report  →  database
                    (no API key / AI error → regex parser + rule engine fallback)
```

## What was implemented

**Backend (`metrology_backend/`)**
- `app/services/ocr_service.py` — `run_ocr_engine()`: max-text OCR, engine from
  `OCR_ENGINE` (`auto` = PaddleOCR if installed else Tesseract; tesseract merges
  PSM 3/6/11). PaddleOCR failures/empty auto-fall back to Tesseract.
- `app/services/ai_service.py` — OpenRouter call → **one canonical JSON shape**
  (declarations + AI verdict + violations + narrative `summary`). Normalizes
  status/severity, retries without JSON mode, raises `AIExtractionError`.
- `app/services/dedupe_service.py` — normalized-text similarity
  (`difflib`) vs. the most recent saved scans; returns a match at
  `>= SIMILARITY_THRESHOLD` (default 80).
- `app/routers/scans.py` — `POST /api/scans` pipeline:
  OCR → cache check → AI extraction (with regex/rule-engine fallback) → save.
  Cache hits return the saved scan with `"cached": true, "similarity": 93.2`.
- `app/models.py` + `app/db_migration.py` — new Scan columns
  (`ocr_engine`, `ai_used`, `ai_model`, `ai_report`, `ai_extracted_json`);
  existing SQLite DBs are ALTER-ed automatically on startup.
- `app/schemas.py` — `ScanOut` carries the new fields + `cached`/`similarity`.
- `app/services/pdf_service.py` — PDF report now includes the analysis report
  + OCR engine + result source.
- `app/routers/admin.py` — system health shows PaddleOCR / OpenRouter / cache.
- `requirements.txt` (openai) + `requirements-optional.txt` (PaddleOCR),
  extended `.env.example`, README §6, `scripts/ocr_text.py` + `scripts/ai_extract.py`.

**Frontend (`metrology_frontend/`)**
- `NewScan.jsx` — **UPLOAD** button accepts any image file (camera still works);
  shows a "From cache • NN% similar" chip, OCR engine + AI source, and the AI
  report (collapsible).
- `ScanHistory.jsx` — detail view shows OCR engine, result source, AI report.
- README + `.env.example`.

## Setup & run checklist

### Phase 0 — Prerequisites
- [ ] Python 3.11/3.12 + `node`/`npm` installed.
- [ ] Tesseract OCR binary installed (system level), or plan to install PaddleOCR.

### Phase 1 — Backend environment
- [ ] `cd metrology_backend`
- [ ] `python -m venv venv` and activate it (`venv\Scripts\activate` on Windows)
- [ ] `pip install -r requirements.txt`  *(adds `openai` for OpenRouter)*
- [ ] *(optional, best OCR)* `pip install -r requirements-optional.txt`  (PaddleOCR, ~500MB)

### Phase 2 — Backend env config
- [ ] `cp .env.example .env`
- [ ] Set `SECRET_KEY` to a long random string.
- [ ] Set `OPENROUTER_API_KEY=sk-or-...` (get one free at https://openrouter.ai/keys).
      Leave blank to use the offline regex + rule-engine fallback.
- [ ] Pick `OCR_ENGINE` (`auto` recommended).
- [ ] Pick `OPENROUTER_MODEL` (any OpenRouter id — output format stays fixed).
- [ ] Adjust cache: `SIMILARITY_THRESHOLD=80`, `SIMILARITY_SEARCH_LIMIT=500`.

### Phase 3 — Database + run backend
- [ ] `python seed_admin.py` (first admin account, if not already created)
- [ ] `uvicorn app.main:app --reload --port 8000`
      — new Scan columns are migrated automatically on startup (check the log).
- [ ] Open `http://localhost:8000/docs` and confirm `/api/scans` is up.

### Phase 4 — Try the pipeline standalone (no DB writes)
- [ ] `python scripts/ocr_text.py some_label.jpg` — prints raw OCR text + engine
- [ ] `python scripts/ai_extract.py some_label.jpg` — prints the fixed JSON from OpenRouter

### Phase 5 — End-to-end via the API
- [ ] Login to get a token: `POST /api/auth/login` → `{"access_token": ...}`
- [ ] Upload a label: `curl -X POST http://localhost:8000/api/scans -H "Authorization: Bearer <token>" -F "image=@label.jpg" -F "product_name=Tea"`
- [ ] Check the response has `ai_used: true`, `ai_model`, `ai_report`, `status`, `compliance_score`.
- [ ] **Repeat the same upload** → response should be the **saved scan** with
      `"cached": true` and `"similarity": ~95+` — and **no AI call** was made
      (check `Audit Logs` → `SCAN_CACHE_HIT` in the Admin Panel).
- [ ] Download the PDF report — it should include the analysis report.

### Phase 6 — Frontend
- [ ] `cd metrology_frontend`
- [ ] `npm install`
- [ ] `cp .env.example .env` (keep `VITE_API_URL=http://localhost:8000`)
- [ ] `npm run dev` → http://localhost:5173
- [ ] Log in → **New Scan** → capture with camera **or click UPLOAD** and pick any image.
- [ ] Verify the result panel: extracted fields, AI Analysis report, OCR engine,
      and the purple **From cache** chip when you scan the same label again.
- [ ] **Scan History** → View a scan → AI report + OCR/source line are shown.

## Tuning & cost control
- [ ] Cache too strict/loose? Change `SIMILARITY_THRESHOLD` (80 = default).
- [ ] Cache comparing too many/few rows? Change `SIMILARITY_SEARCH_LIMIT`.
- [ ] Cheaper/faster model? Change `OPENROUTER_MODEL` (free tier ids work too).
- [ ] Prefer PaddleOCR always? Set `OCR_ENGINE=paddle`.

## Possible next steps (not implemented)
- [ ] Perceptual-image hash (e.g. `imagehash`) as a faster pre-filter before text comparison.
- [ ] Embedding-based semantic similarity instead of character diff.
- [ ] Queue the OpenRouter call as a background task so `POST /api/scans` returns fast and patches the scan when the AI finishes.
- [ ] Unit tests for `ai_service`, `dedupe_service`, `ocr_service` parsers.
- [ ] Alembic migrations when moving to Postgres.
