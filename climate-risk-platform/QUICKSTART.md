# Climate Risk Intelligence Platform — Quickstart

## What This Is

An agent-based climate risk simulation platform inspired by [MiroFish](https://github.com/MiroFish). You describe a climate event in plain English — "Category 5 hurricane hits the Texas Gulf Coast" or "all silicon disappears" — and the platform:

1. **Parses the event** using an LLM (or keyword fallback) to identify the disaster type, affected regions, and impacted sectors
2. **Dynamically generates company agents** relevant to the disaster (ExxonMobil for Texas hurricanes, PG&E for California wildfires, etc.)
3. **Builds a knowledge graph** (networkx) of company dependencies — who supplies whom, who insures whom, who powers whom
4. **Runs cascade simulation** where damage propagates through the dependency network across multiple rounds
5. **Each agent reasons independently** using graph RAG — the LLM sees the agent's neighborhood in the knowledge graph (direct deps, indirect deps, damage state) and decides its own cascade loss
6. **Generates narrative + recommendations** explaining what happened and what to do about it

---

## Setup (2 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend

```bash
cd climate-risk-platform/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Key

Create `climate-risk-platform/backend/.env`:

```env
GEMINI_API_KEY=your-key-here
```

Get a free Gemini key at https://aistudio.google.com/apikey

> **Without a key**, the platform still works — event parsing uses keyword matching, agents use rule-based math, and narratives are template-based. With a key, you get LLM-powered event understanding, per-agent reasoning with graph RAG context, and rich narratives.

### 3. Frontend

```bash
cd climate-risk-platform/frontend
npm install
```

---

## Run

Terminal 1 — Backend:
```bash
cd climate-risk-platform/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — Frontend:
```bash
cd climate-risk-platform/frontend
npm run dev
```

Open http://localhost:3000/dashboard

---

## How To Use

1. The platform auto-seeds a portfolio with 50 real companies on first run
2. Type any climate/economic event in the search bar, or click a quick scenario button
3. Watch the simulation results:
   - **Agent Network** — interactive graph showing companies and their dependency connections. Larger nodes = more loss. Dashed rings = portfolio holdings. Click any node to see details.
   - **Timeline** — cascade events grouped by round, showing how damage propagates
   - **Narrative** — LLM-generated executive briefing (or rule-based summary)
   - **Affected Entities** — sortable table of all impacted companies with loss amounts
   - **Recommendations** — actionable portfolio actions

### Example Scenarios

| Input | What Happens |
|---|---|
| "Category 5 hurricane hits Texas Gulf Coast" | Generates ExxonMobil, CenterPoint Energy, ERCOT, Valero, etc. Cascade through energy → utilities → transportation |
| "Massive wildfire in Northern California" | Generates PG&E, Chevron, Prologis, Driscoll's. Cascade through utilities → real estate → agriculture |
| "All silicon disappears from earth" | LLM parses as supply_shock → Technology, Materials, Consumer Discretionary. Generates Apple, NVIDIA, Dell, etc. |
| "Federal carbon tax of $200/ton" | Policy event → hits all high-carbon sectors nationwide. Energy and Materials take heaviest losses |

---

## Architecture

```
User types event
       │
       ▼
┌─────────────────┐
│  Event Parser   │  LLM or keyword fallback
│  (simulate.py)  │  → event_type, regions, affected_sectors
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Dynamic Agent Builder  │  Portfolio holdings + disaster-relevant companies
│  (cascade_agents.py)    │  from COMPANIES_BY_SECTOR_REGION registry
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Knowledge Graph (RAG)  │  networkx DiGraph
│  CompanyKnowledgeGraph  │  nodes = companies, edges = dependencies
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Cascade Simulation     │  Round 0: direct impact
│  CascadeSimulationEngine│  Round 1-N: propagation with per-agent LLM reasoning
└────────┬────────────────┘  Each agent gets graph RAG context in its prompt
         │
         ▼
┌─────────────────────────┐
│  Results                │  Events, affected entities, narrative, recommendations
│  → Frontend             │  Agent network graph, timeline, tables
└─────────────────────────┘
```

### MiroFish Pattern

This follows the MiroFish philosophy:

| MiroFish | Our Implementation |
|---|---|
| Text → Zep Knowledge Graph | Company registry + networkx `CompanyKnowledgeGraph` |
| Zep graph search enriches agent context | `get_agent_context()` — 2-hop neighborhood walk with damage state |
| Each agent gets own LLM call with persona | `_agent_llm_reasoning()` — system prompt includes graph RAG context |
| OASIS social simulation rounds | Cascade rounds with dependency propagation |
| Results stored back to graph | Damage accumulates across rounds, fed back into graph queries |

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/simulate/run` | POST | Run cascade simulation |
| `/api/portfolios` | GET | List portfolios |
| `/api/portfolios/{id}` | GET | Portfolio details |
| `/api/portfolios/sample/create` | POST | Create sample portfolio |

### Simulation Request

```json
{
  "portfolio_id": "uuid",
  "event_description": "Category 5 hurricane hits Texas Gulf Coast",
  "severity": "high",
  "num_rounds": 3
}
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | No* | Google Gemini API key (free at aistudio.google.com/apikey) |
| `OPENAI_API_KEY` | No* | OpenAI API key (alternative to Gemini) |
| `LLM_BASE_URL` | No | Custom LLM endpoint (for local models) |
| `LLM_MODEL` | No | Custom model name |
| `DATABASE_URL` | No | Defaults to SQLite (zero setup) |

*Without any LLM key, the platform works with rule-based fallback. With a key, you get intelligent event parsing, per-agent graph RAG reasoning, and rich narratives.
