# 🎤 Spokesperson Presentation Speech (Detailed Master Version)

**Speaker:** Ramdas Hembram (Team Leader)
**Occasion:** Smart India Hackathon — Problem Statement 26034
**Time:** 5–7 minutes (full version) — a trimmed 3-minute version is included at the end

---

## How to use this script

- **Bold text = what you say.** *(Italic text in brackets = stage direction for you or the demo operator.)*
- This version is written as a **first-person story**. Judges remember stories, not slide bullets. You are not reading a report — you are walking them through **how you thought**, from the first day to the demo you are showing them right now.
- Speak slowly. Pause after every major section. Do **not** rush the demo.
- If a judge interrupts, answer their question, then say: *"Coming back to my story…"* and continue from where you stopped.

---

# THE FULL SCRIPT

---

## Part 1 — Greeting & Introduction

> **"Good morning / good afternoon, respected judges.**
>
> **My name is Ramdas Hembram, and I am the Team Leader of our six-member team. Today I am going to tell you a story — the story of how we took a real problem faced by the Department of Consumer Affairs and turned it into a working software system.**
>
> **We are solving Problem Statement 26034 — a software system to check the compliance of packaged commodities under the Legal Metrology (Packaged Commodities) Rules, 2011, by scanning products, images, and labels.**
>
> **But before I show you what we built, I want you to understand the problem the way we understood it — because everything we built flows from that understanding."**

*(Pause. Make eye contact with each judge.)*

---

## Part 2 — The Problem, Explained In Depth

> **"Every packaged product sold in India — a biscuit packet, a cold drink bottle, a soap bar, a packet of milk, a medicine strip, a packet of chips — is governed by a law: the Legal Metrology Act, 2009, and the Legal Metrology (Packaged Commodities) Rules, 2011.**
>
> **Under these rules, every package must print certain mandatory declarations on its label —**
>
> **— the MRP, the Maximum Retail Price, inclusive of all taxes;**
> **— the net quantity in standard units;**
> **— the name and complete address of the manufacturer, packer, or importer;**
> **— the month and year of manufacture, packing, or import;**
> **— consumer care details — a phone number, an email;**
> **— and for imported goods, the country of origin.**
>
> **Why does the law demand this? Because these declarations are the only protection a consumer has. The MRP stops a shopkeeper from overcharging. The net quantity stops a company from shrinking the pack while keeping the price. The manufacturer's address makes someone accountable. The date tells you whether the product is fresh. Without these declarations, every one of us can be cheated — and the law exists precisely to prevent that."**

> **"Now here is the problem. These rules are not new — they have existed for years. So why does the Department of Consumer Affairs need a software solution? Let me tell you why the problem exists — because understanding the root cause is where every good solution starts."**

### Why the problem exists (root causes)

> **"First — the sheer scale. Think about a typical supermarket. It has thousands of products. A state has lakhs of retail outlets — kirana shops, supermarkets, e-commerce warehouses. Across India, there are crores of packaged products on shelves at any moment. No enforcement department can physically check even one percent of them."**
>
> **"Second — the current method is manual. An inspector goes to a shop, picks up a product, and checks every declaration with his own eyes — is the MRP printed? Is the quantity there? Is the date there? Is the font readable? One product takes minutes. A hundred products take hours. And after checking fifty products, human eyes get tired — and tired eyes miss things. Manual inspection is slow, inconsistent, and does not scale."**
>
> **"Third — non-compliance is common and profitable. Some manufacturers deliberately print tiny fonts, skip the MRP, hide the quantity, or print dates in ways that are hard to verify — because it saves them money or lets them cheat. Others simply don't know the rules. Either way, the market is full of non-compliant labels, and enforcement cannot keep up."**
>
> **"And fourth — there is no systematic record. When an inspector does find a violation, everything is paper-based. There is no central repository of what was checked, when, by whom, and what was found. No pattern analysis of which violations are most common. No dashboard for enforcement leadership. So even the inspections that DO happen don't produce intelligence."**

> **"So the problem, in one sentence: a massive market, checked manually, by tired eyes, with paper records. That is why the Department asked for a software system. And that is the problem we chose to solve."**

---

## Part 3 — The Ways I Saw the Solution (Alternatives I Considered, and Why I Chose Ours)

> **"Now, as a team leader, the first thing I did was not write code. I sat with my team and asked: what are the possible ways to solve this? We identified four paths — and I want to share with you why we rejected three of them, because I believe that reasoning is the heart of good engineering."**

