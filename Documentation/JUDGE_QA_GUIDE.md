# 🧑‍⚖️ Judge Q&A Guide — Frequently Asked & Tricky Questions

**Team:** 6 members (Team Leader: Ramdas Hembram)
**Problem Statement ID:** 26034 — Legal Metrology Compliance Scanner

> **How to use:** Practice these out loud. The answers are written in the team's voice. Divide by topic as per the Team Roles document. If a judge asks something you haven't prepared — stay calm, structure your answer as *"Our system does X today, and here's how we'd extend it to Y."*

---

## Part A — Frequently Asked Questions (FAQs)

### Q1. What does your project do? (Explain in 30 seconds)
> "Our system checks whether packaged products in India comply with the Legal Metrology (Packaged Commodities) Rules, 2011. An inspector captures or uploads a photo of a product label. The system reads the text using OCR, extracts the mandatory declarations like MRP, net quantity, manufacturer details, manufacturing date, and consumer care information, checks them against the rules, and instantly gives a Pass/Fail result with a compliance score, a list of violations with rule references, and a downloadable PDF report. It also maintains a full inspection history and provides dashboards for enforcement officials."

### Q2. Which problem statement are you solving and who is the organization?
> "Problem Statement ID 26034, given by the Department of Consumer Affairs under the Ministry of Consumer Affairs, Food & Public Distribution."

### Q3. What mandatory declarations does the system check?
> "Seven declarations: (1) name and address of manufacturer/packer/importer, (2) net quantity in standard units, (3) month and year of manufacture/packing/import, (4) MRP inclusive of all taxes, (5) consumer care details, (6) country of origin, and (7) unit sale price for multi-piece packs. We also validate the MRP format and value, the standard unit used, and label readability via the ML classifier."

### Q4. What is OCR and why do you need it?
> "OCR stands for Optical Character Recognition — it converts text visible in an image into machine-readable text. We need it because the label is an image, and to check compliance we first have to read the text. We support two OCR engines: PaddleOCR for best quality, and Tesseract as a lightweight fallback, configurable through a single setting."

### Q5. How do you handle the case when the AI is not available?
> "We designed a two-path system. When an OpenRouter API key is configured, an AI model structures the OCR text and gives a compliance verdict. If the key is missing, the internet is down, or the AI call fails, the system automatically falls back to a deterministic regex parser plus a rule-based compliance engine that checks the same nine rules. So the system works 100% offline with the exact same scan flow."

### Q6. How accurate is your system?
> "We track an overall confidence score per scan, based on how many declarations were found and the AI's self-assessed confidence. On clean, well-lit labels the extraction is highly reliable. On blurred, rotated, or reflective images, accuracy drops — so our system explicitly flags low-confidence scans as 'Pending Review' and the report states that AI/OCR results support, not replace, manual verification by an authorized officer. That is the honest, correct design for an enforcement tool."

### Q7. What does 'multi-side scanning' mean?
> "Many products have declarations spread across the package — MRP on the front, manufacturing details on the back. Our New Scan screen lets the inspector capture or upload up to six sides and press SCAN once. All sides are OCR-read and merged with side markers, and the whole package is graded in a single pass. So a declaration printed on the back satisfies the check even if it's missing from the front — just like a real inspector examining the whole package."

### Q8. How do you generate reports?
> "Every scan generates a professional PDF report using ReportLab — it contains the product image as evidence, the seven extracted declarations, the violations with rule references, the compliance score, the AI analysis summary, and inspector details. On the Reports screen, admins can also generate an all-time system summary PDF and export data as CSV, which covers the 'editable format' requirement."

### Q9. What roles exist in your system?
> "Three roles: Admin, Inspector, and Viewer. Admins manage users, delete scans, view system health and audit logs, and create backups. Inspectors perform scans, view history, and can correct extracted fields (which triggers automatic re-evaluation). Viewers have read-only access. Role checks are enforced on the backend, not just hidden in the UI."

