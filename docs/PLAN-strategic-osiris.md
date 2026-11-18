# PLAN: Strategic OSIRIS — Multi-Agent Strategic Intelligence Platform

> **Project Name:** Strategic OSIRIS (SIFP — Strategic Intelligence Fusion Platform)
> **Created:** 2026-11-18
> **Source:** [ChatGPT Design Conversation](https://chatgpt.com/share/6afdfaa5-ff88-83ea-9983-87fd6c3bd51f)
> **Status:** 📋 Planning

---

## 1. Project Vision

Build a **hybrid multi-agent strategic intelligence platform** that combines military/strategic analysis, OSINT collection, early warning, and scenario forecasting — designed to support military attaché operations and strategic decision-making.

The platform is **not** a news aggregator. It is an **intelligence production system** with traceable evidence, structured analytical tradecraft, and mandatory human review before dissemination.

### Core Differentiators
- **Multi-Agent Debate:** Independent specialist analysts (military, political, economic, technology) produce separate assessments; a Red Team agent challenges assumptions and contradictions
- **Egypt-Centric Strategic Assessment:** Analysis tied to national interests via a configurable framework (default: Egypt)
- **Intelligence-to-Decision Pipeline:** Event → Assessment → Scenarios → Indicators → Recommendations — all auditable and reviewable

---

## 2. Architecture Decision: Fork PYTHIA + Extend

Based on the design conversation's evaluation of multiple platforms:

| Platform | Verdict |
|----------|---------|
| **PYTHIA** (github.com/jangles-byte/Pythia) | ✅ **Primary base** — already has multi-agent swarm, forecasting, OSINT, early warning, local AI via Ollama |
| **OSIRIS** (github.com/simplifaisoul/osiris) | ✅ Included via PYTHIA (PYTHIA builds on OSIRIS for situational awareness) |
| **ShadowBroker** (github.com/BigBodyCobain/Shadowbroker) | 🔍 Reference for OSINT automation patterns |
| **WorldMonitor / Crucix** | 📚 Reference for ideas & supplementary data sources |
| Palantir / Babel Street / Dataminr | 📖 Commercial benchmarks (not open-source) |

**Decision:** Fork PYTHIA and develop **Strategic OSIRIS** — adding an Analyst Room module with 14 specialized AI agents, structured evidence management, and bilingual reporting.

### Recommended Stack

| Layer | Technology |
|-------|-----------|
| Frontend | PYTHIA/OSIRIS existing UI (Next.js) + new Analyst Room module |
| Backend API | FastAPI + Pydantic |
| Agent Orchestration | LangGraph (or native orchestration extending PYTHIA's swarm) |
| AI Models | LiteLLM + Ollama (local) + Cloud APIs (OpenAI/Claude/Gemini) |
| Scheduling & Integration | n8n |
| Task Queues | Redis + Celery |
| Structured Data | PostgreSQL |
| Semantic Search | pgvector |
| Document Storage | MinIO / S3 |
| Document Extraction | Docling |
| Knowledge Base | Onyx (RAG) |
| Report Publishing | Notion + PDF/DOCX export |
| Monitoring | OpenTelemetry + Grafana |
| Deployment | Docker Compose (initially) |

---

## 3. The 14 Agents

Each agent has a defined role, tools, permissions, and output schema. The Chief Strategic Analyst dynamically selects which agents to activate per task.

| ID | Agent | Role | Temperature |
|----|-------|------|------------|
| A01 | **Chief Strategic Analyst** | Supervisor — task planning, synthesis, final assessment | 0.3 |
| A02 | **OSINT Collector** | Evidence gathering from authorized open sources | 0.1 |
| A03 | **Verification Agent** | Source credibility & evidence validation (Admiralty Code) | 0.1 |
| A04 | **Military Analyst** | Defense capabilities, doctrine, military cooperation | 0.2 |
| A05 | **Political Analyst** | Internal/external politics, diplomacy, actor motivations | 0.3 |
| A06 | **Economic Analyst** | GDP, trade, sanctions, energy, defense spending | 0.2 |
| A07 | **Geopolitical Analyst** | Regional balances, great power competition, strategic geography | 0.3 |
| A08 | **Defense Tech Analyst** | Defense industry, aerospace, cyber, dual-use technology | 0.2 |
| A09 | **GEOINT Analyst** | Geographic intelligence, satellite imagery interpretation | 0.1 |
| A10 | **Country Intelligence Analyst** | Comprehensive country profiles and updates | 0.2 |
| A11 | **Forecast Analyst** | Scenario planning, integration with OI Forecast Engine | 0.6 |
| A12 | **Early Warning Analyst** | Indicators & warning, threshold monitoring, alerts | 0.1 |
| A13 | **Red Team Analyst** | Critical review, bias detection, ACH, devil's advocacy | 0.5 |
| A14 | **Report Agent** | Bilingual (AR/EN) strategic report generation | 0.2 |

### Agent Interaction Flow

```
User / Decision Maker
        ↓
   A01 — Chief Strategic Analyst (plans & assigns tasks)
        ↓
   A02 → A03 (Collect → Verify)
        ↓
   Shared Evidence Store
        ↓
   A04-A12 (Parallel specialist analysis)
        ↓
   A01 — Synthesis of findings
        ↓
   A13 — Red Team review
        ↓
   A14 — Report generation
        ↓
   Human Review & Approval → Dissemination
```

---

## 4. Core Modules

### 4.1 Analyst Room (New Module)
- Research question input with country/region/horizon selection
- Intelligence assessment mode selection (10 predefined modes)
- Real-time agent execution status
- Individual agent findings display
- Shared evidence browser
- Contradiction highlighting
- Red Team findings panel
- Final strategic assessment
- Human approval workflow
- Report export (PDF/DOCX/Notion)
- Bilingual AR/EN with RTL support

### 4.2 Agent Management (New Module)
- Create/modify custom agents
- System prompt editor
- LLM provider/model selection per agent
- Tool assignment & permissions
- Execution budgets & limits
- Agent testing & history
- Token consumption monitoring

### 4.3 Evidence & Knowledge Management
- PostgreSQL as System of Record
- Dual timestamps: event time vs. system ingestion time
- Original source archival with content hashes
- Separated reliability scores: source reliability + evidence strength + analytical confidence
- pgvector for semantic search
- Onyx integration for document knowledge base

### 4.4 Early Warning System
- Indicator-based monitoring (not LLM polling)
- Measurable thresholds with baseline comparisons
- Alert severity levels: Informational → Low → Medium → High → Critical
- Automated verification before escalation
- Mandatory human review for high/critical alerts
- Webhook integration for notifications

### 4.5 Strategic Report Templates
1. Daily Intelligence Brief
2. Strategic Assessment (تقدير موقف)
3. Country Intelligence Profile
4. Defense Industry Assessment
5. Regional Security Assessment
6. Technology Assessment
7. Crisis Assessment
8. Strategic Scenario Analysis
9. Comparative Country Assessment
10. Early Warning Assessment

---

## 5. Database Schema

### Core Tables

| Table | Key Fields |
|-------|-----------|
| `sources` | id, name, type, reliability, license |
| `documents` | id, source_id, url, published_at, content_hash |
| `events` | id, title, event_time, location, event_type |
| `entities` | id, name, entity_type, country |
| `claims` | id, statement, evidence_status, confidence |
| `claim_evidence` | claim_id, document_id, evidence_span, stance |
| `assessments` | id, topic, findings, assumptions, confidence |
| `indicators` | id, definition, baseline, threshold, window |
| `alerts` | id, indicator_id, severity, status, triggered_at |
| `reports` | id, type, version, approval_status |
| `agent_runs` | id, agent, model, status, cost, duration |
| `audit_logs` | id, actor, action, timestamp, object_id |

Additional: `users`, `roles`, `workspaces`, `tasks`, `scenarios`, `subscriptions`, `report_evidence`

---

## 6. Project Structure

```
strategic-intelligence-platform/
│
├── apps/
│   ├── web/                 # Next.js Dashboard (extends PYTHIA/OSIRIS)
│   └── api/                 # FastAPI backend
│
├── services/
│   ├── orchestrator/        # Agent orchestration (LangGraph workflows)
│   ├── collection/          # OSINT ingestion
│   ├── verification/        # Evidence validation
│   ├── analysis/            # Specialized analyst agents
│   ├── warning/             # Indicators and alerts engine
│   └── reporting/           # Report generation (AR/EN)
│
├── packages/
│   ├── schemas/             # Pydantic data contracts
│   ├── prompts/             # Versioned agent system prompts
│   └── evaluation/          # Quality benchmarks & agent evals
│
├── infrastructure/
│   ├── docker/              # Docker Compose configs
│   ├── migrations/          # PostgreSQL migrations
│   └── monitoring/          # Grafana dashboards
│
└── tests/
    ├── integration/
    ├── security/
    └── agent-evals/         # Agent quality evaluations
```

---

## 7. Implementation Roadmap

### Phase 1 — Foundation (Weeks 1-2)
- [ ] Fork PYTHIA repository
- [ ] Repository inspection & architecture documentation
- [ ] Set up Docker Compose with PostgreSQL, Redis, FastAPI
- [ ] Design Agent Registry and Tool Registry interfaces
- [ ] Define Pydantic data contracts (`EvidenceBundle`, `AnalystFinding`, `StrategicAssessment`, `WarningSignal`)
- [ ] Set up LiteLLM + Ollama provider integration
- [ ] Database migrations for core schema

### Phase 2 — Strategic Assessment MVP (Weeks 3-5)
- [ ] Implement 7 initial agents:
  1. Chief Strategic Analyst (A01)
  2. OSINT Collector (A02)
  3. Verification Agent (A03)
  4. Military Analyst (A04)
  5. Political Analyst (A05)
  6. Economic Analyst (A06)
  7. Red Team Analyst (A13)
- [ ] Build orchestration engine (native or LangGraph)
- [ ] Implement evidence store with citation tracking
- [ ] Create basic Analyst Room UI
- [ ] Working end-to-end assessment workflow

### Phase 3 — Advanced Agents (Weeks 6-7)
- [ ] Add Geopolitical Analyst (A07)
- [ ] Add Defense Tech Analyst (A08)
- [ ] Add GEOINT Analyst (A09)
- [ ] Add Country Intelligence Analyst (A10)
- [ ] Add Forecast Analyst (A11) — integrate with OI Forecast Engine
- [ ] Add Report Agent (A14) with bilingual output

### Phase 4 — Operational Intelligence (Week 8+)
- [ ] Implement Early Warning Analyst (A12) with indicator engine
- [ ] Build Agents Management admin interface
- [ ] Add Notion integration for report publishing
- [ ] Implement scheduled daily briefings
- [ ] Integrate Onyx knowledge base
- [ ] Security hardening (RBAC, MFA, prompt injection mitigation)
- [ ] Comprehensive testing & evaluation suite

---

## 8. Acceptance Test

**Research Question:** "Assess Turkey's defense industry development, its international defense partnerships, and the strategic implications for Egypt over the next five years."

**Expected Behavior:**
- [ ] Chief Analyst creates a research plan with PIRs
- [ ] Collector retrieves relevant public evidence
- [ ] Verification Agent evaluates source credibility (Admiralty Code)
- [ ] Military, Political, Economic, and Technology analysts execute independently
- [ ] Chief Analyst synthesizes findings
- [ ] Red Team challenges the assessment
- [ ] Unsupported claims are flagged
- [ ] Significant disagreements are preserved (not averaged away)
- [ ] A cited strategic assessment is generated in Arabic
- [ ] Report remains pending until human approval

---

## 9. Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Substantive claims cited to sources | 100% |
| Citation accuracy (human review) | ≥ 95% |
| Unsupported claim detection (test set) | ≥ 90% |
| Report generation time (after collection) | < 5 minutes |
| Automated task success rate | ≥ 95% |
| No publication without approval | 100% |
| Alert traceability | 100% |

---

## 10. Security & Governance

> [!CAUTION]
> This platform may operate in defense/diplomatic contexts. Security is by design, not afterthought.

- **Data Classification:** Separate public OSINT from authorized internal documents
- **Access Control:** RBAC + MFA + workspace isolation
- **Agent Security:** Limited tool permissions, output validation, prompt injection prevention
- **Data Protection:** Encrypted transit & storage, secrets management outside code
- **Human Approval Gates:** No high-importance assessments or alerts published automatically
- **Local AI Option:** Ollama for sensitive (but unclassified) data processing
- **Scope Limitation:** MVP uses only public/authorized information sources

> [!WARNING]
> Do NOT use this platform for classified intelligence processing without independent security audit. Local models alone do not satisfy military information security requirements.

---

## 11. Analytical Methodologies (Agent Toolkit)

Agents select appropriate techniques per task:

- SWOT Analysis
- PESTLE Analysis
- Analysis of Competing Hypotheses (ACH)
- Key Assumptions Check
- Indicators & Warning
- Scenario Planning
- Stakeholder Analysis
- Risk Matrix
- Red Team Analysis
- Devil's Advocacy
- Cross-Impact Analysis
- DIME / PMESII frameworks

---

## 12. Data Sources (MVP)

| Source Type | Examples |
|------------|---------|
| Conflict Data | ACLED |
| Event Data | GDELT |
| News Feeds | RSS from major wire services |
| Official Sources | Government press releases, UN resolutions |
| Defense Publications | SIPRI, IISS, Jane's (public portions) |
| Economic Data | World Bank, IMF, national statistics |
| Geospatial | OSIRIS built-in layers |
| Social/Telegram | Public channels (via OSIRIS) |

---

## 13. Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Agent hallucination | Mandatory citation requirement + Verification Agent + Red Team |
| Echo chamber (agents agreeing without independent evidence) | Evidence traced to original independent sources; repetition ≠ corroboration |
| API cost explosion | Token budgeting per agent, dynamic agent selection, local models for routine tasks |
| PYTHIA upstream breaking changes | Isolate customizations in separate modules; maintain fork discipline |
| Prompt injection via external documents | Treat source content as data, never as instructions; sandbox agent tools |
| Over-engineering before validation | MVP with 7 agents first; prove analytical quality before scaling |

---

## 14. Architecture Decisions ✅

| Decision | Choice |
|----------|--------|
| **Deployment** | VPS (private server) |
| **AI Models** | OpenRouter (multi-model gateway) |
| **Knowledge Base** | OSIRIS built-in API (no Onyx/custom RAG in MVP) |
| **Orchestrator** | LangGraph or native (no Hermes dependency) |
| **UI Language** | Bilingual Arabic (RTL) + English |
| **MVP Countries** | 🇪🇬 Egypt, 🇱🇾 Libya, 🇮🇱 Israel |

### Implications of These Choices

- **VPS:** Docker Compose deployment on a single VPS. Need to provision a server with ≥16GB RAM, 4+ vCPUs, SSD storage. All services (PostgreSQL, Redis, FastAPI, Next.js, n8n) run containerized.
- **OpenRouter:** Single API key routes to multiple models (Claude, GPT-4, Gemini, Llama, Mistral). Cost-efficient model selection per agent — heavier models for Chief Analyst & Red Team, lighter models for collection & verification. No local GPU required.
- **OSIRIS API:** Use PYTHIA/OSIRIS's built-in data sources and APIs (`/agent/view`, `/agent/events`, `/predictions`, `/whatif`, `/brief`) as the knowledge layer. No separate Onyx deployment needed in MVP.
- **Egypt-Libya-Israel focus:** Agent prompts will default to Egyptian national interest perspective. Geographic focus on North Africa, Eastern Mediterranean, and Red Sea corridor.

---

## Next Steps

```
✅ Plan created: docs/PLAN-strategic-osiris.md

Next steps:
- Review the plan and resolve the Open Questions (Section 14)
- Run `/create` to start implementation
- Or modify plan manually
```
