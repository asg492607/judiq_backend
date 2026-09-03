# JudiQ AI: Frontend

![JudiQ Hero Banner](./multimedia/judiq_hero_banner_1778733069009.png)

![Status](https://img.shields.io/badge/Status-Institutional_Beta-gold?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Tech-Vanilla_JS_ES6-blue?style=for-the-badge)
![Modules](https://img.shields.io/badge/Features-NI%20Act%20%7C%20SARFAESI%20Wizard-brightgreen?style=for-the-badge)

The **JudiQ AI Frontend** is a lightweight, high-performance web interface designed for Indian legal practitioners to strategize, analyze, and draft litigation. It leverages a modern Vanilla JS ES6 modular architecture, delivering a premium glassmorphic aesthetic without the bundle overhead of heavy single-page application frameworks.

---

## 🏛️ UI/UX Architecture

The frontend is framework-agnostic to maximize rendering performance and ensure sub-second UI interactions across legacy hardware:

- **ES6 Modular Structure:** Native `import/export` organization initialized through `js/main.js`.
- **Dynamic Legal Wizards (`wizard.js`):** Multi-step guidance forms tailored for both **Section 138 NI Act** and **SARFAESI Act 2002** (Bank vs. Borrower perspectives).
- **Comprehensive Renderer (`renderer.js`):** Dynamically updates defect heatmaps, statutory timeline charts, adversarial threat meters, and AI draft previews.
- **Demo Datasets (`demo_cases/`):** Pre-configured one-click cases (`demo_sarfaesi_bank.json` & `demo_sarfaesi_borrower.json`) for instant evaluation.
- **Glassmorphism 2.0:** Dynamic dark/light mode, deep backdrop blurs, high-contrast typography, and crisp courtroom-grade card layouts.

---

## 🚀 Setup & Local Execution

Because ES6 modules use native HTTP CORS protocol, `index.html` cannot be opened via `file://`. It must be served over a local HTTP server.

**Prerequisites:** Python (or any local static file server)

### Windows PowerShell:
```powershell
# From the frontend directory
python -m http.server 8080
```
*(Or execute `.\start.ps1` if available)*

Access the frontend application at `http://localhost:8080`.

---

## 🎨 Core Feature Highlights

### 1. Interactive SARFAESI & NI Act Wizard
Step-by-step case ingestion supporting NPA dates, Section 13(2) demand notices, 13(4) possession notices, DM/CMM orders, and Section 17 DRT challenge grounds.

### 2. Courtroom Strategy & Threat Meter
Real-time scoring visualizer displaying procedural defects, limitation status, and simulated opposing counsel arguments using `Chart.js` via a leak-safe `ChartRegistry`.

![Courtroom Strategy](./multimedia/judiq_courtroom_strategy.png)

---

## 📁 Directory Structure
- `index.html`: Main layout and structural container.
- `styles.css`: CSS styling containing dynamic design tokens, theme variables, and glassmorphic utilities.
- `config.js`: API environment configuration and endpoint registry.
- `wizard.js`: Interactive multi-step wizard controller.
- `renderer.js`: Dynamic DOM renderer for analysis reports and pleadings.
- `ui.js`: Interactivity handlers, DOM sanitization (DOMPurify), and modal managers.
- `js/main.js`: Application coordinator and entry script.
- `demo_cases/`:
  - `demo_sarfaesi_bank.json`: Sample bank/lender enforcement case.
  - `demo_sarfaesi_borrower.json`: Sample borrower DRT challenge case.

---

© 2026 JudiQ AI. Built for the Institutional Courtroom.