### Option 1 — Do nothing / stay manual (status quo)
> **"The first option was the status quo — keep manual inspection, maybe give officers a printed checklist. Cost: zero rupees. But it solves nothing: still slow, still inconsistent, still no records, still no scale. We rejected it immediately — a hackathon exists to build, not to maintain the status quo."**

### Option 2 — A simple record-keeping app (database-only, manual data entry)
> **"The second option was a simple app where an inspector manually types the MRP, quantity, and manufacturer into a form, and the app checks the rules and stores the record.**
>
> **It would be easy to build — honestly, a two-day job. But think about it: the inspector still has to read the label himself and type everything. Typing is slower than reading. Human errors still happen. And the moment you type 'MRP 10' you have already done the inspection — the computer just does the arithmetic. It adds record-keeping but not intelligence. We rejected it because it automates the paperwork while leaving the hard part — reading the label — to humans."**

### Option 3 — A mobile-only native app with OCR but no AI
> **"The third option was a native mobile app — Android and iOS — that uses OCR to read the label text, extracts declarations with pattern matching, and checks rules. No AI, no internet dependency.**
>
> **This was a serious candidate. OCR-only is fast, works offline, and is cheaper. But when we dug deeper, we found its limits: pattern-matching alone struggles with the huge variety of real labels — different layouts, different fonts, different languages mixed in English and Hindi. It cannot write an inspection report. It gives you fields, but not understanding. And building and maintaining two native apps doubles our work — while enforcement officers may sit behind a desktop too. It solves reading, but not understanding, and it limits our reach."**

### Option 4 — Our chosen path: a full-stack web platform with OCR + AI + rules + ML + smart cache
> **"So we chose a fourth path — and I will tell you honestly why.**
>
> **We built a web platform — because a web app runs on a phone browser AND a desktop browser. No app store, no installation, no two codebases. One build, every device.**
>
> **We combined OCR with an AI model — because OCR reads text, but AI understands it. The AI structures messy raw text into clean fields, and even writes an inspection report an officer can read in seconds.**
>
> **We kept a rule-based compliance engine — because the law is a set of rules, and rules should be checked by code that is transparent, explainable, and works with zero internet.**
>
> **We added a machine-learning classifier — because the rules also care about font size and readability, and a trained vision model can flag labels that text-reading alone cannot judge.**
>
> **We added a smart cache — because this will be used at scale by a government department, and we refused to waste money calling paid AI on the same product twice.**
>
> **And we made every result produce evidence — the original image, the extracted fields, the violations, and a PDF report — because an enforcement tool without evidence is not an enforcement tool."**

*(Optional comparison slide: a small table showing the four options against: speed, accuracy, offline support, cost, evidence, platform reach. Point at it briefly.)*

> **"To put it simply: Option 1 keeps the problem. Option 2 automates paperwork but not inspection. Option 3 reads but doesn't understand. Our choice — Option 4 — reads, understands, checks, records, and reports, while staying offline-capable and cost-conscious. That is why we chose it."**

---

## Part 4 — How I Used My Team (Leadership Story)

> **"Now let me tell you how I used my team — because a team leader's real job is not writing the most code; it is placing the right person on the right task."**

> **"My team has six members. I started by mapping the work into difficulty levels — because I believe everyone should be challenged but no one should be crushed. I also asked one question about every member: what is this person strongest at, and what will this project teach them?"**

> **"The hardest part of this project is the brain — the scan pipeline where OCR, AI, and the compliance engine all come together, plus the overall architecture that decides how everything connects. That is the part where one wrong decision breaks everything. I gave that to myself. As the team leader, I took the hardest responsibility — not as a title, but as a duty. I designed the architecture and built the core scan pipeline and the compliance engine."**
>
> **"The second-hardest part is the foundation everything stands on — the backend APIs, the database design, and security. If the database is wrong, all six of us suffer. I gave that to Bidhi Dutta, our strongest backend developer, who built all the API endpoints, the four database tables, and the JWT authentication."**
>
> **"The medium-difficulty work is the frontend — building the screens. I split it so both members own a meaningful chunk: Partha Paul built the New Scan screen — the camera capture, uploads, and the results panel — plus the Dashboard. Sultan Ahamed built Scan History, Reports, and the Admin Panel — search, filters, charts, and user management."**
>
> **"And I gave the two remaining members roles that are easier technically but absolutely critical on demo day: Anirban Dhara owns documentation, the presentation slides, and collecting real product labels for testing. Shubhankar Barman owns testing, QA, deployment setup, and preparing today's live demo. Because judges, a perfect product with a broken demo is a failure — and a good demo with good docs is a win."**

