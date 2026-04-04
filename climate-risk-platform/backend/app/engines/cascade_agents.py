"""
MiroFish-inspired Agent Cascade Simulation Engine

Each company/entity in the portfolio becomes an autonomous agent with:
- A persona derived from its sector, location, and risk profile
- Dependencies on other entities (supply chain, insurance, grid, etc.)
- Ability to react to climate events and propagate impacts

The simulation runs rounds where agents react to the initial event,
then react to each other's reactions, creating cascade effects.

Uses Gemini (or any OpenAI-compatible LLM) for agent reasoning.
Falls back to rule-based simulation when no LLM is available.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


# Dependency mapping: what each sector depends on
SECTOR_DEPENDENCIES = {
    "Energy": ["grid", "regulators", "insurers", "suppliers", "transportation"],
    "Utilities": ["grid", "regulators", "insurers", "fuel_suppliers"],
    "Transportation": ["fuel_suppliers", "infrastructure", "insurers", "grid"],
    "Real Estate": ["insurers", "construction", "financing", "utilities"],
    "Agriculture": ["water_supply", "transportation", "insurers", "labor"],
    "Materials": ["energy", "transportation", "regulators", "suppliers"],
    "Technology": ["grid", "supply_chain", "data_centers", "talent"],
    "Financials": ["regulators", "credit_markets", "insurers", "technology"],
    "Healthcare": ["supply_chain", "utilities", "transportation", "regulators"],
    "Consumer Discretionary": ["supply_chain", "transportation", "consumer_confidence"],
    "Consumer Staples": ["supply_chain", "agriculture", "transportation"],
    "Communication Services": ["grid", "infrastructure", "regulators"],
}

# How climate events affect different sectors (impact multiplier 0-1)
EVENT_SECTOR_IMPACT = {
    "hurricane": {"Real Estate": 0.9, "Energy": 0.8, "Transportation": 0.85, "Agriculture": 0.7, "Utilities": 0.8, "Insurance": 0.9},
    "wildfire": {"Real Estate": 0.85, "Agriculture": 0.9, "Utilities": 0.7, "Energy": 0.5, "Healthcare": 0.4},
    "flood": {"Real Estate": 0.9, "Transportation": 0.8, "Agriculture": 0.85, "Energy": 0.6, "Utilities": 0.7},
    "drought": {"Agriculture": 0.95, "Utilities": 0.7, "Energy": 0.6, "Consumer Staples": 0.5},
    "heatwave": {"Agriculture": 0.7, "Energy": 0.8, "Utilities": 0.85, "Healthcare": 0.6, "Transportation": 0.5},
    "carbon_tax": {"Energy": 0.9, "Materials": 0.8, "Transportation": 0.75, "Utilities": 0.7, "Consumer Discretionary": 0.4},
    "emissions_regulation": {"Energy": 0.85, "Materials": 0.8, "Utilities": 0.75, "Transportation": 0.7},
}


@dataclass
class AgentPersona:
    """An entity/company represented as an agent"""
    entity_id: str
    name: str
    sector: str
    region: str
    market_value: float
    combined_score: float
    expected_loss: float
    dependencies: List[str]
    carbon_intensity: float = 0.0
    insurance_dependency: float = 0.0
    supply_chain_dependency: float = 0.0

    @property
    def persona_text(self) -> str:
        return (
            f"You are {self.name}, a {self.sector} company based in {self.region}. "
            f"Your market value is ${self.market_value:,.0f}. "
            f"You depend on: {', '.join(self.dependencies)}. "
            f"Your carbon intensity is {self.carbon_intensity:.0f}, "
            f"insurance dependency is {self.insurance_dependency:.0f}/100, "
            f"and supply chain dependency is {self.supply_chain_dependency:.0f}/100."
        )


@dataclass
class CascadeEvent:
    """A single event in the cascade chain"""
    round_num: int
    source_entity: str
    target_entity: str
    event_type: str  # direct_impact, supply_chain, insurance_cascade, grid_failure, etc.
    description: str
    loss_amount: float
    severity: str  # low, medium, high, critical
    propagation_path: List[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Complete result of a cascade simulation"""
    scenario_description: str
    total_rounds: int
    cascade_events: List[CascadeEvent]
    total_direct_loss: float
    total_cascaded_loss: float
    narrative: str
    affected_entities: List[Dict[str, Any]]
    dependency_chains: List[List[str]]
    recommendations: List[str]


