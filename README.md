# Strategic OSIRIS (SIFP) — Multi-Agent Strategic Intelligence Platform
### منصة الاستخبارات والتحليل الاستراتيجي متعددة الوكلاء (مصر • ليبيا • إسرائيل)

Strategic OSIRIS (Strategic Intelligence Fusion Platform) is a defense-grade multi-agent strategic intelligence and decision-support system. It integrates OSINT collection, Admiralty Code verification, multi-domain debate across 14 specialist AI personas, independent Red Team auditing, early warning indicators, and mandatory human review before publication.

---

## 🏛️ Architecture Overview

```
                      User / Military Decision Maker
                                    ↓
                 A01 — Chief Strategic Analyst (Planning & PIRs)
                                    ↓
            A02 OSINT Collector ──→ A03 Verification Agent
                                    ↓ (Admiralty Evaluation A-F, 1-6)
                        Shared Evidence Store
                                    ↓
       ┌────────────────────────────┼────────────────────────────┐
       ↓                            ↓                            ↓
  A04 Military                 A05 Political                A06 Economic
       ↓                            ↓                            ↓
  A07 Geopolitical             A08 Defense Tech             A10 Country Intel
       ↓                            ↓                            ↓
  A09 GEOINT                   A11 Forecast                 A12 Early Warning
       └────────────────────────────┬────────────────────────────┘
                                    ↓
                 A01 — Chief Strategic Analyst (Synthesis)
                                    ↓
                 A13 — Red Team Analyst (Critical Review & ACH)
                                    ↓
                 A14 — Report Agent (Bilingual AR/EN Draft)
                                    ↓
                [🛡️ MANDATORY HUMAN REVIEW & DISSEMINATION GATE]
                                    ↓
                  Approved Intelligence Assessment
```

---

## 🤖 The 14 Specialized Agents

| ID | Agent Persona | Arabic Name | Default Model (OpenRouter) | Role & Responsibility |
|:---|:---|:---|:---|:---|
| **A01** | Chief Strategic Analyst | رئيس خلية التحليل الاستراتيجي | `anthropic/claude-3.5-sonnet` | Task planning, PIRs, synthesis, strategic judgments |
| **A02** | OSINT Collector | وكيل جمع المعلومات | `meta-llama/llama-3.3-70b-instruct` | Event ingestion, feed tracking, timeline building |
| **A03** | Verification Agent | وكيل التحقق والأدلة | `meta-llama/llama-3.3-70b-instruct` | Admiralty code evaluation (A-F, 1-6), claim-evidence links |
| **A04** | Military Analyst | المحلل العسكري والدفاعي | `meta-llama/llama-3.3-70b-instruct` | Force posture, procurement, defense balance, deterrence |
| **A05** | Political Analyst | المحلل السياسي والدبلوماسي | `meta-llama/llama-3.3-70b-instruct` | Leadership dynamics, diplomatic moves, alliances |
| **A06** | Economic Analyst | المحلل الاقتصادي واقتصاديات الدفاع | `meta-llama/llama-3.3-70b-instruct` | Energy corridors, Suez Canal shipping, sanctions, budgets |
| **A07** | Geopolitical Analyst | المحلل الجيوسياسي | `meta-llama/llama-3.3-70b-instruct` | Great power competition, Red Sea, East Med balances |
| **A08** | Defense Tech Analyst | محلل الصناعات الدفاعية | `meta-llama/llama-3.3-70b-instruct` | UAVs, radar, aerospace, tech localization (EDEX) |
| **A09** | GEOINT Analyst | محلل المعلومات الجغرافية | `meta-llama/llama-3.3-70b-instruct` | Chokepoints, maritime straits, border buffer zones |
| **A10** | Country Intel Analyst | محلل شؤون الدول | `meta-llama/llama-3.3-70b-instruct` | Comprehensive profiles & SWOT for Egypt, Libya, Israel |
| **A11** | Forecast Analyst | محلل السيناريوهات والتنبؤ | `meta-llama/llama-3.3-70b-instruct` | 4 alternative future scenarios, tripwires & probabilities |
| **A12** | Early Warning Analyst | وكيل الإنذار المبكر | `meta-llama/llama-3.3-70b-instruct` | Indicator anomalies, threshold breaches, incident surge |
| **A13** | Red Team Analyst | وكيل الفريق الأحمر والمراجعة النقدية | `anthropic/claude-3.5-sonnet` | Independent challenge, bias elimination, ACH audit |
| **A14** | Strategic Report Agent | وكيل صياغة التقارير الاستراتيجية | `meta-llama/llama-3.3-70b-instruct` | Bilingual (Arabic RTL & English) formal report generation |