> **"How did we coordinate? Three simple rules. First, the backend API was our contract — Bidhi published the exact request and response formats, and the frontend members built against that contract, so nobody waited on anybody. Second, a daily fifteen-minute sync — what I did, what I'll do, what's blocking me. Third, git discipline — small commits, never broken code on the main branch, and whoever broke the build fixed it before going home."**

> **"And one more thing: on demo day, my job is to speak, Shubhankar's job is to run the machine, Anirban keeps the slides in sync, and everyone answers questions in their own area. A judge asking our frontend member about the camera screen should see the person who actually built it light up — because he did build it."**

---

## Part 5 — My Journey, First Step to Last Step (How I Built It)

> **"Now let me walk you through how we actually built this — my journey from the first day to today. I will take you through every step, because I want you to see that nothing here is magic."**

### Step 1 — Understanding the law (Day 1)
> **"Before a single line of code, I studied the rules themselves. I read the Legal Metrology Act, 2009, and the Packaged Commodities Rules, 2011 — especially Rule 6, which lists the mandatory declarations. I wrote down the seven declarations we had to check, the rule references for each, and the penalty logic. This document became our rule set — and it still lives in our code today, in the compliance engine."**

### Step 2 — Designing the architecture (Day 1–2)
> **"Next, the architecture. I drew a diagram on paper: a React frontend talking to a FastAPI backend over JSON with JWT authentication; the backend running a pipeline of OCR → cache → AI → rules; a SQLite database storing scans, violations, users, and audit logs; and PDF reports generated server-side. Two decisions here shaped everything: first, keep the frontend and backend as two separate deployable applications — because the problem statement asks for independent deployment; second, design the pipeline so every stage can fail gracefully — if AI fails, the rules still run."**

### Step 3 — Building the data foundation (Day 2–3)
> **"Bidhi designed the database: four tables — users, scans, violations, and audit_logs. The scans table holds every extracted declaration, the raw OCR text, the confidence, the AI metadata, the compliance status and score. Violations link to scans with a code, severity, and rule reference. Audit logs record every action for accountability. We also built a small auto-migration so that when we added new columns later, existing databases were upgraded automatically — no manual SQL."**

### Step 4 — Building the API (Day 3–5)
> **"With the database in place, we built the API endpoints: authentication — register, login, refresh, logout; scans — create, list with filters, view, correct, delete, download report; dashboard statistics; and the admin endpoints — user management, system health, audit logs, backups. Every protected endpoint checks the JWT token, and admin-only endpoints enforce the role server-side."**

### Step 5 — Teaching the computer to read (Day 5–6)
> **"Now the interesting part — making the computer read a label. We integrated two OCR engines: PaddleOCR for quality, Tesseract for lightness, with an auto mode that prefers Paddle and falls back to Tesseract. We added image preparation — downscaling huge camera photos, grayscale, auto-contrast — and for Tesseract we merge three page-segmentation modes so both dense and scattered text get captured. Then I wrote the declaration parser: regex patterns that hunt for MRP, net quantity, manufacturer, dates, consumer care numbers, and country of origin — with a confidence score based on how many declarations were found."**

### Step 6 — Writing the law into code (Day 6–7)
> **"Then the compliance engine — the part I am proudest of. I wrote the nine rules as code: missing manufacturer, missing net quantity, missing MRP, missing date, missing consumer care, invalid MRP format, invalid MRP value, non-standard units, and the AI-flagged label check. Each rule carries its severity and its rule reference — Rule 6(1)(a), 6(1)(e), Rule 8, and so on. The score starts at 100 and deducts 15 for a major violation and 6 for a minor. No violations — Passed. Any major — Failed. Only minors — Pending Review. Transparent, explainable, defensible."**

### Step 7 — Adding AI understanding (Day 7–8)
> **"Next, understanding. I connected the raw OCR text to an AI model through OpenRouter — a single API that gives us access to many models, so we can switch models without touching code. The AI is told, through a carefully written system prompt, to return one fixed JSON shape — always the same keys: the seven declarations, the status, the compliance score, the violations, the confidence, and a written inspection report. Fixed shape is critical — the database and the UI can rely on it no matter what label was scanned. If the AI fails, the system catches the error and falls back to Step 5 and 6 automatically."**

