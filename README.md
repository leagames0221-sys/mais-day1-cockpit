# MAIS — Day-1 Cockpit

> **Day-1 readiness plan generator** that auto-builds a 100-day post-merger integration plan from acquirer / target system / org / process inputs, with **dependency graph + risk score + 5-audience communication kit**.

[![tests](https://img.shields.io/badge/tests-66%20passing-brightgreen)]()
[![pip-audit](https://github.com/leagames0221-sys/mais-day1-cockpit/actions/workflows/pip-audit.yml/badge.svg)](https://github.com/leagames0221-sys/mais-day1-cockpit/actions/workflows/pip-audit.yml)
[![python](https://img.shields.io/badge/python-3.11+-blue)]()
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 30-second pitch

Drafting a Day-1 integration plan from scratch takes a senior PMI consultant a week. Most of that time is mechanical: which system depends on which, which audience hears what, when, in what tone.

**MAIS Day-1 Cockpit** automates the mechanical 80% so the consultant focuses on judgement:
- 4-axis parallel agents (organization / process / system / culture) generate Day-1 / 30 / 100 task nodes via LangGraph
- NetworkX builds the integration dependency graph + topological sort + critical path + cycle detection
- 5-audience communication cascade (employees / customers / vendors / regulators / investors) with citation link-backs
- Japanese mid-market culture detector (5 axes: union response / banking relations / family integration / business customs / trade practices)

Industry benchmark: AI-assisted M&A integration shrinks from 12-18 months → 3-6 months (top-tier PMI advisory research).

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  DD Workbench output (sibling input)         │
│  • Citation array (Q-A pairs)                │
│  • JP fit pattern hits                       │
│  • Question responses                        │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  LangGraph state graph       │
        │  (4 parallel agents)         │
        │  ┌──────────┬─────────────┐  │
        │  │ org      │ process     │  │
        │  ├──────────┼─────────────┤  │
        │  │ system   │ culture     │  │
        │  └──────────┴─────────────┘  │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  NetworkX dependency graph   │
        │  • topological sort          │
        │  • critical path             │
        │  • cycle detection           │
        │  • risk score (5 dim 0-100)  │
        └──────────────┬───────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌────────────────┐         ┌──────────────────────┐
│ Day-1 plan     │         │ 5-audience           │
│ visualizer     │         │ communication kit    │
│                │         │ • employees          │
│ • PlanNodes    │         │ • customers          │
│ • Edges        │         │ • vendors            │
│ • Risk scores  │         │ • regulators         │
│                │         │ • investors          │
│                │         │ + citation link-back │
└────────────────┘         └──────────────────────┘
```

---

## What's inside

| Capability | Implementation |
|---|---|
| **4-axis stateful planner** | LangGraph state graph runs organization / process / system / culture agents in parallel with checkpoint replay |
| **Dependency graph + risk** | NetworkX 3.x — topological sort, critical path, cycle detection, 5-dim risk score (0-100) per node and edge |
| **5-audience communication kit** | LLM drafts press materials / employee letter / FAQ / customer notification / vendor / regulator / investor messages, each with citation link-back |
| **Past PMI failure surface** | 5-stage hybrid retrieval pulls similar past cases (synthetic in PoC; real engagements in production) |
| **JP mid-market culture detector** | Regex + LLM library for 5 axes: union response, banking relationship, family integration, business customs, trade practices |
| **MCP-future-proof** | LangGraph internal calls today; design-documented swap path to MCP server in production phase |

---

## Tech stack

| Layer | Choice |
|---|---|
| Orchestrator | LangGraph 1.0+ (MIT) — stateful DAG with checkpoint replay |
| Fallback orchestrator | Pydantic AI (MIT) — type-safe + MCP-native, switchable if LangGraph hits red flags |
| Graph | NetworkX 3.x (BSD-3) |
| Citation infra | LlamaIndex CitationQueryEngine (MIT) |
| Retrieval | rank-bm25 + multilingual-e5-large + cross-encoder/ms-marco-MiniLM-L-12-v2 + LLM listwise |
| LLM | Anthropic SDK (MIT) — Claude Sonnet 4.6 with MockProvider swap |
| Web | FastAPI + uvicorn + Jinja2 (MIT) |
| Schema | Pydantic v2 (MIT) |
| Crypto | cryptography Fernet (Apache-2.0) — vault for contact info |
| Tests | pytest (66 collected) |
| Synthetic data | Faker ja_JP (MIT) |

---

## Decomposed prior art

| Reference | Pattern adopted |
|---|---|
| [Dealroom Day-1 readiness checklist](https://dealroom.net/resources/templates/integration-day-1-readiness-checklist) | structural template |
| [NMS Consulting](https://nmsconsulting.com/day-1-readiness-checklist/) | task category breakdown |
| [Deloitte M&A integration plan](https://www.deloitte.com/us/en/services/consulting/articles/mergers-acquisitions-integration-plan-checklist.html) | dependency layering |
| [Korn Ferry Day-One checklist](https://www.kornferry.com/insights/featured-topics/organizational-transformation/mergers-and-acquisitions-day-one-checklist) | cultural integration framing |
| [M&A Science Day-1 operating model](https://www.mascience.com/plays/day-1-operating-model) | audience cascade structure |

---

## ID conventions

| Prefix | Entity |
|---|---|
| `IP-` | IntegrationPlan (one M&A engagement) |
| `PN-` | PlanNode (Day-1/30/100 task across 4 axes) |
| `DE-` | DependencyEdge (NetworkX edge) |
| `CK-` | CommunicationKit (5-audience cascade) |
| `RS-` | RiskScore (per-node / per-edge, 0-100) |
| `JPD1-` | JP Day-1 culture pattern hit |

---

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-week1.txt

# Launch UI — /api/generate produces a synthetic IntegrationPlan inline (no separate data-gen step)
uvicorn src.api.app:app --reload --port 8000
# → http://localhost:8000/  (landing)
# → http://localhost:8000/api/generate  (synthetic Day-1 plan JSON)

# Optional: ingest output from sibling DD Workbench (mais-dd-workbench)
# python -m src.integration.ingest_t2_output --input <path/to/dd_output.json>
```

---

## Configuration (env)

```bash
ANTHROPIC_API_KEY=sk-ant-...           # required for LLM-driven planning
VAULT_KEY=<fernet key>                  # contact info vault
SYNTHETIC_SEED=20260513
DATA_DIR=./data
```

---

## Production deployment notes

- Real M&A engagement data → sandbox (Docker / WSL2 / Codespaces)
- Customer sandbox dry-run + 1-week stability before cutover
- Sweep 2026 advisories for LangGraph, LlamaIndex, NetworkX
- External penetration test recommended for large engagements

---

## Sibling tools (M&A Intelligence Suite)

- [mais-deal-matching](https://github.com/leagames0221-sys/mais-deal-matching) — sourcing
- [mais-dd-workbench](https://github.com/leagames0221-sys/mais-dd-workbench) — DD
- **[mais-day1-cockpit](https://github.com/leagames0221-sys/mais-day1-cockpit)** ← this repo (Day-1)
- [mais-pmi-cockpit](https://github.com/leagames0221-sys/mais-pmi-cockpit) — 100-day PMI dashboard
- [mais-pmi-knowledge-base](https://github.com/leagames0221-sys/mais-pmi-knowledge-base) — knowledge layer
- [mais-portfolio](https://github.com/leagames0221-sys/mais-portfolio) — overview

---

## License

MIT. See [LICENSE](LICENSE).