### Q10. What database do you use and why?
> "SQLite for development and small deployments — it's a single file, zero configuration, perfect for a hackathon and field trials. The code uses SQLAlchemy, so switching to PostgreSQL for large production deployments is a configuration change plus proper migrations — we documented that as our scaling path."

### Q11. How long did it take you to build this and who did what?
> "We built it as a team of six during the hackathon period. The team leader designed the architecture and the scan pipeline; one member built all the APIs, the database, and security; two members built the frontend screens; and two members handled documentation, testing, and demo preparation. Everyone's work is clearly mapped in our documentation."

---

## Part B — Tricky / Technical Questions

### Q12. Your OCR reads text, but font size is a legal requirement. How do you actually measure font size?
> "Honest answer: measuring absolute font size in millimetres from a photo requires calibration (known camera-to-label distance and DPI), which is hard in uncontrolled field photos. So we take a two-tier approach: our trained MobileNetV2 image classifier acts as a readability/print-quality proxy — it flags labels where the model predicts non-compliance, often due to small or poorly placed text. For production, our documented roadmap adds pixel-to-millimetre calibration using reference markers on the package to compute real font sizes. We deliberately did not fake a font-size number we couldn't measure."

### Q13. How do you prevent someone from bypassing your compliance check? (e.g., a label that looks compliant but isn't)
> "Three layers: (1) the OCR text is the ground truth of what's printed — if a declaration isn't there, it can't be extracted; (2) the ML classifier adds a vision-level check that catches print-quality issues text alone can't; (3) every result is stored with the original image, the raw OCR text, and the AI's extracted JSON, so an officer can open the image and verify. The report explicitly says it supports manual verification. No automated system can replace a human's final judgment — ours gives the officer the strongest possible starting point and complete evidence."

### Q14. Your cache returns saved results for ≥80% similar text. What if two DIFFERENT products have similar text? Won't you return the wrong result?
> "That's a sharp question. The similarity is computed on the full normalized OCR text — two different products' labels typically differ in brand names, MRP, quantities, addresses, etc., so their full-text similarity rarely crosses 80%. We also compare against the most recent 500 scans and use pre-filters (length ratio and token overlap) before the expensive comparison. That said, it's a heuristic, not a guarantee — which is why cache hits are clearly labeled 'From cache • NN% similar' in the UI and logged in the audit trail, so an inspector always knows the result came from cache. If needed, the threshold is tunable from 80% to 90%+."

### Q15. How is the compliance score calculated?
> "The rule engine starts at 100 and deducts 15 points per major violation and 6 per minor violation, never below zero. Status logic: no violations → Passed; any major violation → Failed; only minor violations → Pending Review. When the AI path is used, the AI model computes its own score and verdict, which is normalized and clamped to 0–100."

### Q16. Your ML classifier — what is it trained on, and what classes does it output?
> "It's a MobileNetV2-based binary classifier taking 224×224×3 images, outputting a softmax over two classes — by default 'Non-Compliant Label' and 'Compliant Label', configurable via environment variables because the class names depend on the original training data. It runs as an additional signal, and if it can't load, scans continue without it — a missing model never blocks an inspection."

### Q17. What happens if the internet is down during the demo — won't the whole thing fail?
> "No. The system has a fully offline path: Tesseract OCR + regex parser + rule engine. Everything except the optional OpenRouter AI call works without the internet. Even the demo product images are saved on the machine, so if the camera fails we use the Upload button. We deliberately engineered for field reality, where enforcement officers often work in areas with poor connectivity."

### Q18. How do you secure the system? What if someone steals a JWT token?
> "Passwords are hashed with bcrypt — never stored in plain text. Tokens are JWT (HS256) signed with a secret key from the environment, expiring after 7 days, and the frontend refreshes them every 12 hours. If a token is stolen, its expiry limits the damage; the audit log records all actions, so suspicious activity is visible; and admins can disable a user's account instantly, which also invalidates their access since the backend re-checks `is_active` on every request. In production we'd add HTTPS everywhere and optionally token revocation lists."