---

## 🚀 Quickstart & Local Execution

### 1. Requirements
- Python 3.12+ (or `uv`)
- Node.js (optional, for web tooling; frontend is served directly by the API)

### 2. Environment Setup
```bash
# Clone and enter directory
cd geopolitcs

# Create virtual environment
uv venv .venv --python 3.12
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 3. Configure `.env`
```bash
cp .env.example .env
# Edit .env and insert your OpenRouter API key:
# OPENROUTER_API_KEY=sk-or-v1-...
```
*(Note: If no API key is set, the system automatically runs in deterministic mock fallback mode, generating fully formed evidence-based strategic outputs for offline testing).*

### 4. Run the Server
```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at: **`http://localhost:8000`** to access the **Analyst Room** mission dashboard.

---

## 🚢 VPS Deployment (Docker Compose)

The repository includes a production-ready VPS deployment configuration with PostgreSQL (pgvector), Redis, FastAPI, and Nginx reverse proxy.

```bash
cd infrastructure/docker

# Copy environment variables
cp ../../.env.example .env

# Start all containers in background
docker compose up -d --build
```

Services exposed:
- `http://YOUR_VPS_IP` (Port 80/443 via Nginx)
- `http://YOUR_VPS_IP:8000` (Direct FastAPI Backend & Dashboard)

---

## 🧪 Automated Test Suite

Run the full automated test suite verifying all 14 agents, Admiralty verification, indicator threshold alerts, human review gates, and the end-to-end acceptance test:

```bash
.venv\Scripts\pytest -v tests
```

Output:
```
tests/test_agents.py::test_all_14_agents_registered PASSED
tests/test_agents.py::test_build_system_prompt_parameter_substitution PASSED
tests/test_api.py::test_api_health_endpoint PASSED
tests/test_api.py::test_api_agents_list_and_detail PASSED
tests/test_api.py::test_api_assessment_lifecycle PASSED
tests/test_api.py::test_api_indicators_and_alerts PASSED
tests/test_indicators.py::test_indicator_breach_triggers_alert PASSED
tests/test_indicators.py::test_indicator_within_baseline_no_alert PASSED
tests/test_pipeline.py::test_acceptance_strategic_assessment PASSED
tests/test_verification.py::test_admiralty_confidence_calculation PASSED
tests/test_verification.py::test_claim_verification_with_citations PASSED

============================= 11 passed in 4.94s ==============================
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/health` | Health check, agent count, LLM status |
| `GET` | `/api/agents` | List all 14 agents with Arabic & English metadata |
| `GET` | `/api/agents/{id}` | Detailed agent metadata and sample system prompt |
| `POST` | `/api/assessments` | Execute multi-agent strategic assessment |
| `GET` | `/api/assessments` | List all executed assessments |
| `GET` | `/api/assessments/{id}` | Get complete assessment with domain findings & Red Team critique |
| `POST` | `/api/assessments/{id}/approve` | Human review gate (`approve`, `reject`, `request_changes`) |
| `GET` | `/api/assessments/{id}/export` | Export assessment as Markdown (`?format=markdown`) or HTML (`?format=html`) |
| `GET` | `/api/evidence` | List all ingested evidence documents with Admiralty scores |
| `GET` | `/api/indicators` | List strategic early warning indicators (Egypt, Libya, Israel, Red Sea) |
| `POST` | `/api/indicators/{id}/update` | Update indicator metric and evaluate alert threshold |
| `GET` | `/api/alerts` | List active early warning alerts |
| `POST` | `/api/alerts/{id}/dismiss` | Dismiss an alert |
