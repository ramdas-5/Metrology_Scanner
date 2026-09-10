# 🏆 THE GOAT FILE — Complete Project Explanation (The One File You Need)

**Project:** Metrology Scanner — Legal Metrology Compliance Platform
**Hackathon:** Smart India Hackathon (SIH) | **Problem Statement ID:** 26034
**Organization:** Department of Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution
**Team:** 6 Members | **Team Leader & Speaker:** Ramdas Hembram

> **What is this file?** This is the ONE document that explains our entire project — from the problem to the code to the demo — in simple words, with analogies and real examples. If you read only one file, read this one.

---

## 📖 Table of Contents

1. [The Project in One Line](#1-the-project-in-one-line)
2. [The Problem — A Real-Life Story](#2-the-problem)
3. [The Law in Simple Words](#3-the-law-in-simple-words)
4. [Our Solution — The Big Picture](#4-our-solution)
5. [Our Team — Who Did What](#5-our-team)
6. [How a Scan Works — Full Walkthrough](#6-how-a-scan-works)
7. [The Frontend — What Users See](#7-the-frontend)
8. [The Backend — The Brain](#8-the-backend)
9. [The Database — The Memory](#9-the-database)
10. [The APIs — The Waiters](#10-the-apis)
11. [OCR — Teaching the Computer to Read](#11-ocr)
12. [AI — Teaching the Computer to Understand](#12-ai)
13. [The Compliance Rules — The Law as Code](#13-the-compliance-rules)
14. [The ML Classifier — The Second Pair of Eyes](#14-the-ml-classifier)
15. [The Smart Cache — The Money Saver](#15-the-smart-cache)
16. [PDF Reports — The Evidence](#16-pdf-reports)
17. [Security — The Locks and Guards](#17-security)
18. [How to Run the Project](#18-how-to-run)
19. [What Impresses Judges — Key Selling Points](#19-key-selling-points)
20. [Quick Q&A Cheat Sheet](#20-quick-qa-cheat-sheet)
21. [Glossary — Tech Words in Simple English](#21-glossary)

---

## 1. The Project in One Line

> **📸 Point a camera at any product label → within seconds the system reads the label, checks it against Indian law, and tells you Pass or Fail — with the exact violations and a downloadable PDF report.**

**Analogy:** Think of our system as a **super-fast, super-careful inspector** who never gets tired. A human inspector checks one product in minutes; our system checks one in seconds — and checks thousands without blinking.

---

## 2. The Problem

### The story

> Imagine a shopkeeper in a small town. On his shelf there are **5,000 products** — biscuits, cold drinks, soaps, milk packets, chips, medicines. The law says every single product must show its **MRP, net quantity, manufacturer's name and address, manufacturing date, and consumer care number** on the label.
>
> Now a government inspector walks in. He picks up a biscuit packet. He reads the label with his eyes: "MRP — yes. Quantity — yes. Manufacturer — yes. Date — hmm, where is the date?... Font is very small... I can't read it properly."
>
> He does this for **one product**. There are 5,000 on the shelf — and crores across the country. **He can never check them all.**

### Why the problem exists (4 root causes)

| # | Cause | Explanation |
|---|---|---|
| 1 | **Huge scale** | Crores of packaged products in millions of shops across India. Impossible to check manually. |
| 2 | **Manual inspection is slow** | Checking one label by eye takes minutes. Tired eyes make mistakes. |
| 3 | **Non-compliance is common** | Some companies deliberately print tiny fonts or skip declarations to save money or cheat customers. |
| 4 | **No records** | Everything is paper-based. No central database of what was checked, no pattern analysis, no dashboard for enforcement heads. |

### The official problem statement asks for
- Scanning product images and labels ✅
- Detecting mandatory declarations ✅
- Checking correctness, completeness, and placement ✅
- Checking font readability ✅
- Generating compliance reports and violation summaries ✅
- Maintaining a repository of scanned products and history ✅
- Dashboards for enforcement officials ✅

---

## 3. The Law in Simple Words

**Legal Metrology Act, 2009 + Legal Metrology (Packaged Commodities) Rules, 2011** — the law that says what must be printed on every packaged product in India.

### The 7 mandatory declarations our system checks

| # | Declaration | Real example on a label | Rule Ref |
|---|---|---|---|
| 1 | Manufacturer / Packer / Importer name + address | "Manufactured by: ABC Foods Pvt. Ltd., Mumbai" | Rule 6(1)(a) |
| 2 | Net quantity in standard units | "Net Qty: 70 g" or "500 ml" | Rule 6(1)(b) / Rule 8 |
| 3 | Consumer care details | "Customer Care: 1800-123-4567" | Rule 6(1)(d) |
| 4 | MRP (Maximum Retail Price, all taxes included) | "MRP Rs. 10.00 (incl. of all taxes)" | Rule 6(1)(e) |
| 5 | Month & year of manufacture/packing/import | "Mfg. Date: Jun 2024" | Rule 6(1)(f) |
| 6 | Country of origin (for imports) | "Country of Origin: India" | — |
| 7 | Unit sale price (for multi-piece packs) | "Unit Sale Price: Rs. 2.00" | — |

**Also checked:** Is the MRP a valid positive number? Is the quantity in a standard unit? Is the label readable (font size / print quality)?

---

## 4. Our Solution

### The restaurant analogy 🍽️

Think of our system as a restaurant:

| Restaurant | Our Project |
|---|---|
| 🧑‍💼 **Waiter** (takes your order, brings food) | **Frontend** (React web app) — the screens the inspector sees and clicks |
| 👨‍🍳 **Kitchen** (does the actual cooking) | **Backend** (FastAPI server) — does all the smart work: OCR, AI, rules, PDFs |
| 🧊 **Storage room** (keeps ingredients & records) | **Database** (SQLite) — stores users, scans, violations, logs |
| 📋 **Menu** (what you can order) | **APIs** — the list of things the frontend can ask the backend to do |
| 🧾 **Bill / receipt** (proof of your order) | **PDF reports** — official evidence of each inspection |

### The pipeline (our "recipe")

```
Capture label image
      │
      ▼
1️⃣ Save image           → stored for evidence
      ▼
2️⃣ OCR                 → reads ALL text from the image
      ▼
3️⃣ Cache check         → same product before? Return saved result (saves money)
      ▼
4️⃣ ML Classifier       → looks at the image itself (font/print quality)
      ▼
5️⃣ AI (if available)   → understands the text, structures it, writes a report
      ▼
6️⃣ Rules engine        → checks against the law (works even offline)
      ▼
7️⃣ Save + Report       → stored in database, PDF can be downloaded
```

---

## 5. Our Team

Six members, work divided **by difficulty** — leader takes the hardest part, everyone contributes.

| Member | Difficulty | Role in the project (simple words) |
|---|---|---|
| **Ramdas Hembram** (Leader) | 🔴 Hardest | The **architect + brain** — designed how everything connects, built the main scan pipeline and the compliance rules. Also the **speaker**. |
| **Bidhi Dutta** | 🟠 2nd Hardest | The **backbone** — built the APIs (the waiters), the database (storage), and security (locks). |
| **Partha Paul** | 🟡 Medium | The **face** — built the New Scan screen (camera/upload) and Dashboard. |
| **Sultan Ahamed** | 🟡 Medium | The **organizer** — built Scan History, Reports, and Admin Panel screens. |
| **Anirban Dhara** | 🟢 Easiest | The **storyteller** — documentation, slides, and collected real product labels for testing. |
| **Shubhankar Barman** | 🟢 Easiest | The **quality checker** — testing, deployment setup, and prepared the live demo. |

**How we coordinated:** the backend API was our "contract" (frontend built against the exact formats Bidhi published) → nobody waited on anybody. Plus a 15-minute daily sync and git discipline.

---

## 6. How a Scan Works — Full Walkthrough

Let's follow **one real example**: an inspector scanning a **biscuit packet**.

### What the inspector does (frontend)
1. **Logs in** with email + password.
2. Clicks **New Scan** → the phone camera opens automatically (or he clicks UPLOAD and picks a photo).
3. Captures the **front** of the packet, then the **back** (multi-side support — up to 6 sides).
4. Types the product name (optional) → presses **SCAN**.

### What happens inside (backend) — step by step

| Step | What happens | Real example |
|---|---|---|
| 1. Save | Image is saved to `app/uploads/` | `biscuit_front.jpg` |
| 2. OCR | Computer reads all visible text | Raw text: `"PARLE BISCUIT... MRP Rs 10.00 ... Net wt 70 g ... Mfd by XYZ Ltd Mumbai ... Mfg date Jun 2024 ..."` |
| 3. Cache | Checks if ≥80% similar to an old scan | First time: no match → continue. Same packet again later: match → return saved result instantly! |
| 4. Classifier | ML model looks at the image itself | Predicts "Compliant Label" (92%) |
| 5. AI | OpenRouter structures the text into fixed fields + writes a report | `{mrp: "10.00", net_quantity: "70 g", manufacturer: "XYZ Ltd, Mumbai", mfg_date: "Jun 2024", ...}` |
| 6. Rules | Compliance engine checks the 9 rules | All present → score 100 → **Passed** |
| 7. Save | Scan + violations + audit log saved | One new row in `scans`, audit log "SCAN_CREATED" |
| 8. Report | PDF can be generated on demand | `report_abc123.pdf` |

### What the inspector sees (frontend result)
- ✅ Status badge: **Passed**
- Compliance score with a progress bar: **100%**
- All 7 extracted declarations (MRP, quantity, manufacturer, date, consumer care, origin, unit price)
- Violations list (if any) with rule references
- AI inspection report (collapsible)
- **DOWNLOAD REPORT** button → PDF

### If the label has a violation, e.g. MRP missing
| Declaration | Detected? | Violation created |
|---|---|---|
| MRP | ❌ Not detected | `MISSING_MRP` — **major** — Rule 6(1)(e) |
| Quantity | ✅ 70 g | — |
| Manufacturer | ✅ XYZ Ltd | — |

Score: `100 − 15 = 85` → Status: **Failed** (because a major violation exists).

---

## 7. The Frontend — What Users See

Built with **React + Vite + Tailwind CSS** (the "waiter" — pretty, fast, easy to use). One web app, works on mobile AND desktop browsers.

### The 6 screens

**1. Login** — email + password → gets a secure token → logged in.
*Analogy: showing your ID card at the gate.*

**2. Dashboard** — home screen with live numbers: Total Scans Today, Violations Detected, Passed Inspections, Compliance Rate, Top Violation, Pending Review. Big **SCAN NEW PRODUCT** button.
*Analogy: the control room with all the meters.*

**3. New Scan** (the star) — camera opens automatically; upload button for images; **multi-side capture** (front, back, sides with thumbnails); one SCAN button; results panel with all extracted fields, score, violations, AI report, "From cache" chip, and PDF download.
*Analogy: the main workbench where inspection happens.*

**4. Scan History** — table of every past inspection with **search** (product/MRP/inspector), **filters** (status, date range), **pagination**, a **View** button (full detail modal) and **Download** (PDF).
*Analogy: the filing cabinet — every record, searchable.*

**5. Reports** — KPI cards, compliance **donut chart** (Passed/Violations/Pending), **top-5 violations** analysis, **GENERATE PDF** (all-time system report) and **EXPORT CSV** (editable format).
*Analogy: the monthly report the boss reads.*

**6. Admin Panel** (admin only) — user management (add/disable/delete inspectors), system health checks, audit logs, 14-day trend chart, compliance donut, rule list, database backup.
*Analogy: the manager's office.*

---

## 8. The Backend — The Brain

Built with **Python + FastAPI** (the "kitchen" — where all intelligence lives). It has:

| File | Job (simple words) |
|---|---|
| `main.py` | The front door — starts the app, sets up CORS, serves images/PDFs, loads ML model at startup |
| `config.py` | The settings box — reads the `.env` file (secret keys, API keys, options) |
| `database.py` | The connection to the storage room (SQLAlchemy) |
| `models.py` | Defines the 4 tables (blueprint of the storage) |
| `schemas.py` | The exact shapes of data going in/out (like order forms) |
| `auth.py` | The security guard — creates tokens, checks passwords, checks roles |
| `routers/` | The 4 waiters: auth, scans, dashboard, admin — each handles its own requests |
| `services/` | The chefs: OCR, AI, dedupe, classifier, compliance, PDF |

**Why FastAPI?** It's fast, modern, auto-generates interactive API docs at `/docs`, and validates every request automatically — perfect for a hackathon where we needed to move quickly and reliably.

---

## 9. The Database — The Memory

**SQLite** — a single file (`metrology.db`) holding 4 "registers":

### 📒 Register 1: `users` — who can use the system
| Column | Example |
|---|---|
| name | "Ramdas Hembram" |
| email | "ramdas@metrology.gov.in" |
| role | admin / inspector / viewer |
| is_active | true (or false if disabled by admin) |

### 📒 Register 2: `scans` — every inspection ever done
One row per scan, with the 7 declarations, raw OCR text, confidence %, AI metadata (used? which model? AI report?), compliance status & score, and who did it.

### 📒 Register 3: `violations` — every problem found
| Column | Example |
|---|---|
| code | `MISSING_MRP` |
| severity | major |
| rule_reference | Rule 6(1)(e) |
| description | "The Maximum Retail Price inclusive of all taxes must be declared..." |

### 📒 Register 4: `audit_logs` — who did what, when
| Column | Example |
|---|---|
| action | `SCAN_CREATED` / `SCAN_CACHE_HIT` / `USER_CREATED` / `BACKUP_CREATED` |
| details | "Scan abc123 created with status Failed via OpenRouter (openai/gpt-4o-mini)" |

**Relationships (simple):** one user → many scans → many violations. One user → many audit logs.

**Bonus:** the backend **auto-migrates** — if new columns are added later, existing databases are upgraded automatically on startup.

---

## 10. The APIs — The Waiters

**API = Application Programming Interface** — the "phone numbers" the frontend uses to order work from the backend. All are under `http://localhost:8000/api/...` and most need a token (`Authorization: Bearer <token>`).

### 🎫 Auth (identity)
| API | Simple meaning |
|---|---|
| `POST /api/auth/register` | Create a user account |
| `POST /api/auth/login` | Login → returns token |
| `GET /api/auth/me` | "Who am I?" |
| `POST /api/auth/refresh` | Get a fresh token (stay logged in) |
| `POST /api/auth/logout` | Log out |

### 📸 Scans (the main work)
| API | Simple meaning |
|---|---|
| `POST /api/scans` | Upload image → run the full pipeline → save scan |
| `POST /api/scans/multi` | Upload up to 6 sides of one package → one combined result |
| `GET /api/scans` | List scans (with status/search/date/page filters) |
| `GET /api/scans/{id}` | Full detail of one scan |
| `PATCH /api/scans/{id}` | Inspector corrects a field → system re-checks automatically |
| `DELETE /api/scans/{id}` | Delete (admin only) |
| `GET /api/scans/{id}/report` | Download PDF report |

### 📊 Dashboard (statistics)
| API | Simple meaning |
|---|---|
| `GET /api/dashboard/stats?period=Daily|Weekly|Monthly|All` | Counts, compliance rate, top violations |
| `GET /api/dashboard/recent-activity` | Recent activity feed |

### 🛠️ Admin (management — admin only)
| API | Simple meaning |
|---|---|
| `GET/POST /api/admin/users` | List / create users |
| `PATCH /api/admin/users/{id}/toggle-active` | Enable / disable a user |
| `DELETE /api/admin/users/{id}` | Delete a user |
| `GET /api/admin/system-health` | Health check: DB, model, storage, OCR, AI, cache |
| `GET /api/admin/audit-logs` | Full audit trail |
| `GET /api/admin/system-stats` | All-time KPIs |
| `GET /api/admin/trend` | Daily chart data (last 14 days) |
| `GET /api/admin/rules` | The 9 compliance rules |
| `POST /api/admin/backup` | Backup the database |
| `GET /api/admin/summary-report` | All-time analytics PDF |

> 🎁 **Free extras:** Swagger UI at `/docs` — the backend generates interactive API documentation automatically.

---

## 11. OCR — Teaching the Computer to Read

**OCR = Optical Character Recognition** — software that reads text from a picture.

### Real example (before → after)
**Image contains:** `MRP Rs. 10.00 (incl. of all taxes)`
**OCR output:** `MRP Rs. 10.00 (incl. of all taxes)` (as text)

### Our OCR strategy
| Engine | When | Why |
|---|---|---|
| **PaddleOCR** | If installed | Best quality on printed labels |
| **Tesseract** | Fallback / light setup | Works everywhere, lightweight |

- `OCR_ENGINE=auto` (default) = try Paddle, fall back to Tesseract. A scan **never fails** because of OCR.
- **Speed tricks:** downscale huge photos to 1600px, grayscale, auto-contrast; merge 3 Tesseract modes; skip extra passes when the first pass already got enough text.

### The parser (offline extraction)
After OCR, **regex patterns** (text-hunting rules) pull out each declaration:
- MRP → looks for "MRP" / "M.R.P" + ₹/Rs + number
- Quantity → "Net Qty" / "Net Wt" + number + g/kg/ml/l/pcs
- Manufacturer → "Mfd. by" / "Manufactured by" / "Packed by"
- Date → "Mfg. Date" + month/year patterns
- Consumer care → 1800 numbers, emails
- Origin → "Country of Origin" / "Made in"

**This is the offline fallback** — it works with zero internet.

---

## 12. AI — Teaching the Computer to Understand

OCR reads, but **AI understands**. With an OpenRouter API key (default model: `openai/gpt-4o-mini`), the raw OCR text is sent to the AI with a strict instruction: *"return exactly this JSON shape, always"*.

### Real example (before → after)
**Raw OCR text (messy):**
```
PARLE BISCUITS 200g BISCUITS MADE FROM WHEAT MRP RS 14.00
INCL OF ALL TAXES NET WT 200 G MFD BY PARLE PRODUCTS PVT LTD
MUMBAI MFD DATE JUN 2024 CUSTOMER CARE 1800-123-4567
COUNTRY OF ORIGIN INDIA
```

**AI output (clean, fixed shape):**
```json
{
  "mrp": "14.00",
  "net_quantity": "200 g",
  "manufacturer": "Parle Products Pvt Ltd, Mumbai",
  "mfg_date": "Jun 2024",
  "consumer_care": "1800-123-4567",
  "country_of_origin": "India",
  "unit_sale_price": null,
  "status": "Passed",
  "compliance_score": 100,
  "violations": [],
  "overall_confidence": 95,
  "summary": "The label contains all mandatory declarations and appears compliant..."
}
```

**Why fixed shape matters:** every key always present (null if missing) → database and UI always know the format, no matter what label was scanned.

**Reliability controls:** temperature 0 (no randomness), max 900 tokens, JSON-mode with retry, values normalized, and **if the AI fails → automatic fallback** to OCR parser + rules. The app never breaks.

---

## 13. The Compliance Rules — The Law as Code

`compliance_engine.py` — the 9 rules, written in code, exactly as in our documentation:

| Code | What it catches | Severity | Rule Ref |
|---|---|---|---|
| MISSING_MANUFACTURER | No manufacturer/packer/importer details | major | Rule 6(1)(a) |
| MISSING_NET_QUANTITY | No net quantity | major | Rule 6(1)(b) / Rule 8 |
| MISSING_MRP | No MRP | major | Rule 6(1)(e) |
| MISSING_MFG_DATE | No month & year of manufacture | major | Rule 6(1)(f) |
| MISSING_CONSUMER_CARE | No consumer care contact | minor | Rule 6(1)(d) |
| INVALID_MRP_FORMAT | MRP not a valid amount | minor | Rule 6(1)(e) |
| INVALID_MRP_VALUE | MRP is zero/negative | major | Rule 6(1)(e) |
| NON_STANDARD_UNIT | Quantity not in standard units | minor | Rule 8 |
| AI_FLAGGED_LABEL | ML classifier flags unreadable label | major | Rule 5 |

### The scoring formula (simple math)
```
Score = 100 − (15 × major violations) − (6 × minor violations)
```

### The status logic (a traffic light)
| Situation | Result |
|---|---|
| No violations | ✅ **Passed** |
| Any major violation | ❌ **Failed** |
| Only minor violations | ⏳ **Pending Review** |

**Example:** biscuit missing MRP (major) + missing consumer care (minor) → Score = 100 − 15 − 6 = **79** → **Failed**.

---

## 14. The ML Classifier — The Second Pair of Eyes

- **What:** a trained **MobileNetV2** neural network (file: `label_classifier.h5`).
- **Input:** the label image, resized to 224×224.
- **Output:** "Compliant Label" or "Non-Compliant Label" with a confidence %.
- **Why:** the law cares about **font size and print quality** — text alone can't judge that. The model adds a vision-level check.
- **Analogy:** like a senior inspector who can tell at a glance that a label's print is too small to read — before even reading a word.
- **Extra:** loads once in the background at startup (fast first scan); if the model is missing, scans continue without it.

---

## 15. The Smart Cache — The Money Saver

**Problem:** AI calls cost money, and inspectors scan the same products repeatedly.

**Solution:** before calling AI, compare the new OCR text with recent scans:
- Normalize text (lowercase, remove punctuation)
- Quick pre-filters (length + word overlap)
- Compare with `difflib` similarity
- **≥ 80% similar** → return the saved result from the database. No AI call. No duplicate row.

**User-visible:** a purple chip **"From cache • 95% similar"** on the result panel, plus a "cache hits saved" counter in the admin dashboard, and every cache hit logged in the audit trail.

**Tunable:** `SIMILARITY_THRESHOLD` (default 80) and `SIMILARITY_SEARCH_LIMIT` (default 500 recent scans).

---

## 16. PDF Reports — The Evidence

Generated with **ReportLab**. Each report contains:
1. Official header (Department of Consumer Affairs)
2. Scan ID, product, inspector name & email, dates, status, score
3. **The product image** (photographic evidence 🖼️)
4. **All 7 extracted declarations** ("Not detected" where missing)
5. **Violations table** (code, severity, rule reference)
6. **AI analysis report** (plain-English summary)
7. Official disclaimer (supports, not replaces, officer verification)

**Plus:** all-time system summary PDF (admin) and **CSV export** (editable format requirement ✅).

---

## 17. Security — The Locks and Guards

| Protection | Simple meaning |
|---|---|
| 🔒 **bcrypt password hashing** | Passwords are scrambled — even the database can't reveal them |
| 🔑 **JWT tokens** | A secure "pass" that expires (7 days), refreshed every 12h by the app |
| 🚪 **Role checks on the server** | Admin/Inspector/Viewer — enforced in code, not just hidden buttons |
| 🛡️ **CORS limits** | Only approved websites can call our API |
| 📋 **Audit trail** | Every action recorded — who did what, when |
| 🚫 **Backup filename validation** | No path-traversal attacks |
| ⚠️ **Honest design** | Low-confidence results say "Pending Review"; reports say AI supports — not replaces — officer judgment |

---

## 18. How to Run the Project

### Prerequisites
- Python 3.10+, Node.js + npm, Tesseract OCR (system install)

### Backend (Terminal 1)
```bash
cd metrology_backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
# (optional better OCR): pip install -r requirements-optional.txt
cp .env.example .env          # edit: add SECRET_KEY, optional OPENROUTER_API_KEY
python seed_admin.py          # create the first admin account
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Frontend (Terminal 2)
```bash
cd metrology_frontend
npm install
cp .env.example .env          # keep VITE_API_URL=http://localhost:8000
npm run dev
```

### Open
| What | URL |
|---|---|
| App | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |

Login with the admin from `seed_admin.py`, then create inspector accounts in the Admin Panel. Done! 🎉

---

## 19. Key Selling Points (What Impresses Judges)

1. **It actually works** — live demo, real camera, real OCR, real PDF. Not a mockup.
2. **Multi-side scanning** — the whole package checked as one product (declarations on the back count!).
3. **Offline fallback** — works without internet/AI. Built for field reality.
4. **Smart cache** — repeat scans cost nothing. Built for government-scale economics.
5. **Evidence-first** — image + extracted fields + violations + PDF. Built for enforcement.
6. **Full audit trail** — accountability built in.
7. **Honest AI design** — fixed JSON shape, normalized output, "Pending Review" for uncertainty.
8. **Complete problem-statement coverage** — every requirement mapped to a feature.
9. **Clean architecture** — frontend/backend separate, deployable independently, Docker-ready.
10. **A coordinated team** — six members, clear roles, everyone can answer for their part.

---

## 20. Quick Q&A Cheat Sheet

| Question | 30-second answer |
|---|---|
| What did you build? | A web app that scans product label photos and automatically checks them against the Legal Metrology (Packaged Commodities) Rules 2011 — Pass/Fail + violations + PDF report. |
| Tech stack? | React + Vite frontend; Python FastAPI backend; SQLite (SQLAlchemy); Tesseract/PaddleOCR; OpenRouter AI; TensorFlow ML classifier; ReportLab PDFs; Docker. |
| How accurate? | High on clean labels; low-quality images honestly flagged as "Pending Review". AI/OCR support — not replace — officer verification. |
| What if AI/internet fails? | Automatic fallback to the regex parser + rule engine. The system works fully offline. |
| What makes it special? | Multi-side scanning, offline fallback, cost-saving cache, complete audit trail, evidence-backed PDFs. |
| Who uses it? | Legal Metrology enforcement officers and department admins. |
| Database? | SQLite now (zero-config, ideal for field trials); SQLAlchemy makes PostgreSQL a config change for production. |

---

## 21. Glossary — Tech Words in Simple English

| Word | Simple meaning |
|---|---|
| **Frontend** | The part you see and click (React web app) |
| **Backend** | The part that does the work behind the scenes (FastAPI server) |
| **API** | A "menu" of requests the frontend can make to the backend |
| **Database** | The storage room where all records are kept (SQLite) |
| **OCR** | Software that reads text from images |
| **AI / LLM** | A model that understands language and structures information (via OpenRouter) |
| **ML classifier** | A trained model that looks at images and predicts a category |
| **JWT** | A secure digital pass for logged-in users |
| **CORS** | A browser rule that controls which websites may call our API |
| **Cache** | Remembering past results so we don't redo expensive work |
| **Pipeline** | The ordered sequence of steps a scan goes through |
| **Multipart upload** | Sending a file (image) to the server as part of a request |
| **Schema** | The defined shape of data (what fields, what types) |
| **Migration** | Automatically updating an old database to match new code |
| **Audit log** | A diary of every important action in the system |
| **Compliance score** | A 0–100 number showing how compliant a label is |
| **Severity** | How serious a violation is (major = serious, minor = small) |

---

*The End — but only the beginning of the demo. 🚀 Good luck, Team!*

*Related documents: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) (technical deep-dive) · [TEAM_ROLES_AND_RESPONSIBILITIES.md](TEAM_ROLES_AND_RESPONSIBILITIES.md) · [PRESENTATION_SPEECH.md](PRESENTATION_SPEECH.md) · [JUDGE_QA_GUIDE.md](JUDGE_QA_GUIDE.md)*