### Q19. What is your database schema? Walk me through the tables.
> "Four tables. `users` holds accounts with role and active status. `scans` holds one row per inspection — the seven extracted declarations, raw OCR text, confidence scores, AI metadata, compliance status and score. `violations` holds each problem found, linked to its scan, with code, severity, and rule reference. `audit_logs` records every action — who scanned what, cache hits, user creation, backups — which powers the activity feed and accountability."

### Q20. How does the system decide 'Pending Review' vs 'Failed'?
> "Failed means at least one major violation — a required declaration is missing or invalid. Pending Review means issues exist but they're all minor (like a missing consumer-care phone number), or the extraction is ambiguous. This maps to real enforcement: major violations are actionable offenses; minor ones need a second look."

### Q21. Why did you choose OpenRouter instead of calling a model directly?
> "OpenRouter gives us one API to many models — we can switch between GPT-4o-mini, Gemini Flash, or even free models through a single environment variable, without changing any code. That gives flexibility and cost control, which matters because the department will run thousands of scans. And critically, the output format stays fixed regardless of the model."

### Q22. How do you prevent duplicate scans and wasted AI calls?
> "Our dedupe service normalizes the OCR text and compares it against recent scans. If similarity is ≥80% (tunable), the saved result is returned directly from the database with `cached: true` — no AI call, no duplicate row. The admin dashboard even shows a 'cache hits saved' counter, and each cache hit is logged. For field use, inspectors scanning the same shelf of products benefit enormously."

### Q23. What's your compliance rate logic in the dashboard?
> "Compliance rate = passed scans / total scans × 100. The dashboard supports Daily, Weekly, Monthly, and All-time periods, and the admin panel shows a 14-day trend chart of inspections and violations, plus top violation types — so an enforcement head can see exactly what's failing in the market."

### Q24. Your system is a web app. How would an inspector use it in a shop with no laptop?
> "Two answers: first, the frontend is responsive and camera-enabled, so it works on a phone browser in the field. Second, our documented roadmap includes a mobile app and offline-first mode. Today the design already supports field reality — images can be uploaded later if connectivity is poor, and the backend can be deployed centrally while inspectors use thin clients."

### Q25. What testing did you do?
> "End-to-end manual testing of every screen: login, single and multi-side scans, filters, pagination, PDF downloads, admin user management, backups. We also tested the cache: scanning the same label twice returns the cached result with no second AI call. We tested the fallback by running without an API key. Automated unit tests for the OCR parser, dedupe, and AI services are on our roadmap — the hackathon timeline prioritized a fully working integrated system."

---

## Part C — Domain / Legal Questions

### Q26. Which sections of the rules does your system implement?
> "We codified the mandatory-declaration checks from Chapter II of the Legal Metrology (Packaged Commodities) Rules, 2011, primarily Rule 6(1): manufacturer/packer/importer details under 6(1)(a), net quantity under 6(1)(b)/Rule 8, consumer care under 6(1)(d), MRP under 6(1)(e), month and year of manufacture under 6(1)(f), plus Rule 5 for general declaration quality. Our Admin Panel lists all nine enforced rules with their rule references, and every violation stores its rule reference."

### Q27. What is MRP? Why does it matter?
> "MRP — Maximum Retail Price — is the maximum price inclusive of all taxes at which a product may be sold. It protects consumers from overcharging. Under the rules it must be printed as 'MRP Rs. … (incl. of all taxes)'. Our system checks both that an MRP exists and that it's a valid positive number — a 'MRP Rs. 0' or unparsable value is flagged."

### Q28. Does your system handle products exempted from declaring MRP or quantity?
> "Currently our rule set targets standard packaged commodities under the rules. Exemptions exist for certain categories — that's why every scan result is reviewed by an officer and the report explicitly supports human verification. Extending the rule configuration to handle exemption categories per commodity is part of our rule-management roadmap."

