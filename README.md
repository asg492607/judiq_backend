# 🏛️ JudiQ AI — Institutional Litigation Intelligence Platform

[![Build Status](https://img.shields.io/badge/Tests-3%2C362%20Passing-brightgreen.svg)](file:///backend/tests)
[![Accuracy](https://img.shields.io/badge/Benchmark%20Accuracy-100%25-blue.svg)](file:///backend/tests/test_real_world_criminal_cases.py)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Enterprise%20Proprietary-gold.svg)]()

> **JudiQ AI** is a deterministic legal intelligence platform purpose-built for the Indian Judiciary and legal practitioners. It automates fatal defect analysis, limitation audits, courtroom probability scoring, verified precedent matching, and legal document drafting across four major litigation verticals.

---

## 📑 Core Litigation Verticals

| Domain | Statutory Framework | Key Capabilities |
| :--- | :--- | :--- |
| **Cheque Bounce** | Negotiable Instruments Act (S.138, 141, 142) | 3-month cheque presentation check, S.138(b) 30-day notice, 15-day cure window, S.142 limitation condonation, S.141 director vicarious liability audit. |
| **SARFAESI & DRT** | SARFAESI Act 2002 & RDDBFI Act 1993 | Creditor & Borrower dual engines, S.13(2) demand, S.13(3A) mandatory 15-day objection reply, S.26D CERSAI bar, S.31(i) agricultural exemption, Rule 8/9 auction compliance. |
| **Criminal Defense** | IPC 1860 / CrPC 1973 ↔ BNS 2023 / BNSS 2023 | Dual-statute mapping, Satender Kumar Antil (2022) Categories A–D, Arnesh Kumar (S.41A/35) notice, S.167(2) default bail, Bhajan Lal (1992) quashing matrix. |
| **Commercial Suits** | CPC 1908 & Commercial Courts Act 2015 | Order 39 interim injunctions, S.12A mandatory pre-institution mediation, Limitation Act Articles 54/55/113, specific performance readiness audits. |

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://bitbucket.org/judiqai/judiq.git
cd judiq-ai

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Start Local Unified Server
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Access the Application
- **Frontend Web App:** [http://localhost:8000/](http://localhost:8000/) *(or [http://127.0.0.1:8000/](http://127.0.0.1:8000/))*
- **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Automated Testing & Empirical Benchmarks

The repository includes a comprehensive 3,300+ test suite covering real-world Supreme Court and High Court cases:

```bash
# Run entire test benchmark
python -m pytest backend/tests

# Run specific domain benchmarks
python -m pytest backend/tests/test_real_world_criminal_cases.py -v
python -m pytest backend/tests/test_cheque_bounce_hard_cases.py -v
python -m pytest backend/tests/test_sarfaesi_ultra_hard_cases.py -v
```

**Result:** `3362 passed in 3.88s (100% pass rate, 0 failures)`.

---

## 🏛️ Comprehensive Architecture & Engineering Guide

For an in-depth, file-by-file breakdown of the backend engines, data flow sequences, frontend SPA modules, token systems, and junior developer onboarding guides, please refer to:

👉 [**ARCHITECTURE.md**](file:///c:/Users/Atharva/OneDrive/Desktop/judiq-ai/ARCHITECTURE.md)

---

## 📁 Repository Structure

```
judiq-ai/
├── backend/               # FastAPI Backend Engines & Precedent Registries
│   ├── core/              # BaseDomainEngine ABC & Case Registry
│   ├── criminal/          # Criminal defense, dual-statute & bail engines
│   ├── sarfaesi/          # Creditor/Borrower SARFAESI & DRT engines
│   ├── tests/             # 3,362 automated benchmark test cases
│   ├── main.py            # FastAPI entry point & unified static file mount
│   ├── documents.py       # PDF & Word court document endpoints
│   └── session.py         # Database manager & analytics store
│
├── frontend/              # Institutional Legal-Tech Frontend SPA
│   ├── js/                # Main controller & client modules (charts, simulator, dock)
│   ├── api.js             # Fetch client with auto JWT injection
│   ├── config.js          # Multi-domain wizard definitions & role mappings
│   ├── draft_templates.js # Legal draft templates (Bail, Quashing, Notices)
│   ├── renderer.js        # SVG score gauge & strategy results renderer
│   ├── styles.css         # Obsidian dark theme, tokens & glassmorphism
│   ├── wizard.js          # Dynamic intake wizard state machine
│   └── index.html         # Master application shell
│
├── ARCHITECTURE.md        # Complete technical and architectural manual
└── README.md              # Platform overview & quick start
```
