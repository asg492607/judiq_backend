# JudiQ AI: Backend

![JudiQ Backend Architecture](./judiq_hero_adversarial.png)

![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)

The **JudiQ AI Backend** powers deep legal analytics, deterministic statutory calculations, and generative AI drafting for the JudiQ Litigation Operating System. Engineered specifically for **Section 138 NI Act** (Cheque Bounce) matters, it operates under strict segregation of duties to ensure predictable courtroom intelligence.

---

## 🏛️ System Architecture

The backend strictly decouples analytical engines to avoid hallucinations and ensure that statutory bounds directly inform the final analysis:

```mermaid
graph TD
    API(FastAPI Gateway) --> Orchestrator[Engine Core Orchestrator]
    Orchestrator --> DB[(SQLite Database)]
    Orchestrator --> LLM[LLM / GenAI Engine]
    
    Orchestrator --> TE(Timeline Engine)
    Orchestrator --> SE(Scoring Engine)
    Orchestrator --> AE(Adversarial Engine)
    
    TE -. Injects Statutory Bounds .-> SE
    SE -. Multi-pillar Defect Calc .-> AE
```

### Core Engines
- **Timeline Engine (`timeline_engine.py`)**: Maps legal timelines to identify statutory limitation breaches.
- **Scoring Engine (`scoring_engine.py`)**: Multi-pillar approach calculates structural risk. Fatal defects apply multiplicative penalties.
- **Adversarial Engine (`adversarial_engine.py`)**: Simulates opposing counsel arguments to build defense resilience.
- **Draft Engine (`draft_engine.py`)**: Generates high-fidelity legal drafts and court-ready pleadings based on AI synthesis.

---

## 🚀 Setup & Running Locally

**Prerequisites:** Python 3.10+

### Windows PowerShell:
```powershell
# Create Virtual Environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API Server
python main.py
```
*(Alternatively, run `uvicorn main:app --reload`)*

Access the interactive Swagger documentation at `http://localhost:8000/docs`.

---

## 🔒 Security Posture
- **End-to-End Encryption**: Physical evidence is encrypted using AES-256 Fernet before being written to disk in the Caseroom logic.
- **Input Sanitization**: Pydantic V2 schemas implement recursive HTML/XSS sanitization for all inbound REST payloads.
- **DDoS Protection**: `slowapi` enforces strict throughput caps on AI generation endpoints (e.g., 5 requests/minute).

---

## 🧪 Testing

The codebase uses deterministic testing to prevent regressions.

```powershell
pytest tests/
```
*Note: The test suite explicitly disables LLM inference via `monkeypatch` to ensure the core rules engines act deterministically in CI environments.*

---

© 2026 JudiQ AI. Built for the Institutional Courtroom.
