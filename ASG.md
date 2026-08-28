# JUDIQ AI — Enterprise Litigation & Institutional Banking Intelligence Platform
## Complete Master Architecture, Engineering, Statutory Rules & Operational Specification
**Document ID:** `ASG-MASTER-SPEC-2026`  
**Version:** `12.5.0-ENTERPRISE`  
**Last Updated:** August 2026  
**Classification:** Proprietary / Institutional Specification  

---

# Table of Contents
1. [Executive Summary & Product Vision](#1-executive-summary--product-vision)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Comprehensive Data Flow & Lifecycle](#3-comprehensive-data-flow--lifecycle)
4. [Statutory Engine Deep-Dives](#4-statutory-engine-deep-dives)
   - [4.1 Section 138 Negotiable Instruments Act (Cheque Bounce Engine)](#41-section-138-negotiable-instruments-act-cheque-bounce-engine)
   - [4.2 SARFAESI Act 2002 (Secured Debt Recovery Engine)](#42-sarfaesi-act-2002-secured-debt-recovery-engine)
   - [4.3 Criminal Litigation Engine (CrPC / BNSS 2023 & IPC / BNS 2023)](#43-criminal-litigation-engine-crpc--bnss-2023--ipc--bns-2023)
   - [4.4 Civil Litigation Engine (CPC 1908 & Commercial Courts Act 2015)](#44-civil-litigation-engine-cpc-1908--commercial-courts-act-2015)
   - [4.5 Institutional Banking & Stressed Asset Recovery OS](#45-institutional-banking--stressed-asset-recovery-os)
5. [Adversarial Simulation & Scoring Mechanics](#5-adversarial-simulation--scoring-mechanics)
6. [Caseroom, Forensic OCR & Evidence Certification (S.65B / BSA S.63)](#6-caseroom-forensic-ocr--evidence-certification-s65b--bsa-s63)
7. [Automated Legal Pleadings & Drafting Engine](#7-automated-legal-pleadings--drafting-engine)
8. [Frontend Architecture & UI/UX Design System](#8-frontend-architecture--uiux-design-system)
9. [Master Admin, Governance & Telemetry Control Center](#9-master-admin-governance--telemetry-control-center)
10. [Security, Encryption & DPDP Act Compliance](#10-security-encryption--dpdp-act-compliance)
11. [Complete REST API Reference & Schema Catalog](#11-complete-rest-api-reference--schema-catalog)
12. [Deployment, Localhost Operations & Troubleshooting Runbook](#12-deployment-localhost-operations--troubleshooting-runbook)

---

# 1. Executive Summary & Product Vision

### 1.1 The Legal Reality
In the Indian judicial landscape, over **40 lakh Section 138 NI Act (Cheque Bounce) cases** and hundreds of thousands of **SARFAESI, DRT, and commercial civil matters** clog the court system. A staggering **68% of commercial claims suffer delay or dismissal** not because of the underlying financial debt, but due to **fatal procedural, statutory, or evidentiary defects** committed before the initial plaint is ever filed:
- Sending a statutory notice on Day 31 instead of within the mandatory 30-day window (*Section 138(b)*).
- Filing a complaint on Day 12 before the mandatory 15-day borrower cure window expires (*Yogendra Pratap Singh v. Savitri Pandey trap*).
- Failing to aver specific day-to-day managerial control against company directors (*S.M.S. Pharmaceuticals Ltd. v. Neeta Bhalla standard*).
- Suing directors without arraigning the corporate entity as Accused No. 1 (*Aneeta Hada v. Godfather Travels fatal bar*).
- Attempting SARFAESI Section 13(2) enforcement without prior CERSAI registration (*Section 26D bar*) or over agricultural land (*Section 31(i) bar*).
- Submitting digital bank account statements without the mandatory Section 65B Indian Evidence Act / Section 63 Bharatiya Sakshya Adhiniyam (BSA) certification (*Arjun Panditrao Khotkar standard*).

### 1.2 The JudiQ Solution
**JudiQ AI** is an institutional-grade **Litigation Operating System (OS)** and **Stressed Asset Recovery Intelligence Platform**. It bridges the gap between raw document ingestion, strict statutory procedural adherence, adversarial courtroom simulation, and court-admissible legal drafting.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             JUDIQ AI PLATFORM                               │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│  LITIGATION STRATEGY │  BANKING RECOVERY OS │     EVIDENTIARY AUDIT VAULT   │
│  - Adversarial Sim   │  - 5-Track Strategy  │  - Forensic Tamper OCR        │
│  - Defect Classifier │  - OTS vs Lit NPV    │  - S.65B / BSA S.63 Evidence  │
│  - Survivability Map │  - Advocate SLA Hub  │  - Contradiction Detector     │
│  - Strategy Roadmap  │  - Statutory Drafter │  - Cryptographic Hash Ledger  │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
```

### 1.3 Key Architectural Principles
1. **Deterministic Rule Engines Over Probabilistic Models:** Statutory deadlines (limitation periods, notice windows, statutory bars) are computed using 100% deterministic mathematical rule engines. AI is never permitted to "hallucinate" limitation dates.
2. **Adversarial Opponent Modeling:** The system evaluates every case through the hostile lens of opposing counsel, pre-emptively exposing legal weaknesses, contradictory averments, and cross-examination traps.
3. **Single-Port Unified Architecture:** Seamlessly bundles high-performance FastAPI backends and modern ES6 Glassmorphism frontends on a single localhost/production port with zero-configuration reverse proxies.
4. **Zero-Training Confidentiality:** Strict DPDP Act 2023 compliance ensures client legal files are encrypted with AES-256 and never used to train public models.

---

# 2. End-to-End System Architecture

```
                                  USER INTERFACE LAYER
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │  HTML5 + Vanilla ES6 Modules + Glassmorphism 2.0 Design System + Chart.js        │
  │  - Case Intake Wizard (8-Step Dynamic Form with Rule-Based Field Validation)     │
  │  - Caseroom Real-Time Evidence Audit Dock                                        │
  │  - Adversarial Simulation & Survivability Graph Workspace                        │
  │  - Institutional Banking Recovery Suite (5-Tab Executive OS)                     │
  │  - Master Admin Control Center (3-Tab Governance, User Quotas, Bank Audits)      │
  └────────────────────────────────────────┬─────────────────────────────────────────┘
                                           │ HTTP / WebSocket (Port 8000)
                                           ▼
                                APPLICATION SERVER LAYER
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │  FastAPI (Python 3.10+) + Uvicorn ASGI Server                                    │
  │  - StaticFiles Mount: Serves frontend directory directly at /                    │
  │  - Middleware: CORS Allowlist, Process Timing, Prometheus Telemetry Scraping     │
  │  - Security: Rate Limiting (SlowAPI), JWT RBAC (Admin, Bank Officer, Advocate)   │
  └────────────────────────────────────────┬─────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                                                   ▼
  DETERMINISTIC STATUTORY ENGINES                             PROBABILISTIC AI & SYNTHESIS
┌───────────────────────────────────────────────┐           ┌────────────────────────────┐
│ 1. NI Act Timeline & S.141/142/143A Rules     │           │ 1. LLM Strategy Synthesizer│
│ 2. SARFAESI Chapter III & CERSAI/Agri Rules   │           │ 2. Opponent Cross-Exam Sim │
│ 3. Criminal CrPC/BNSS & Bail/Quash Rules      │           │ 3. Judge Behavior Profiler │
│ 4. Civil CPC O.37 & Commercial Mediation Rules│           │ 4. Dynamic Pleadings Gen   │
│ 5. OTS NPV Financial Decay & RBI Capital Model│           │ 5. Precedent Semantic RAG  │
└──────────────────────┬────────────────────────┘           └──────────────┬─────────────┘
                       │                                                   │
                       └───────────────────────┬───────────────────────────┘
                                               ▼
                                      DATA & STORAGE LAYER
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │  1. SQLite Relational Database (analytics.db) — Officer accounts, quotas, audits │
  │  2. AES-256 Cryptographic Vault — Client evidence & confidential case payloads   │
  │  3. Precedents Corpus (JSON Knowledge Base) — Supreme Court & High Court rulings │
  │  4. In-Memory Session & Cache Registry (engine_core.py)                          │
  └──────────────────────────────────────────────────────────────────────────────────┘
```

---

# 3. Comprehensive Data Flow & Lifecycle

```
[1. User / Officer Ingestion]
        │
        ├─► Option A: Case Intake Wizard (Parties, Dates, Cheque/Loan Data, Collateral)
        ├─► Option B: Caseroom Evidence Upload (Cheque, Memo, Notice, Postal Slip, 65B)
        └─► Option C: Institutional Bank Portfolio (Tier 1 to 5 Pre-configured Portfolios)
        │
[2. Normalization & Sanitization]
        │
        ├─► Normalizer Engine: Flattens hierarchical / wizard payloads into unified schemas
        ├─► Type Coercion: Standardizes ISO dates (YYYY-MM-DD), floating amounts, boolean flags
        └─► Pydantic V2 Validation: Enforces mandatory fields and blocks malformed data
        │
[3. Deterministic Statutory Audit]
        │
        ├─► Timeline Engine: Evaluates Presentation (3m), Notice (30d), Cure (15d), Filing (30d)
        ├─► Defect Classifier: Categorizes issues into FATAL, CURABLE, or STRATEGIC
        ├─► Rule Registry Cross-Check: Matches facts against 100+ statutory precedents
        └─► Readiness Scoring Engine: Computes 0-100 Viability Score using penalty deductions
        │
[4. Adversarial Simulation & Vulnerability Scan]
        │
        ├─► Opponent Persona Engine: Generates likely defence objections and counter-claims
        ├─► Cross-Examination Vector Simulator: Previews 4-phase interrogation vectors
        ├─► Contradiction Detector: Uncovers factual clashes across documents & statements
        └─► Courtroom Survivability Graphing: Simulates survival odds across judicial tiers
        │
[5. Strategy Formulation & Legal Economics]
        │
        ├─► Courtroom Strategy Engine: Proposes procedural motions (S.143A, NBW, Attachments)
        ├─► Economic Recovery Modeler: Compares immediate settlement NPV vs multi-year trial
        ├─► Multi-Track Orchestrator: Evaluates S.138, SARFAESI, DRT, IBC, RBI Defaulter tracks
        └─► OTS vs Litigation Calculator: Computes time decay, legal fees, RBI write-backs
        │
[6. Output Generation & Digital Execution]
        │
        ├─► Dynamic Pleadings Drafter: Generates court-admissible notices, complaints, petitions
        ├─► S.65B / BSA S.63 Evidence Certificate: Computes SHA-256 hashes and signs certificate
        ├─► Empaneled Advocate Dispatch: Assigns brief to advocate with 48h SLA tracking
        ├─► Compliance Ledger Export: Generates downloadable cryptographic JSON audit trail
        └─► Document Export Engine: Produces formatted PDF and Word (.docx) case dossiers
```

---

# 4. Statutory Engine Deep-Dives

---

## 4.1 Section 138 Negotiable Instruments Act (Cheque Bounce Engine)

The Section 138 Engine is the bedrock of JudiQ's commercial dispute analysis. It models every statutory milestone defined under the **Negotiable Instruments Act, 1881** (amended up to 2018).

### Statutory Rules & Limitation Windows
```
Cheque Issue Date
       │
       ▼ (Max 3 Months / Validity Period — RBI Master Circular)
Bank Return Memo (Dishonour Date)
       │
       ▼ (Mandatory: Within 30 Calendar Days u/s 138(b))
Demand Notice Dispatch Date
       │
       ▼ (Proof of Service / Deemed Service u/s 27 General Clauses Act)
Notice Receipt / Delivery Date
       │
       ▼ (Mandatory: 15 Calendar Days Borrower Cure Window u/s 138(c))
Cause of Action Accrual Date (Day 16)
       │
       ▼ (Mandatory: Within 30 Calendar Days u/s 142(1)(b))
Complaint Filing Deadline in Court of Metropolitan / Judicial Magistrate
```

### Statutory Defect Classification Matrix
| Defect Type | Severity | Statutory Provision | Authoritative Precedent | Remedy / Legal Effect |
|---|---|---|---|---|
| **Stale Cheque Presentation** | `FATAL` | RBI DBOD Circular 2011 / S.138 | *Shri Ishar Alloy Steels Ltd. v. Jayaswals Neco Ltd.* (2001) | Claim barred u/s 138. Civil suit / Order 37 only remedy. |
| **Notice Delayed (> 30 Days)** | `FATAL` | Section 138(b) NI Act | *Kamlesh Kumar v. State of Bihar* (2014) | Fatal defect. Criminal complaint cannot be instituted. |
| **Premature Complaint Filing** | `FATAL` | Section 138(c) NI Act | *Yogendra Pratap Singh v. Savitri Pandey* (2014) 10 SCC 709 | Complaint filed before Day 16 is non-est. Must file fresh complaint with S.142(1)(b) condonation. |
| **Time-Barred Complaint (> 30 Days)** | `CURABLE` | Section 142(1)(b) NI Act | *Birendra Prasad Sah v. State of Bihar* (2019) | File formal S.142(1)(b) Condonation Application with Sufficient Cause Affidavit. |
| **Missing Company Arraignment** | `FATAL` | Section 141 NI Act | *Aneeta Hada v. Godfather Travels & Tours* (2012) 5 SCC 661 | Fatal defect if company not named as Accused No. 1. Directors cannot be sued alone. |
| **Omnibus Director Averments** | `HIGH RISK` | Section 141 NI Act | *S.M.S. Pharmaceuticals Ltd. v. Neeta Bhalla* (2005) 8 SCC 89 | High quashing risk u/s 482 unless specific day-to-day control averred in complaint. |
| **Interim Relief Opportunity** | `OPPORTUNITY` | Section 143A NI Act | *Noor Mohammed v. Khurram Pasha* (2022) | Court empowered to order 20% interim compensation deposit upon plea recording. |
| **Appellate Pre-Deposit** | `MANDATORY` | Section 148 NI Act | *Surinder Singh Deswal v. Virender Gandhi* (2019) 11 SCC 341 | Appellate Court must direct minimum 20% fine deposit during appeal admission. |

---

## 4.2 SARFAESI Act 2002 (Secured Debt Recovery Engine)

The SARFAESI Engine governs extra-judicial enforcement of security interests by Banks and Financial Institutions under the **Securitisation and Reconstruction of Financial Assets and Enforcement of Security Interest Act, 2002**.

```
                           SARFAESI ENFORCEMENT WORKFLOW
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. NPA Classification (90 Days Overdue as per RBI Guidelines)          │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 2. Section 13(2) Statutory Demand Notice (60-Day Cure Period)          │
  │    - Details exact outstanding principal, penal interest & collateral  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 3. Section 13(3A) Borrower Representation & Bank Disposal SLA          │
  │    - Bank MUST respond within mandatory 15 Calendar Days               │
  │    - Authoritative Precedent: ITC Ltd v. Blue Coast Hotels (2018)      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 4. Section 13(4) Measures (Symbolic Possession & Takeover of Mgmt)     │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 5. Section 14 Application to Chief Metropolitan Magistrate / DM        │
  │    - Mandates physical possession with police assistance               │
  │    - NKGSB Co-op Bank v. Subir Chakravarty (2022)                      │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 6. Section 17 DRT Securitisation Application (Borrower Appeal - 45d)   │
  │    - Section 18 DRAT Appeal: Mandatory 50% Pre-Deposit (Balkrishna)    │
  └────────────────────────────────────────────────────────────────────────┘
```

### Statutory Bars Checked by Engine
1. **Section 26D CERSAI Registration Bar:** Security interest must be registered with CERSAI. Under Section 26D (effective Jan 2020), no secured creditor can exercise Chapter III enforcement rights without mandatory CERSAI registration.
2. **Section 31(i) Agricultural Land Bar:** Security enforcement under SARFAESI is strictly prohibited against any parcel classified as agricultural land (*K. Sreedhar v. Raus Construction Pvt Ltd (2023)*).
3. **Section 31(h) De Minimis Debt Bar:** Claims where the remaining principal plus interest is less than 20% of the original principal debt are barred from SARFAESI.
4. **Section 31(j) Financial Limit Bar:** Debt claims below ₹1 Lakh are excluded.

---

## 4.3 Criminal Litigation Engine (CrPC / BNSS 2023 & IPC / BNS 2023)

JudiQ’s Criminal Engine supports Indian criminal jurisprudence spanning both the historic Code of Criminal Procedure (CrPC) and Indian Penal Code (IPC), as well as the modern **Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023)** and **Bharatiya Nyaya Sanhita (BNS, 2023)**.

### Core Modules
1. **Anticipatory Bail Calculator (CrPC S.438 / BNSS S.482):** Evaluates custodial necessity, gravity of offense, likelihood of flight, and prior antecedents under the landmark *Sushila Aggarwal v. State (NCT of Delhi) (2020)* Constitution Bench ruling.
2. **Regular Bail Evaluation (CrPC S.437/439 / BNSS S.480/483):** Applies the Supreme Court "Triple Test" (*P. Chidambaram v. Directorate of Enforcement (2019)*):
   - Flight risk / Likelihood of absconding.
   - Risk of tampering with documentary or electronic evidence.
   - Likelihood of influencing or intimidating witnesses.
3. **Statutory Default Bail Tracker (CrPC S.167(2) / BNSS S.187):** Computes mandatory statutory bail rights upon expiration of the 60-day or 90-day investigation window without police charge-sheet filing (*Ritu Chhabaria v. Union of India (2023)*).
4. **Quashing Petition Auditor (CrPC S.482 / BNSS S.528):** Tests criminal complaints against the 7 landmark principles laid down in *State of Haryana v. Bhajan Lal (1992)* and *Neeharika Infrastructure v. State of Maharashtra (2021)* to identify malicious prosecution, civil disputes dressed up as criminal offenses, and absence of prima facie ingredients.

---

## 4.4 Civil Litigation Engine (CPC 1908 & Commercial Courts Act 2015)

The Civil Engine provides procedural roadmap optimization under the **Code of Civil Procedure, 1908** and the **Commercial Courts Act, 2015**.

### Key Provisions
1. **Summary Suits (Order XXXVII CPC):** Rapid debt recovery based on written contracts, bills of exchange, and cheques. Computes leave to defend viability using the *IDBI Trusteeship Services v. Hubtown Ltd (2017)* 5-tier test.
2. **Rejection of Plaint (Order VII Rule 11 CPC):** Scans plaints for lack of cause of action, undervaluation, non-payment of court fees, or claims barred by limitation (*Dahiben v. Arvindbhai Kalyanji Bhanusali (2020)*).
3. **Mandatory Pre-Institution Mediation (Section 12A Commercial Courts Act):** Checks if urgent interim relief is pled. If not, Section 12A pre-institution mediation is mandatory; plaints filed without exhausting S.12A are rejected outright (*Patil Automation Pvt Ltd v. Rakheja Engineers (2022)*).
4. **Infrastructure Injunction Bar (Section 20A Specific Relief Act 1963):** Automatically bars interim injunctions against infrastructure and public utility contracts (*N.G. Projects Ltd v. Vinod Kumar Jain (2022)*).

---

## 4.5 Institutional Banking & Stressed Asset Recovery OS

The Institutional Banking Suite is engineered specifically for Stressed Asset Recovery Branches (SARB), Large Corporate Recovery (LCR) teams, and General Counsel of Indian Scheduled Commercial Banks (SBI, PNB, HDFC, ICICI, Bank of Baroda, Axis, Canara).

```
                       5-TAB INSTITUTIONAL BANKING OS
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. STATUTORY INTAKE & FORENSIC AUDIT                                        │
│    - 5 Institutional Reference Portfolios (Tier 1 to Tier 5)                │
│    - 6-Point Evidentiary Asset Checklist & Milestone Limit Verification     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. MULTI-TRACK STATUTORY ORCHESTRATOR                                       │
│    - Simultaneous viability across S.138, SARFAESI, DRT, IBC S.95, and RBI  │
│    - Concurrent forum compatibility under Transcore & Pioneer Urban rulings │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. STATUTORY NOTICE & S.65B/BSA S.63 DRAFTER                                │
│    - Auto-generates S.138 Demand, SARFAESI S.13(2), S.65B/63, S.142 Petitions│
│    - Court-admissible markdown preview with copy/download controls          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. OTS VS LITIGATION NPV DECISION ENGINE                                    │
│    - Financial model: Time decay discount, legal cost deduction, NPV yield  │
│    - RBI Tier-1 Capital provisioning release write-back modeling            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. EMPANELED ADVOCATE SLA & DISPATCH HUB                                    │
│    - Counsel registry with High Court/DRT win rates and turnaround SLAs     │
│    - 1-Click brief handoff with 48h court filing SLA ledger tracking        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Institutional Reference Portfolios
1. **Tier 1 — Clean Standard S.138 (₹8.5L):** 100% compliant timeline, complete 6-point evidentiary pack, ready for immediate filing with 20% S.143A interim compensation motion.
2. **Tier 2 — Curable Procedural Gaps (₹14.0L):** Notice sent in time, but missing India Post tracking report and Banker's Book Section 65B certificate. Identifies step-by-step cure actions.
3. **Tier 3 — Critical Statutory Trap (₹25.0L):** Complaint filed on Day 8 of 15-day cure window. Flags fatal bar u/s 138(c) under *Yogendra Pratap Singh* and instructs refiling.
4. **Tier 4 — Concurrent SARFAESI Enforcement Bar (₹1.80 Cr):** Enforcement attempted without mandatory CERSAI registration (*S.26D*) and on agricultural collateral (*S.31(i)*). Flags dual fatal statutory bars.
5. **Tier 5 — Limitation Delay with Condonation (₹65.0L):** Complaint filed 20 days late. Compliant only with formal S.142(1)(b) Condonation Application & Sufficient Cause Affidavit.

---

# 5. Adversarial Simulation & Scoring Mechanics

### 5.1 The 10-Pillar Structural Viability Scoring Algorithm
The readiness of any case is evaluated across 10 statutory dimensions, starting from a base score of 100 points:

$$\text{Viability Score} = \max\left(0, \min\left(100, 100 - \sum \text{Penalties} + \sum \text{Credits}\right)\right)$$

```
┌────────────────────────────────────────────────────────┬─────────────┐
│ STATUTORY EVALUATION PILLAR                            │ MAX PENALTY │
├────────────────────────────────────────────────────────┼─────────────┤
│ 1. Cheque Presentation Window (3 Months / Stale)       │ -50 (FATAL) │
│ 2. Statutory Demand Notice Window (30 Calendar Days)   │ -50 (FATAL) │
│ 3. Borrower Cure Period Observance (15 Calendar Days)  │ -50 (FATAL) │
│ 4. Complaint Limitation Window (30 Days u/s 142)       │ -25 (CURABLE│
│ 5. Corporate Vicarious Liability & Director Averments  │ -35 (FATAL) │
│ 6. Original Evidentiary Pack (Cheque, Memo, Sanction)  │ -20 (CURABLE│
│ 7. Proof of Service (Post Receipts & Tracking Records) │ -15 (CURABLE│
│ 8. Electronic Evidence Certification (S.65B / BSA S.63)│ -15 (CURABLE│
│ 9. Financial Capacity & Legally Enforceable Debt Proof │ -15 (CURABLE│
│ 10. Collateral Validity & Registration (CERSAI / Agri) │ -45 (FATAL) │
└────────────────────────────────────────────────────────┴─────────────┘
```

### 5.2 Courtroom Survivability Curve
JudiQ calculates stage-by-stage progression survival probabilities across 4 court tiers:

$$\text{JMFC (Magistrate Trial)} \longrightarrow \text{Sessions Court Appeal} \longrightarrow \text{High Court Revision} \longrightarrow \text{Supreme Court SLP}$$

- **JMFC Survivability:** Governed by threshold statutory compliances (presentation, notice delivery, prima facie evidence).
- **Sessions Survivability:** Governed by Section 148 mandatory 20% deposit compliance and debt enforceability.
- **High Court Survivability:** Governed by Section 141 averment precision and Section 482 quashing standards.
- **Supreme Court Survivability:** Governed by settled constitutional bench precedents.

---

# 6. Caseroom, Forensic OCR & Evidence Certification (S.65B / BSA S.63)

### 6.1 Digital Evidence Vault
The Caseroom functions as a secure digital evidence repository. Each piece of uploaded evidence (cheque, bank memo, legal notice, postal certificate, account statement) is processed with:
1. **Cryptographic SHA-256 Hash Chaining:** Creates an immutable tamper-evident fingerprint upon upload.
2. **Forensic Optical Character Recognition (OCR):** Extracts text, monetary figures, IFSC codes, account numbers, and dispatch timestamps.
3. **Contradiction Detection:** Cross-references the cheque amount written in words vs figures, the date on the return memo vs the notice date, and the names of authorized signatories against MCA corporate records.

### 6.2 Section 65B Indian Evidence Act / Section 63 BSA 2023 Electronic Evidence Certificate
To render computerized account ledgers, CBS printouts, and digital notices admissible in Indian courts without oral evidence, JudiQ generates a court-admissible certificate complying with the Supreme Court mandate in *Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal (2020)*:
- Identifies the electronic device, system hardware, and software environment.
- Avers regular lawful operation and production during ordinary course of business.
- Certifies integrity and absence of electronic tampering.
- Embeds SHA-256 document checksums.

---

# 7. Automated Legal Pleadings & Drafting Engine

JudiQ’s Draft Engine transforms structured case data into court-ready pleadings formatted to Indian High Court and Supreme Court practice rules.

### Supported Document Templates
1. **Formal Statutory Demand Notice u/s 138(b) NI Act:** Incorporates Section 141 corporate director liability clauses, details cheque dishonour reasons, and sets a 15-day cure deadline.
2. **Criminal Complaint u/s 138 NI Act:** Ready for presentation before the Chief Judicial Magistrate / Metropolitan Magistrate, complete with verification clause, list of witnesses, and list of relied-upon documents.
3. **SARFAESI Section 13(2) Demand Notice:** Includes formal schedule of mortgaged immovable/movable assets, loan sanction details, NPA date, and 60-day enforcement notice.
4. **Section 142(1)(b) Delay Condonation Application & Sufficient Cause Affidavit:** Formatted with formal verification clauses citing *Birendra Prasad Sah* and medical/administrative delay grounds.
5. **Section 143A Petition for 20% Interim Compensation Deposit:** Pre-structured application citing *Noor Mohammed v. Khurram Pasha*.
6. **Section 65B IEA / Section 63 BSA 2023 Electronic Evidence Certificate:** Certified by authorized bank officer or custodian of computer systems.
7. **Criminal Quashing Petition u/s 482 CrPC / BNSS S.528:** Structures grounds for quashing based on *Bhajan Lal* standards (civil dispute dressed as criminal, absence of Section 141 specific averments).

---

# 8. Frontend Architecture & UI/UX Design System

### 8.1 Technology Stack & Rendering Performance
- **Zero Framework Bloat:** Built with Vanilla ES6 JavaScript modules and Native Web Components to guarantee lightning-fast sub-50ms screen transitions on any hardware.
- **Glassmorphism 2.0 Aesthetic:** Blue-and-white theme featuring subtle backdrop blur filters (`backdrop-filter: blur(12px)`), refined border strokes, and curated typography (`Cinzel`, `Outfit`, `Inter`).
- **Dynamic Dark / Light Mode:** Native CSS custom properties seamlessly toggle between dark glassmorphism and executive institutional light mode.
- **Memory-Safe Chart Registry:** Custom `ChartRegistry` manages Chart.js instances, automatically destroying previous canvas contexts to eliminate memory leaks during rapid adversarial state recalculations.

### 8.2 Screen Navigation & Security Gate Architecture
The frontend is controlled by a centralized `switchScreen(targetScreenId)` router in [`frontend/ui.js`](file:///c:/Users/Atharva/OneDrive/Desktop/judiq-ai/frontend/ui.js):
```javascript
// Screen State Routing
'landingScreen'          ──► Main Public Portal & Product Overview
'caseWizardScreen'       ──► 8-Step Interactive Litigation Intake Wizard
'resultsScreen'          ──► Adversarial Simulation & Strategy Results Workspace
'bankRecoveryScreen'     ──► Institutional Banking & Stressed Asset Recovery OS (Auth Gated)
'adminPortalScreen'      ──► Master Administration & Governance Control Center (Admin Gated)
'draftStudioScreen'      ──► Court Pleadings Drafting & Export Studio
```

### 8.3 Authentication Security Gate
Access to `bankRecoveryScreen` is protected by a client-and-server security gate:
```javascript
if (targetScreenId === 'bankRecoveryScreen') {
    const hasBankUser = !!localStorage.getItem('judiq_bank_user');
    const hasBankJwt = !!localStorage.getItem('judiq_bank_jwt');
    const hasGeneralAuth = !!localStorage.getItem('judiq_token') || (window.state && window.state.currentUser);
    
    if (!hasBankUser && !hasBankJwt && !hasGeneralAuth) {
        window.toast.show("Please sign in or register with your institutional bank credentials.", "warning");
        window.openBankAuthModal();
        return;
    }
}
```

---

# 9. Master Admin, Governance & Telemetry Control Center

The Master Admin Portal provides bank heads, law firm managing partners, and platform administrators with complete oversight.

```
                         ADMIN CONTROL CENTER (3 TABS)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SYSTEM METRICS & PERFORMANCE OBSERVABILITY                               │
│    - Total System Requests, Mean Response Latency, Active Caseroom Sessions │
│    - Engine Registry Status (All 18 Engines Online)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. USER QUOTA & CREDITS GOVERNANCE                                          │
│    - User Account Registry, Monthly Token Allocations, Tier Switching       │
│    - 1-Click Token Quota Reset & Account Suspension Toggles                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. INSTITUTIONAL BANK GOVERNANCE & AUDIT LOGS                               │
│    - Bank Recovery Officer Directory across Nationalized & Private Banks    │
│    - Real-Time Statutory Audit Ledger: Case Reference, Viability, Verdicts  │
│    - Monthly Audit Allowance Allocation & Officer Status Toggles            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Universal Admin Elevation
Accounts associated with designated master administrator emails (`admin@judiq.ai`, `gandhiatharv565@gmail.com`) automatically receive universal administrator elevation (`is_admin: true`), bypassing token rate limits and gaining instant multi-branch switching privileges.

---

# 10. Security, Encryption & DPDP Act Compliance

### 10.1 Encryption Architecture
- **In-Transit:** Mandatory TLS 1.3 encryption across all client-server communications.
- **At-Rest:** Confidential case dossiers and evidence payloads are encrypted using **AES-256 Fernet** encryption (`cryptography.fernet`) before being written to disk.
- **Key Derivation:** Cryptographic keys are managed via environment variables (`ENCRYPTION_KEY`, `SECRET_KEY`) with fallback validation against weak development keys.

### 10.2 Digital Personal Data Protection (DPDP) Act 2023 Compliance
- **Data Fiduciary Standard:** Case facts are processed strictly for the user-authorized purpose of legal strategy formulation.
- **Strict Model Isolation:** Customer confidential evidence, pleadings, and debtor particulars are **strictly isolated** and **never used** to train or fine-tune public foundation models.
- **Right to Erasure:** Users can irreversibly purge caserooms and associated cryptographic hashes with 1-click deletion.

---

# 11. Complete REST API Reference & Schema Catalog

All platform routes are versioned and served under the `/api/v1` prefix (with direct backward-compatible aliases on root paths).

### 11.1 Authentication & Session
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/anonymous` | Creates an anonymous trial session token | No |
| `POST` | `/api/v1/bank/auth/register` | Registers a bank officer with institutional email verification | No |
| `POST` | `/api/v1/bank/auth/login` | Authenticates bank officer and issues JWT | No |
| `GET` | `/api/v1/bank/auth/profile` | Retrieves bank officer profile and remaining monthly quota | Yes (JWT) |
| `GET` | `/api/v1/bank/auth/validate-domain` | Validates if an email domain meets institutional banking rules | No |

### 11.2 Core Litigation Analysis
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/analyze` | Executes full deterministic audit, scoring, and adversarial simulation | Yes |
| `POST` | `/api/v1/caseroom/forensic-audit` | Performs multi-document forensic OCR and contradiction scan | Yes |
| `GET` | `/api/v1/cases` | Lists saved case files for the authenticated user | Yes |
| `GET` | `/api/v1/cases/detail` | Retrieves complete analysis results for a specific case ID | Yes |
| `DELETE`| `/api/v1/cases/delete` | Irreversibly deletes a case file and its evidence payload | Yes |

### 11.3 Enterprise Banking & Stressed Asset Recovery
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/bank/recovery-audit` | Executes statutory recovery audit and logs entry to DB ledger | Yes |
| `POST` | `/api/v1/bank/multi-track-strategy`| Evaluates concurrent viability across 5 statutory recovery tracks | Yes |
| `POST` | `/api/v1/bank/generate-statutory-notice`| Generates court-admissible legal notices, delay petitions, 65B | Yes |
| `POST` | `/api/v1/bank/ots-npv-calculator` | Calculates OTS vs litigation NPV, time decay, RBI write-backs | Yes |
| `GET` | `/api/v1/bank/advocates` | Retrieves directory of empaneled advocates with win rates & SLAs | Yes |
| `POST` | `/api/v1/bank/advocates/dispatch`| Dispatches brief to counsel and records 48h court filing SLA | Yes |
| `GET` | `/api/v1/bank/branches` | Retrieves pre-configured partner bank branches | No |
| `GET` | `/api/v1/bank/portfolio-templates`| Returns 5 production reference recovery case portfolios | No |
| `GET` | `/api/v1/bank/rules` | Returns the complete Statutory Legal-Rule Registry with citations | No |

### 11.4 Legal Pleadings & Document Generation
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/documents/generate-pdf` | Generates a high-resolution PDF case intelligence report | Yes |
| `POST` | `/api/v1/documents/draft-pdf` | Generates a court-admissible legal pleading in PDF format | Yes |
| `GET` | `/api/v1/documents/draft/history` | Retrieves versioned drafting history for a case matter | Yes |
| `POST` | `/api/v1/verify/memo` | Validates bank return memo authenticity and dishonour reasons | Yes |

### 11.5 Platform Governance & Observability
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Server health check with CPU, RAM, and Engine Registry size | No |
| `GET` | `/metrics` | Prometheus metrics scraping endpoint | No |
| `POST` | `/api/v1/admin/auth/verify` | Authenticates platform administrator credentials | No |
| `GET` | `/api/v1/admin/stats` | Retrieves system-wide usage, case count, and server stats | Yes (Admin) |
| `GET` | `/api/v1/admin/users` | Lists all registered users and quota usage | Yes (Admin) |
| `POST` | `/api/v1/admin/users/allocate` | Allocates analysis credits/tokens to a user account | Yes (Admin) |
| `POST` | `/api/v1/admin/users/reset-usage` | Resets a user account's monthly usage counter | Yes (Admin) |
| `POST` | `/api/v1/admin/users/toggle-status` | Suspends or activates a user account | Yes (Admin) |
| `GET` | `/api/v1/admin/bank/stats` | Retrieves aggregate institutional banking metrics | Yes (Admin) |
| `GET` | `/api/v1/admin/bank/officers` | Lists registered bank recovery officers | Yes (Admin) |
| `POST` | `/api/v1/admin/bank/officers/create`| Registers a bank officer from admin console | Yes (Admin) |
| `POST` | `/api/v1/admin/bank/officers/allocate`| Allocates monthly recovery audit allowance to officer | Yes (Admin) |
| `POST` | `/api/v1/admin/bank/officers/toggle` | Suspends or activates a bank officer account | Yes (Admin) |
| `GET` | `/api/v1/admin/bank/audits` | Retrieves live statutory recovery audit ledger | Yes (Admin) |
| `POST` | `/api/v1/telemetry/error` | Receives client-side error telemetry logs | No |

---

# 12. Deployment, Localhost Operations & Troubleshooting Runbook

### 12.1 Localhost 1-Click Launch Options
The platform is designed to launch with zero friction on Windows, macOS, and Linux:

- **Option A: PowerShell Launcher (Recommended on Windows)**
  ```powershell
  .\start_localhost.ps1
  ```
- **Option B: Windows Batch Launcher**
  Double-click [`start_localhost.bat`](file:///c:/Users/Atharva/OneDrive/Desktop/judiq-ai/start_localhost.bat)
- **Option C: Direct Terminal ASGI Execution**
  ```powershell
  cd backend
  python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
  ```

### 12.2 Localhost URLs
- **Web Application Portal:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc API Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)
- **Prometheus Metrics:** [http://localhost:8000/metrics](http://localhost:8000/metrics)

### 12.3 Docker Deployment
```bash
# Build and start containerized stack
docker compose up --build -d

# Verify container status
docker compose ps

# Tail logs
docker compose logs -f
```

### 12.4 Automated Test Suite Execution
```bash
# Run banking enterprise suite
python -m pytest backend/tests/test_bank_recovery_engine.py backend/tests/test_bank_enterprise_features.py -v

# Run full platform automated test suite (3,404 Tests)
python -m pytest backend/tests/ -v
```

### 12.5 Troubleshooting & Common Scenarios
| Issue | Root Cause | Resolution |
|---|---|---|
| `[WinError 10013] Access forbidden` | Lingering Python process holding port 8000 | Run: `Get-NetTCPConnection -LocalPort 8000 \| Stop-Process -Id {$_.OwningProcess} -Force` |
| `404 Not Found on /advocates` | Endpoint path missing `/api/v1/bank` prefix | Both versioned route `/api/v1/bank/advocates` and direct alias `/advocates` are mounted. |
| `Bank Recovery Portal closed / won't open` | Unauthenticated guest session | Click "Officer Sign In / Register", select a bank branch preset (e.g. SBI SARB Mumbai), and sign in. |
| `Database tables missing` | Fresh environment startup | Database tables auto-initialize on startup via `DatabaseManager.init_db()` in `lifespan`. |

---

*JUDIQ AI — Built for the Indian Courtroom. Engineered for Institutional Stressed Asset Recovery.*
