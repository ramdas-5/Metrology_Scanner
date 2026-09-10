# 👥 Team Roles & Responsibilities

**Team Name:** (add your team name here)
**Problem Statement ID:** 26034 — Legal Metrology Compliance Scanner
**Team Size:** 6 members

---

## Role Distribution Summary

We divided the work **by difficulty level** — the most complex part went to the Team Leader, and the easier parts went to the juniors, so that everyone contributes meaningfully and the project comes together as one complete system.

| # | Member Name | Difficulty | Main Responsibility |
|---|---|---|---|
| 1 | **Ramdas Hembram** (Team Leader) | 🔴 Hardest | System Architecture + Backend Core (OCR + AI + Compliance Engine pipeline) + Integration + Spokesperson |
| 2 | **Bidhi Dutta** | 🟠 2nd Hardest | Backend API Development + Database Design + Authentication & Security |
| 3 | **Partha Paul** | 🟡 Medium | Frontend — New Scan screen (camera/upload UI) + Dashboard |
| 4 | **Sultan Ahamed** | 🟡 Medium | Frontend — Scan History + Reports + Admin Panel screens |
| 5 | **Anirban Dhara** | 🟢 Easiest | Documentation + Presentation Slides + Test Data Collection |
| 6 | **Shubhankar Barman** | 🟢 Easiest | Testing & QA + Deployment Setup + Demo Preparation |

---

## Member 1 — Ramdas Hembram (Team Leader) 🔴 Hardest Role

> *"The brain of the project — he decides HOW everything will work and makes all the pieces talk to each other."*

### Responsibilities
1. **Overall System Architecture** — designing how the frontend, backend, database, and AI services connect together.
2. **Backend Core Scan Pipeline** — the heart of the project: `POST /api/scans` which runs **OCR → Cache check → AI extraction → Compliance rules → Save → Report** in one flow. This is in `metrology_backend/app/routers/scans.py`.
3. **Compliance Rules Engine** — implementing the Legal Metrology (Packaged Commodities) Rules, 2011 checks (`compliance_engine.py`): the 9 rules, scoring formula, Pass/Fail/Pending logic.
4. **AI Integration** — connecting the OpenRouter AI service and the offline fallback (`ai_service.py`, `ocr_service.py` integration).
5. **Multi-side scanning** — the smart feature where all sides of a package are checked together in one scan.
6. **Final Integration & Testing** — making sure backend + frontend work together end-to-end.
7. **Team Coordination** — assigning tasks, reviewing teammates' work, solving blocking issues.
8. **Spokesperson** — presenting the project to the judges (see the Presentation Speech document).

### Why this is the hardest part
The scan pipeline is where the "brain" of the project lives. If the pipeline breaks, nothing works — no scanning, no reports, no dashboard. It also requires understanding OCR, AI, ML, and legal rules all at the same time, plus integrating everyone else's work.

---

## Member 2 — Bidhi Dutta 🟠 2nd Hardest Role

> *"The backbone of the backend — he builds the API and the database that hold everything together."*

### Responsibilities
1. **Database Design** — creating the 4 tables (users, scans, violations, audit_logs) with SQLAlchemy models (`models.py`), and the auto-migration system (`db_migration.py`).
2. **API Development** — building the FastAPI routers:
   - `/api/auth/*` — register, login, me, refresh, logout
   - `/api/scans/*` — list, get, update (correction), delete, report download
   - `/api/dashboard/*` — stats & recent activity
   - `/api/admin/*` — user management, system health, audit logs, backups
3. **Authentication & Security** — JWT token creation/verification (`auth.py`), bcrypt password hashing, role-based access control (admin/inspector/viewer).
4. **Schemas** — defining the Pydantic request/response models (`schemas.py`).
5. **Data validation** — making sure only valid data enters the database.

### Why this is the 2nd hardest
The entire frontend depends on the APIs he builds. If an API endpoint is wrong, the screens break. Database design also requires careful thought — all 6 members' work stores and reads data from the tables he designed.

---

## Member 3 — Partha Paul 🟡 Medium Role

> *"The face of the product — he builds the screens the inspector sees first."*

### Responsibilities
1. **New Scan Screen** (`NewScan.jsx`) — the main scanning UI:
   - Live camera capture (using the mobile rear camera)
   - Upload button for image files
   - Multi-side capture with thumbnails
   - The result panel (extracted fields, compliance score, violations, AI report, "From cache" chip)
   - Download report button
2. **Dashboard Screen** — the home page with live statistics cards (total scans, violations, passed inspections, compliance rate) and the "SCAN NEW PRODUCT" button.

### Why this is medium difficulty
Building React components with camera access, file uploads, and dynamic result display requires solid frontend skills, but the logic comes from the backend — so he mainly "connects the UI to the API."

---