### Step 8 — Adding the vision check (Day 8–9)
> **"The rules care about font size and readability — text alone can't judge that. So we added a trained machine-learning classifier — a MobileNetV2 model that looks at the label image itself and predicts compliant or non-compliant. If it flags the label, the compliance engine adds a major violation under Rule 5 — general provisions regarding declarations. The model loads once in the background at startup, so the first scan isn't slow, and if the model is missing, scans continue without it."**

### Step 9 — The money-saving cache (Day 9)
> **"Then a practical problem: the AI call costs money, and inspectors scan the same products again and again. So I built a dedupe service — before calling the AI, the new OCR text is compared with recent scans. If it's at least 80% similar, we return the saved result from the database — no AI call, no duplicate row — and the UI shows a purple 'From cache' chip with the similarity percentage. At scale, this alone saves most of the AI cost."**

### Step 10 — The evidence: PDF reports (Day 10)
> **"An enforcement tool needs evidence. We built PDF generation with ReportLab — each report contains the product image as proof, all seven extracted declarations, the violations with rule references, the compliance score, the AI analysis, the inspector's name, and an official disclaimer. One click, downloadable, ready to attach to an inspection file. On the Reports screen we also added CSV export and an all-time system summary PDF."**

### Step 11 — The face of the product (Day 10–12)
> **"While the backend was being built, the frontend team was building the face of the product — and here I want to highlight two features we designed together. First, the New Scan screen opens the camera automatically and supports multi-side scanning — because in reality, declarations are spread across a package, and a real inspector examines the whole package. Second, the Scan History and Reports screens pull real data from the APIs — live statistics, donut charts, violation analysis, filters, pagination — everything backed by the database, nothing hardcoded."**

### Step 12 — Putting it all together (Day 12–13)
> **"Then integration day — the day all six members' work met. We connected frontend to backend, tested the full flow end to end: login, scan, result, history, report. We found and fixed the classic integration bugs — CORS settings, date formats, field names. This is also where the cache feature proved itself: scanning the same label twice returned the saved result instantly."**

### Step 13 — Testing and hardening (Day 13)
> **"Shubhankar then tested everything like an enemy of the product: wrong passwords, empty scans, blurry images, disabled accounts, deleting users, backups. We tested the offline path by running with no AI key — the rule engine took over and the scan still completed. We tested the classifier-unavailable path. Every test result went back to the owner of that module, and every bug was fixed before we called the project done."**

### Step 14 — Preparing for today (Day 14)
> **"And finally — today. Anirban prepared the documentation and slides, Shubhankar prepared the demo environment and backup product images, and we rehearsed this presentation until it was smooth. Because a hackathon submission is not what you build in your room — it's what you show, and what you prove."**

---

## Part 6 — 🎥 THE LIVE DEMO

> **"And now — with your permission — let me show you the result of that journey. This is not a slide; this is the working system."**

*(Signal Shubhankar. Take ONE prepared product — preferably one with a visible violation.)*

> **"I am logged in as an inspector. I click New Scan — the camera opens. I capture the front of this package, and the back. Now I press SCAN.**
>
> **Watch what happens inside: the image is saved, OCR reads the text, the cache check runs, the classifier looks at the label, the AI structures the fields, the compliance engine applies the rules — and here is the result.**
>
> **All seven declarations, extracted and displayed. The compliance score. The status. The violations, each with its rule reference — you can see exactly which rule this product violates. And here is the AI inspection report, written in plain language for an officer.**
>
> **Now watch this — I scan the same label again. See the purple chip: 'From cache — 95% similar.' The system recognized the same product and returned the saved result — no wasted AI call.**
>
> **And finally, one click — the official PDF report. *(Show it to the judges.)* Product image, declarations, violations, rule references, inspector details. Evidence, ready for an inspection file."**

*(If the camera fails: "No problem — our system also accepts uploads. This is exactly why we built both paths." Use a saved image.)*

---

## Part 7 — Key Features Recap

> **"In summary, everything the problem statement asked for is here:**
>
> **— Image upload and product scanning, single and multi-side;**
> **— Automatic extraction and validation of mandatory declarations;**
> **— Font and readability analysis through a trained ML classifier;**
> **— Detection of missing, misleading, and non-standard declarations;**
> **— PDF and CSV report generation;**
> **— A searchable repository of scanned products with full inspection history;**
> **— Dashboards for enforcement officials — live statistics, trends, audit logs;**
> **— Role-based access with secure JWT authentication."**