class LLMClient:
    """Lightweight LLM client supporting Gemini and OpenAI-compatible APIs"""

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("LLM_BASE_URL", "")
        self.model = os.environ.get("LLM_MODEL", "")
        self.available = False

        if self.api_key:
            try:
                # Try Gemini first
                if os.environ.get("GEMINI_API_KEY") and not self.base_url:
                    self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
                    self.model = self.model or "gemini-2.0-flash"
                elif not self.base_url:
                    self.base_url = "https://api.openai.com/v1"
                    self.model = self.model or "gpt-4o-mini"

                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                self.available = True
                logger.info(f"LLM client ready: model={self.model}, base_url={self.base_url[:40]}")
            except Exception as e:
                logger.warning(f"LLM client init failed: {e}")
        else:
            logger.info("No LLM API key found, using rule-based cascade simulation")

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> Optional[str]:
        if not self.available:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return None

    def chat_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict]:
        text = self.chat(system_prompt, user_prompt, temperature=0.3)
        if not text:
            return None
        try:
            # Extract JSON from markdown code blocks if present
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response")
            return None


# Singleton LLM client
_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


class CascadeSimulationEngine:
    """
    Runs agent-based cascade simulation inspired by MiroFish.

    Each holding becomes an agent. When a climate event hits:
    1. Direct impact: agents in the affected region/sector take damage
    2. Cascade round 1: damaged agents propagate to their dependencies
    3. Cascade round 2+: secondary effects ripple through the network
    4. LLM narrates what happened (or rule-based fallback)
    """

    def __init__(self):
        self.llm = get_llm_client()

    def build_agents(self, holdings: List[Dict]) -> List[AgentPersona]:
        """Convert portfolio holdings into agent personas"""
        agents = []
        for h in holdings:
            sector = h.get("sector", "Unknown")
            deps = SECTOR_DEPENDENCIES.get(sector, ["suppliers", "regulators"])
            agents.append(AgentPersona(
                entity_id=str(h.get("id", h.get("holding_id", ""))),
                name=h.get("issuer_name", h.get("asset_name", "Unknown")),
                sector=sector,
                region=h.get("state_region") or h.get("country", "Unknown"),
                market_value=float(h.get("market_value", 0)),
                combined_score=float(h.get("combined_score", 50)),
                expected_loss=float(h.get("expected_loss", 0)),
                dependencies=deps,
                carbon_intensity=float(h.get("carbon_intensity_proxy", 0) or 0),
                insurance_dependency=float(h.get("insurance_dependency_score", 0) or 0),
                supply_chain_dependency=float(h.get("supply_chain_dependency_score", 0) or 0),
            ))
        return agents

    def run_simulation(
        self,
        agents: List[AgentPersona],
        event_type: str,
        event_description: str,
        affected_regions: List[str],
        severity: str = "high",
        num_rounds: int = 3,
    ) -> SimulationResult:
        """Run the full cascade simulation"""
        logger.info(f"Starting cascade simulation: {event_type} in {affected_regions}, severity={severity}")

        all_events: List[CascadeEvent] = []
        severity_mult = {"low": 0.3, "medium": 0.6, "high": 1.0, "extreme": 1.5}.get(severity, 1.0)
        event_type_key = event_type.lower().replace(" ", "_")

        # Build dependency graph between agents
        dep_graph = self._build_dependency_graph(agents)

        # Round 0: Direct impact
        direct_events = self._compute_direct_impact(
            agents, event_type_key, affected_regions, severity_mult
        )
        all_events.extend(direct_events)

        # Track cumulative damage per agent
        agent_damage: Dict[str, float] = {}
        for e in direct_events:
            agent_damage[e.target_entity] = agent_damage.get(e.target_entity, 0) + e.loss_amount

        # Rounds 1-N: Cascade propagation
        for round_num in range(1, num_rounds + 1):
            cascade_events = self._propagate_cascade(
                agents, agent_damage, dep_graph, round_num, severity_mult
            )
            if not cascade_events:
                break  # No more propagation
            all_events.extend(cascade_events)
            for e in cascade_events:
                agent_damage[e.target_entity] = agent_damage.get(e.target_entity, 0) + e.loss_amount

        # Calculate totals
        total_direct = sum(e.loss_amount for e in all_events if e.round_num == 0)
        total_cascaded = sum(e.loss_amount for e in all_events if e.round_num > 0)

        # Build affected entities summary
        affected = self._summarize_affected(agents, agent_damage)

        # Extract dependency chains
        chains = self._extract_chains(all_events)

        # Generate narrative
        narrative = self._generate_narrative(
            event_type, event_description, affected_regions, severity,
            all_events, affected, total_direct, total_cascaded
        )

        # Generate recommendations
        recs = self._generate_recommendations(affected, event_type, total_direct + total_cascaded)

        return SimulationResult(
            scenario_description=event_description,
            total_rounds=max((e.round_num for e in all_events), default=0) + 1,
            cascade_events=all_events,
            total_direct_loss=total_direct,
            total_cascaded_loss=total_cascaded,
            narrative=narrative,
            affected_entities=affected,
            dependency_chains=chains,
            recommendations=recs,
        )

    def _build_dependency_graph(self, agents: List[AgentPersona]) -> Dict[str, List[str]]:
        """Build a graph of which agents depend on which other agents"""
        graph: Dict[str, List[str]] = {}
        sector_agents: Dict[str, List[str]] = {}

        for a in agents:
            sector_agents.setdefault(a.sector, []).append(a.name)

        for a in agents:
            dependents = []
            for dep_type in a.dependencies:
                # Map dependency types to sectors
                dep_sector_map = {
                    "grid": "Utilities", "energy": "Energy", "fuel_suppliers": "Energy",
                    "insurers": "Financials", "financing": "Financials", "credit_markets": "Financials",
                    "transportation": "Transportation", "infrastructure": "Transportation",
                    "supply_chain": "Materials", "suppliers": "Materials", "construction": "Materials",
                    "agriculture": "Agriculture", "water_supply": "Utilities",
                    "data_centers": "Technology", "technology": "Technology",
                }
                mapped_sector = dep_sector_map.get(dep_type)
                if mapped_sector and mapped_sector in sector_agents:
                    for dep_name in sector_agents[mapped_sector]:
                        if dep_name != a.name:
                            dependents.append(dep_name)
            graph[a.name] = list(set(dependents))
        return graph

    def _compute_direct_impact(
        self, agents: List[AgentPersona], event_type: str,
        affected_regions: List[str], severity_mult: float
    ) -> List[CascadeEvent]:
        """Compute direct impact on agents in affected regions"""
        events = []
        sector_impacts = EVENT_SECTOR_IMPACT.get(event_type, {})
        normalized_regions = [r.lower() for r in affected_regions]

        # Policy events (carbon_tax, emissions_regulation) affect all regions
        is_policy_event = event_type in ("carbon_tax", "emissions_regulation", "compound")

        for agent in agents:
            if is_policy_event:
                region_match = True  # Policy affects everyone
            else:
                region_match = (
                    not normalized_regions
                    or any(nr in agent.region.lower() for nr in normalized_regions)
                    or "usa" in normalized_regions
                )

            if not region_match:
                continue

            impact_factor = sector_impacts.get(agent.sector, 0.15 if is_policy_event else 0.0)
            if impact_factor == 0:
                continue

            # For policy events, also factor in carbon intensity
            if is_policy_event and agent.carbon_intensity > 0:
                carbon_factor = min(agent.carbon_intensity / 300.0, 1.5)
                impact_factor *= carbon_factor

            loss = agent.market_value * impact_factor * severity_mult * 0.15

            if loss > 0:
                sev = "critical" if impact_factor > 0.7 else "high" if impact_factor > 0.5 else "medium"
                events.append(CascadeEvent(
                    round_num=0,
                    source_entity="Climate Event",
                    target_entity=agent.name,
                    event_type="direct_impact",
                    description=f"Direct {event_type} impact on {agent.name} in {agent.region}",
                    loss_amount=round(loss, 2),
                    severity=sev,
                    propagation_path=["Climate Event", agent.name],
                ))
        return events

    def _propagate_cascade(
        self, agents: List[AgentPersona], agent_damage: Dict[str, float],
        dep_graph: Dict[str, List[str]], round_num: int, severity_mult: float
    ) -> List[CascadeEvent]:
        """Propagate cascade effects through dependency network"""
        events = []
        agent_map = {a.name: a for a in agents}
        damaged_agents = {name for name, dmg in agent_damage.items() if dmg > 0}

        for agent in agents:
            # Check if any of this agent's dependencies are damaged
            deps = dep_graph.get(agent.name, [])
            damaged_deps = [d for d in deps if d in damaged_agents and d != agent.name]

            if not damaged_deps:
                continue

            # Calculate cascade loss based on dependency strength
            dep_factor = min(len(damaged_deps) / max(len(deps), 1), 1.0)
            supply_chain_factor = agent.supply_chain_dependency / 100.0 if agent.supply_chain_dependency else 0.5
            cascade_loss = agent.market_value * dep_factor * supply_chain_factor * 0.05 * severity_mult

            # Diminish with each round
            cascade_loss *= (0.6 ** (round_num - 1))

            if cascade_loss < 10000:  # Skip trivial amounts
                continue

            source = damaged_deps[0]  # Primary source
            event_type = "supply_chain_disruption"
            if any("insur" in d.lower() or "financ" in d.lower() for d in damaged_deps):
                event_type = "insurance_cascade"
            elif any("grid" in d.lower() or "utilit" in d.lower() for d in damaged_deps):
                event_type = "grid_failure_cascade"

            sev = "high" if cascade_loss > agent.market_value * 0.05 else "medium" if cascade_loss > agent.market_value * 0.01 else "low"

            events.append(CascadeEvent(
                round_num=round_num,
                source_entity=source,
                target_entity=agent.name,
                event_type=event_type,
                description=f"{agent.name} affected by cascade from {source} ({event_type})",
                loss_amount=round(cascade_loss, 2),
                severity=sev,
                propagation_path=[source, agent.name],
            ))

        return events

    def _summarize_affected(self, agents: List[AgentPersona], damage: Dict[str, float]) -> List[Dict]:
        """Summarize affected entities"""
        agent_map = {a.name: a for a in agents}
        result = []
        for name, total_loss in sorted(damage.items(), key=lambda x: -x[1]):
            a = agent_map.get(name)
            if a:
                result.append({
                    "entity": name,
                    "sector": a.sector,
                    "region": a.region,
                    "market_value": a.market_value,
                    "total_loss": round(total_loss, 2),
                    "loss_pct": round((total_loss / a.market_value) * 100, 2) if a.market_value > 0 else 0,
                })
        return result

    def _extract_chains(self, events: List[CascadeEvent]) -> List[List[str]]:
        """Extract unique dependency chains from events"""
        chains = []
        seen = set()
        for e in events:
            if e.round_num > 0:
                chain_key = f"{e.source_entity}->{e.target_entity}"
                if chain_key not in seen:
                    seen.add(chain_key)
                    chains.append(e.propagation_path)
        return chains[:20]  # Top 20 chains

    def _generate_narrative(
        self, event_type: str, description: str, regions: List[str],
        severity: str, events: List[CascadeEvent], affected: List[Dict],
        direct_loss: float, cascaded_loss: float
    ) -> str:
        """Generate narrative using LLM or rule-based fallback"""
        if self.llm.available:
            prompt = (
                f"A {severity} {event_type} event has occurred: {description}\n"
                f"Affected regions: {', '.join(regions)}\n\n"
                f"Direct losses: ${direct_loss:,.0f}\n"
                f"Cascade losses: ${cascaded_loss:,.0f}\n"
                f"Total affected entities: {len(affected)}\n\n"
                f"Top 5 affected:\n"
            )
            for a in affected[:5]:
                prompt += f"- {a['entity']} ({a['sector']}, {a['region']}): ${a['total_loss']:,.0f} loss ({a['loss_pct']:.1f}%)\n"

            prompt += (
                f"\nCascade events: {len([e for e in events if e.round_num > 0])}\n"
                f"Write a 3-4 paragraph executive narrative explaining the cascade effects, "
                f"which sectors were most impacted, how dependencies amplified losses, "
                f"and what the key risk drivers are. Be specific about company names and numbers."
            )

            result = self.llm.chat(
                "You are a climate risk analyst writing an executive briefing on cascade effects from a climate event on a financial portfolio.",
                prompt
            )
            if result:
                return result

        # Rule-based fallback
        top3 = affected[:3]
        top_names = ", ".join(a["entity"] for a in top3)
        total = direct_loss + cascaded_loss
        cascade_pct = (cascaded_loss / total * 100) if total > 0 else 0

        return (
            f"A {severity}-severity {event_type} event impacting {', '.join(regions)} has triggered "
            f"significant portfolio losses totaling ${total:,.0f}.\n\n"
            f"Direct impact accounts for ${direct_loss:,.0f}, while cascade effects through "
            f"supply chain disruptions, insurance dependencies, and infrastructure failures "
            f"added ${cascaded_loss:,.0f} ({cascade_pct:.0f}% of total losses).\n\n"
            f"The most affected entities are {top_names}. "
            f"A total of {len(affected)} entities experienced losses, with cascade effects "
            f"propagating through {len([e for e in events if e.round_num > 0])} secondary events "
            f"across {len(set(a['sector'] for a in affected))} sectors.\n\n"
            f"Key risk amplifiers include high supply chain dependencies in the {top3[0]['sector'] if top3 else 'affected'} "
            f"sector and geographic concentration in {', '.join(regions)}."
        )

    def _generate_recommendations(self, affected: List[Dict], event_type: str, total_loss: float) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        if affected:
            top = affected[0]
            recs.append(f"Reduce exposure to {top['entity']} ({top['sector']}) — highest loss at ${top['total_loss']:,.0f}")

        sectors = {}
        for a in affected:
            sectors.setdefault(a["sector"], 0)
            sectors[a["sector"]] += a["total_loss"]
        if sectors:
            worst_sector = max(sectors, key=sectors.get)
            recs.append(f"Diversify away from {worst_sector} sector — ${sectors[worst_sector]:,.0f} in cascade losses")

        regions = {}
        for a in affected:
            regions.setdefault(a["region"], 0)
            regions[a["region"]] += a["total_loss"]
        if regions:
            worst_region = max(regions, key=regions.get)
            recs.append(f"Reduce geographic concentration in {worst_region} — ${regions[worst_region]:,.0f} exposure")

        high_insurance = [a for a in affected if a["loss_pct"] > 10]
        if high_insurance:
            recs.append(f"Review insurance coverage for {len(high_insurance)} entities with >10% loss ratios")

        recs.append("Establish supply chain redundancy for critical dependencies identified in cascade analysis")
        return recs