## Member 4 — Sultan Ahamed 🟡 Medium Role

> *"The data organizer — he builds the screens that show all records and reports."*

### Responsibilities
1. **Scan History Screen** (`ScanHistory.jsx`):
   - Table of all previous inspections
   - Search + filters (status, date range)
   - Pagination
   - Detail view modal (all fields, violations, AI report)
   - PDF report download per scan
2. **Reports Screen** (`Reports.jsx`):
   - KPI cards (total, compliant, violations)
   - Compliance donut chart
   - Top-5 violation analysis bars
   - Generate PDF report + Export CSV
3. **Admin Panel Screen** (`AdminPanel.jsx`) — assisting with:
   - User management UI (add/enable/disable/delete inspectors)
   - System health, audit logs, trend chart, backups

### Why this is medium difficulty
These screens have lots of UI states (loading, error, empty, filters, pagination, modals), which needs careful frontend work — but again the data comes ready-made from the backend APIs.

---

## Member 5 — Anirban Dhara 🟢 Easiest Role

> *"The storyteller — he makes sure the world understands what the team built."*

### Responsibilities
1. **Project Documentation** — writing clear documentation explaining the whole system (like the PROJECT_DOCUMENTATION.md file).
2. **Presentation Slides** — preparing the pitch deck for the judges (problem → solution → demo → impact).
3. **Test Data Collection** — collecting real packaged product label photos (biscuits, cold drinks, soaps, milk packets, etc.) from shops to test the system.
4. **README & Help Files** — making setup instructions easy for anyone to follow.

### Why this is the easiest role
Documentation and slides don't require deep coding, but they are **critical for winning** — judges read the docs and watch the presentation. It's the perfect role for a member who is still building confidence in coding while contributing hugely to the team's success.

---

## Member 6 — Shubhankar Barman 🟢 Easiest Role

> *"The quality checker — he makes sure everything works before the judges see it."*

### Responsibilities
1. **Testing & QA** — testing all screens and features:
   - Login works, scanning works, filters work, PDF downloads work
   - Scanning the same label twice returns the cached result (purple "From cache" chip)
   - Admin features (user management, backup) work
2. **Bug Reporting** — finding issues and telling the developers exactly what broke (and on which screen).
3. **Deployment Setup** — helping run the project on other machines / setting up the demo environment (installing Python, Node, Tesseract, dependencies).
4. **Demo Preparation** — preparing 3–4 sample products for the live demo, making sure the camera works and the demo runs smoothly.
5. **Data Entry** — creating inspector accounts for team members in the Admin Panel.

### Why this is the easiest role
Testing and demo setup need understanding of the system and attention to detail, but don't require writing complex code. It's the perfect "everything must work on demo day" role.

---

## 📋 Quick Reference — Who Is Under Which Part (Simplified)

| Part of the Project | Owner(s) | Difficulty |
|---|---|---|
| Architecture design + main scan pipeline (OCR→AI→Rules) | **Ramdas Hembram** | 🔴 Hardest |
| APIs + Database + Login/Security | **Bidhi Dutta** | 🟠 2nd Hardest |
| New Scan screen + Dashboard | **Partha Paul** | 🟡 Medium |
| Scan History + Reports + Admin Panel | **Sultan Ahamed** | 🟡 Medium |
| Documentation + Slides + Test images | **Anirban Dhara** | 🟢 Easiest |
| Testing + Deployment + Demo setup | **Shubhankar Barman** | 🟢 Easiest |

---

## 🗣️ Who Answers What During the Judges' Questions

When judges ask questions, divide the answering like this (but the Team Leader speaks the main pitch):

| Question Topic | Who Answers |
|---|---|
| Overall idea, architecture, pipeline | Ramdas Hembram (Team Leader) |
| How the scan pipeline / compliance engine / AI works | Ramdas Hembram |
| API endpoints, database tables, authentication, security | Bidhi Dutta |
| How the scanning UI and camera work | Partha Paul |
| Scan history, reports, admin panel features | Sultan Ahamed |
| Documentation, how the rules were studied | Anirban Dhara |
| Testing done, how the demo was prepared, deployment | Shubhankar Barman |

---

## 🎯 Team Working Rules (Suggested)

1. **Daily sync (15 min):** each member says — *what I did yesterday, what I'll do today, any blockers.*
2. **Git discipline:** never push broken code; commit small changes with clear messages.
3. **One source of truth:** the backend API is the contract — frontend members ask Bidhi for the exact response format.
4. **Demo day:** Ramdas speaks, Shubhankar handles the machine, Anirban keeps the slides in sync, everyone else stands ready to answer follow-up questions.
5. **Always have a backup demo:** if the internet fails and AI is unavailable, the system still works offline via the rule engine — and if the camera fails, use the Upload button with saved images.