### Q29. Who is the end user of this system?
> "The primary users are Legal Metrology enforcement officers and inspectors of the Department of Consumer Affairs. Secondary users are the department administrators who manage inspectors and monitor compliance trends across the market. It's a government enforcement tool — not a consumer shopping app."

---

## Part D — Impact / Business Questions

### Q30. What is the real-world impact of your solution?
> "Manual label inspection takes minutes per product and can't scale. Our system does it in seconds, so an inspector can cover hundreds of products per day. It catches non-compliance consistently — no tired eyes, no missed declarations. It creates official evidence (PDFs + images) that can be attached to legal notices. And the dashboard gives enforcement leadership visibility into which violations are most common, enabling targeted market drives. The ultimate beneficiary is the consumer."

### Q31. How would you deploy this for a state government?
> "The backend is Dockerized — one image with Tesseract preinstalled. The frontend builds to static files hostable on any government infrastructure. We'd deploy the backend centrally, use PostgreSQL instead of SQLite for multi-instance reliability, put HTTPS in front, set CORS to the government domain, and give each district's inspectors their own accounts. We documented the full production checklist in our project documentation."

### Q32. What happens when a company changes its label design? Does your system adapt?
> "The compliance rules are stable — they come from the law, not from label designs. What changes is the text extraction, which is handled by generic OCR and AI that read whatever is printed. The ML classifier is the only trained component; it would need retraining if we wanted it to recognize a completely new label style — but the rule engine and pipeline keep working unchanged."

### Q33. Cost estimate — how much does each scan cost?
> "Without AI: zero — pure OCR and rules. With AI: the OpenRouter call costs fractions of a rupee per scan, and our cache eliminates most repeat scans. We also support free-tier models through OpenRouter, so the department can run the system at negligible per-scan cost. We designed cost control as a first-class feature."

### Q34. This problem mentions scanning product listings on e-commerce too. Do you cover that?
> "Our current system covers label images via upload and camera. E-commerce product listings are text-based, and our pipeline can accept any text source — the same parser and rule engine work on listing text. That's a documented extension: adding a text-paste or listing-URL input that reuses the exact compliance engine. The image pipeline is the harder part, and it's fully built."

---

## 🎯 Quick-Answer Cheat Sheet (30-second versions)

| Question | One-line answer |
|---|---|
| What did you build? | A web app that scans product label photos and automatically checks them against the Legal Metrology (Packaged Commodities) Rules 2011, giving Pass/Fail + PDF reports. |
| What's the tech stack? | React + Vite frontend, Python FastAPI backend, SQLAlchemy + SQLite database, Tesseract/PaddleOCR, OpenRouter AI, TensorFlow ML classifier, ReportLab PDFs, Docker. |
| What makes it special? | Multi-side scanning, offline fallback (works without AI/internet), smart cache that saves AI costs on repeat scans, and complete audit trail. |
| What's the accuracy? | High on clean labels; low-quality images are honestly flagged as 'Pending Review' — the report supports, not replaces, officer verification. |
| Who uses it? | Legal Metrology inspectors and enforcement admins under the Department of Consumer Affairs. |
| Why is it needed? | Manual label checking can't scale to crores of packaged products; non-compliant labels routinely reach the market. |

---

## ⚠️ Golden Rules When Answering Judges

1. **Answer the question asked** — don't dump your whole pitch again.
2. **If you don't know — say so honestly**, then connect to what you do know ("We haven't implemented X yet, but our architecture handles it because…").
3. **Team members answer their own areas** — it shows a real team effort.
4. **Never argue with a judge.** Acknowledge the point, then explain your design reasoning.
5. **Keep answers under 60 seconds** unless the judge clearly wants more.
6. **Turn limitations into roadmap items** — every honest limitation shows maturity.