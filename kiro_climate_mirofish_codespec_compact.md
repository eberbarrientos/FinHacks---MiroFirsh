# Compact Code Spec — Climate Risk Intelligence + MiroFish

## 1. Objective
Build a polished climate risk intelligence platform for financial institutions that:
- measures climate exposure for assets, companies, and portfolios
- estimates financial loss under physical and policy scenarios
- runs stress tests
- uses **MiroFish** to simulate dependency cascades and narrative what-if outcomes
- delivers a **premium visual dashboard** as the primary product experience

**Architecture rule:** core risk math lives in our backend; MiroFish is the orchestration / dependency simulation layer.

---

## 2. Product Output
The app must produce:
1. portfolio climate risk score
2. asset/company risk breakdown
3. expected loss under selected scenarios
4. geographic risk map
5. sector and issuer concentration views
6. MiroFish-driven cascade summary
7. actionable portfolio recommendations

---

## 3. UX Priority
This product should feel like **Bloomberg x Palantir x modern AI copilot**.

### Visual requirements
- dark mode default
- glassmorphism cards, subtle blur, thin borders
- premium spacing, rounded 2xl corners, soft shadows
- cyan/teal/emerald/amber/red accents for risk states
- elegant typography with big numbers and compact annotations
- tasteful motion only: counters, map pulses, hover reveals, smooth scenario transitions

### Main dashboard layout
- **Top bar:** portfolio selector, scenario selector, date, export button
- **Hero stats row:** portfolio value, climate VaR, stressed drawdown, top hotspot, top sector risk
- **Center:** large interactive map with risk overlays
- **Right rail:** MiroFish cascade panel + top issuers at risk
- **Bottom:** loss waterfall, sector heatmap, scenario compare chart, dependency graph, recommendations

### Non-negotiables
- map is visually stunning
- loading states are premium
- empty states still look intentional
- scenario compare feels cinematic and fast

---

## 4. Core Modules

### A. Portfolio Intake
Accept CSV/manual/sample data.
Required fields:
- `asset_id`
- `asset_name`
- `asset_type`
- `issuer_name`
- `sector`
- `country`
- `state_region`
- `latitude`
- `longitude`
- `market_value`
- `revenue_exposure_pct` (optional)
- `carbon_intensity_proxy` (optional)
- `insurance_dependency_score` (optional)
- `supply_chain_dependency_score` (optional)

### B. Climate Exposure Engine
Compute:
- physical hazard score
- transition/policy risk score
- combined climate risk score

### C. Financial Impact Engine
Compute:
- asset expected loss
- issuer aggregated loss
- portfolio stressed drawdown
- sector concentration risk
- geography concentration risk

### D. Scenario Engine
Support:
- hurricane
- wildfire
- drought
- heatwave
- flood
- carbon tax / emissions regulation
- compound scenarios

### E. MiroFish Adapter
Input:
- structured scenario packet
- affected entities
- dependency seeds
- issuer / sector / geography metrics
Output:
- cascade events
- dependency narrative
- propagated impact summary
- qualitative uncertainty notes

### F. Recommendation Engine
Return:
- rebalance suggestions
- hedge / diversify suggestions
- hotspot reduction suggestions
- issuer watchlist
- resilience / insurance review flags

---

## 5. High-Level Architecture

### Frontend
- Next.js 15+
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- Mapbox GL or deck.gl
- Recharts or ECharts
- Zustand for UI state

### Backend
- FastAPI
- Python 3.11+
- Pydantic
- pandas / numpy
- networkx for dependency graphs
- PostgreSQL
- Redis for caching / async jobs

### Services
1. `ingestion-service`
2. `risk-engine`
3. `scenario-engine`
4. `mirofish-adapter`
5. `recommendation-engine`
6. `reporting-service`

---

## 6. Data Model

### Tables

#### portfolios
- id
- name
- base_currency
- created_at

#### holdings
- id
- portfolio_id
- asset_id
- asset_name
- asset_type
- issuer_name
- sector
- country
- state_region
- latitude
- longitude
- market_value
- revenue_exposure_pct
- carbon_intensity_proxy
- insurance_dependency_score
- supply_chain_dependency_score

#### scenarios
- id
- name
- scenario_type
- parameters_json
- created_at

#### risk_results
- id
- portfolio_id
- holding_id
- scenario_id
- physical_score
- transition_score
- combined_score
- expected_loss
- stressed_return_delta
- confidence

#### mirofish_runs
- id
- scenario_id
- status
- input_json
- output_json
- created_at

#### recommendations
- id
- portfolio_id
- scenario_id
- recommendation_type
- priority
- message

---

## 7. Calculation Logic
Use simple but defensible prototype formulas.

### 7.1 Physical hazard score
For each hazard:
`hazard_component = hazard_intensity * geographic_vulnerability * asset_sensitivity`

Then:
`physical_score = weighted_sum(all hazard_component values)`

Example hazard weights:
- flood 0.25
- hurricane 0.20
- wildfire 0.20
- heatwave 0.15
- drought 0.10
- storm / other 0.10