---

## Part 8 — Impact & Closing

> **"And what is the impact? Let me give you three numbers and one promise.**
>
> **Speed: a label that took minutes to check by hand now takes seconds. Scale: one inspector can cover hundreds of products in a day. Intelligence: for the first time, a department can see which violations are most common across the whole market — and target enforcement where it matters.**
>
> **The promise: every result is honest. If the system is not confident, it says Pending Review. If the AI is offline, the rules still work. The report says it supports, not replaces, an officer's judgment. We did not build a system that pretends to be perfect — we built a system that is trustworthy.**
>
> **Respected judges, this problem touches every citizen of this country — because all of us buy packaged goods. We are proud to have turned a legal rulebook into a practical tool for enforcement.**
>
> **My team of six stands behind this work — and we will be happy to answer any questions you have. Thank you."**

*(Bow/namaste. Step back. Let teammates introduce themselves — one line each. Then invite questions.)*

---

## 🧑‍🤝‍🧑 Team Introduction Lines (one sentence each)

- **Bidhi Dutta:** *"I built the backend APIs and the database — every record you saw in the demo lives in the system I designed, and every request is secured with JWT authentication."*
- **Partha Paul:** *"I built the New Scan screen and the Dashboard — the camera capture, multi-side scanning, and the results panel you just saw."*
- **Sultan Ahamed:** *"I built the Scan History, Reports, and Admin Panel — search, filters, the charts, and user management."*
- **Anirban Dhara:** *"I wrote the documentation, prepared the slides, and collected the real product labels we used for testing and today's demo."*
- **Shubhankar Barman:** *"I did the testing and QA, prepared today's demo environment, and made sure everything runs smoothly on stage."*

---

## 🎬 Trimmed 3-Minute Version (if the judges give less time)

> **"Good morning. I am Ramdas Hembram, Team Leader, solving Problem Statement 26034 — checking packaged commodities against the Legal Metrology Rules 2011 by scanning labels.**
>
> **The problem: crores of packaged products, checked manually by inspectors with paper records — slow, inconsistent, and impossible to scale. Non-compliant labels — missing MRP, wrong quantity, unreadable fonts — keep reaching the market.**
>
> **We considered four approaches: staying manual — rejected, solves nothing; a data-entry app — rejected, automates paperwork but not inspection; OCR-only mobile apps — rejected, reads text but can't understand it; and what we built: a full-stack web platform where OCR reads the label, AI structures and understands it, a rule engine checks it against the law, and the system produces evidence and PDF reports — with an offline fallback and a smart cache that saves AI costs on repeat scans.**
>
> **How I used my team: I took the hardest part myself — the architecture and the core scan pipeline. Bidhi built the APIs, database, and security. Partha and Sultan built the frontend screens. Anirban handled documentation and slides, and Shubhankar handled testing and this demo. The API was our contract; daily syncs kept us moving.**
>
> **How I built it, step by step: I studied the law first, then designed the architecture, then the database, then the APIs, then OCR, then the compliance rules, then AI, then the ML classifier, then the cache, then PDF reports, then the frontend, then integration, testing, and finally today's demo.**
>
> **Let me show you — *(demo)* — camera opens, capture two sides, scan, and here are the seven declarations, the compliance score, the violations with rule references, the AI report — and scanning again gives us the cached result. One click — the PDF report.**
>
> **The impact: seconds instead of minutes, hundreds of products a day, and dashboards that show enforcement leadership exactly where violations are happening.**
>
> **Thank you — we're happy to take your questions."**

---

## ⚠️ Delivery Tips

1. **Know your 6 beats:** Problem → Why it exists → Alternatives & choice → Team usage → Step-by-step journey → Demo & impact.
2. **The alternatives section is your differentiator** — judges love seeing rejected options and honest reasoning. Do not skip it even in the trimmed version.
3. **Never touch the laptop during the demo** — you speak, Shubhankar clicks.
4. **If something fails on stage:** stay calm, say *"this is exactly why we built an offline fallback"* — turn a bug into a feature.
5. **Answer questions honestly** — if you don't know, say so and connect to what you do know. Never bluff.
6. **Keep the team visible** — after your pitch, let each member say their one line. A coordinated team is a winning team.