### 7.2 Transition risk score
`transition_score = carbon_weight + sector_policy_weight + regulation_weight + supply_chain_weight`

Normalize to 0–100.

### 7.3 Combined score
`combined_score = 0.65 * physical_score + 0.35 * transition_score`

### 7.4 Expected loss
`expected_loss = market_value * damage_ratio * business_interruption_factor * insurance_gap_factor`

### 7.5 Portfolio climate VaR proxy
`portfolio_climate_var = sum(expected_loss across portfolio under scenario)`

### 7.6 Concentration penalties
Add penalties if portfolio is overly concentrated by:
- geography
- issuer
- sector
- hazard type

---

## 8. Scenario Packet Sent to MiroFish
```json
{
  "scenario": {
    "type": "hurricane+carbon_tax",
    "severity": "high",
    "time_horizon": "12m"
  },
  "portfolio": {
    "portfolio_id": "p1",
    "value": 250000000
  },
  "entities": [
    {
      "issuer": "Example Energy Co",
      "sector": "Utilities",
      "region": "Texas Gulf",
      "combined_score": 78,
      "expected_loss": 12500000,
      "dependencies": ["insurers", "grid", "regulators", "suppliers"]
    }
  ],
  "questions": [
    "What second-order cascades are likely?",
    "Which entities amplify portfolio loss?",
    "What mitigation actions matter most?"
  ]
}
```

MiroFish output should be stored as structured JSON plus display-ready narrative text.

---

## 9. API Surface

### Portfolio
- `POST /api/portfolios`
- `POST /api/portfolios/{id}/upload-holdings`
- `GET /api/portfolios/{id}`
- `GET /api/portfolios/{id}/holdings`

### Risk
- `POST /api/risk/run`
- `GET /api/risk/results?portfolio_id=&scenario_id=`
- `GET /api/risk/summary?portfolio_id=&scenario_id=`

### Scenarios
- `GET /api/scenarios/templates`
- `POST /api/scenarios`
- `POST /api/scenarios/{id}/stress-test`

### MiroFish
- `POST /api/mirofish/run`
- `GET /api/mirofish/run/{id}`

### Recommendations
- `GET /api/recommendations?portfolio_id=&scenario_id=`

### Reports
- `GET /api/reports/executive?portfolio_id=&scenario_id=`

---

## 10. Frontend Routes
- `/` → landing / demo portfolio
- `/dashboard` → main portfolio dashboard
- `/portfolio/[id]` → portfolio detail
- `/scenario/[id]` → scenario analysis
- `/compare` → side-by-side scenario compare
- `/issuer/[name]` → issuer drill-down

---

## 11. Required Components
- `TopNav`
- `ScenarioSelector`
- `PortfolioStatsRow`
- `ClimateRiskMap`
- `IssuerRiskTable`
- `LossWaterfallChart`
- `SectorHeatmap`
- `DependencyGraphPanel`
- `MiroFishNarrativePanel`
- `RecommendationsPanel`
- `UploadPortfolioModal`
- `PremiumLoader`

---

## 12. Dashboard Behavior
When a user selects a scenario:
1. optimistic skeleton loaders appear immediately
2. stats animate in first
3. map risk layers update next
4. charts crossfade to new data
5. MiroFish panel streams / reveals cascade summary last

Clicking a hotspot on the map should filter the rest of the dashboard to that geography.
Clicking an issuer should open issuer drill-down with direct + propagated risk.

---

## 13. Repo Structure
```text
climate-risk-platform/
  frontend/
    app/
    components/
    lib/
    store/
  backend/
    app/
      api/
      models/
      schemas/
      services/
      engines/
      adapters/
      utils/
  shared/
    scenario_schemas/
    types/
```

---

## 14. Implementation Order

### Phase 1 — Foundation
- scaffold frontend + backend
- portfolio upload
- sample portfolio seed
- basic dashboard shell

### Phase 2 — Risk Engine
- exposure scoring
- expected loss scoring
- portfolio summary endpoints
- charts + map integration

### Phase 3 — Scenarios
- predefined scenario templates
- rerun risk under selected scenario
- scenario compare mode

### Phase 4 — MiroFish
- build adapter
- send scenario packets
- render cascade narrative + dependency graph

### Phase 5 — Polish
- premium motion
- exportable executive report
- empty/loading/error states
- performance tuning

---

## 15. Acceptance Criteria
The prototype is successful if it can:
- ingest a sample portfolio
- compute per-holding and portfolio risk
- run at least 4 scenario types
- show map + charts + recommendations
- integrate one working MiroFish scenario call path
- compare two scenarios visually
- look polished enough to demo to judges or executives

---

## 16. Build Philosophy for Kiro
- prefer clean modular code over hacks
- keep formulas explicit and editable
- separate visual components from business logic
- treat MiroFish as an adapter boundary
- optimize the dashboard experience heavily
- make the MVP feel premium even with simple models

