"""
Free-form climate event simulation API

Users describe a climate event in natural language (e.g., "Category 5 hurricane
hits Houston, Texas") and the system runs an agent-based cascade simulation
showing how the event propagates through the portfolio.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging
import re

from app.database import get_db
from app.models.holding import Holding
from app.models.risk_result import RiskResult
from app.engines.cascade_agents import CascadeSimulationEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simulate", tags=["simulate"])


class SimulationRequest(BaseModel):
    """Free-form simulation request"""
    portfolio_id: str
    event_description: str
    severity: str = "high"
    num_rounds: int = 3
    num_companies: int = 15  # How many companies to simulate

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "some-uuid",
                "event_description": "Category 5 hurricane hits the Texas Gulf Coast, causing massive flooding and infrastructure damage",
                "severity": "high",
                "num_rounds": 3,
            }
        }


def parse_event(description: str) -> dict:
    """
    Parse event description using LLM first, keyword fallback second.

    The LLM can understand arbitrary scenarios like "all silicon disappears"
    and map them to affected sectors, regions, and an event type.
    """
    from app.engines.cascade_agents import get_llm_client
    import json as _json

    llm = get_llm_client()

    # --- Try LLM-based parsing first ---
    if llm.available:
        try:
            system = (
                "You parse climate/economic/supply-chain event descriptions into structured JSON. "
                "Return ONLY valid JSON with these keys:\n"
                '  "event_type": one of hurricane, wildfire, flood, drought, heatwave, '
                "carbon_tax, emissions_regulation, supply_shock, pandemic, cyberattack, compound\n"
                '  "regions": list of US state names affected (use [] for global/nationwide)\n'
                '  "affected_sectors": list of sectors impacted, from: Energy, Utilities, '
                "Real Estate, Transportation, Agriculture, Materials, Technology, Financials, "
                "Healthcare, Consumer Discretionary, Consumer Staples, Communication Services\n"
                '  "sector_impact": dict mapping sector name to impact severity 0.0-1.0\n'
                '  "reasoning": one sentence explaining your interpretation\n'
            )
            user = f"Event: {description}"
            raw = llm.chat(system, user, temperature=0.2)
            if raw:
                # Strip markdown fences if present
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                parsed = _json.loads(cleaned)
                result = {
                    "event_type": parsed.get("event_type", "compound"),
                    "regions": parsed.get("regions", ["USA"]) or ["USA"],
                    "affected_sectors": parsed.get("affected_sectors", []),
                    "sector_impact": parsed.get("sector_impact", {}),
                    "reasoning": parsed.get("reasoning", ""),
                }
                logger.info(f"LLM parsed event: {result['event_type']}, "
                            f"regions={result['regions']}, "
                            f"sectors={result['affected_sectors']}, "
                            f"reasoning={result['reasoning']}")
                return result
        except Exception as e:
            logger.warning(f"LLM event parsing failed, falling back to keywords: {e}")

    # --- Keyword fallback ---
    desc_lower = description.lower()

    event_type = "compound"
    type_keywords = {
        "hurricane": ["hurricane", "cyclone", "tropical storm", "typhoon"],
        "wildfire": ["wildfire", "fire", "blaze", "burn"],
        "flood": ["flood", "flooding", "storm surge", "deluge"],
        "drought": ["drought", "dry", "water shortage", "arid"],
        "heatwave": ["heatwave", "heat wave", "extreme heat", "heat dome"],
        "carbon_tax": ["carbon tax", "carbon price", "carbon levy"],
        "emissions_regulation": ["emission", "regulation", "epa", "clean air"],
        "supply_shock": ["silicon", "chip", "semiconductor", "shortage", "supply chain",
                         "rare earth", "lithium", "cobalt", "disappear"],
    }
    for etype, keywords in type_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            event_type = etype
            break

    us_states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming",
    ]
    regions_found = []
    for state in us_states:
        if state.lower() in desc_lower:
            regions_found.append(state)

    region_aliases = {
        "gulf coast": ["Texas", "Louisiana", "Florida"],
        "east coast": ["New York", "New Jersey", "Virginia", "North Carolina"],
        "west coast": ["California", "Oregon", "Washington"],
        "midwest": ["Iowa", "Illinois", "Missouri", "Nebraska"],
        "southeast": ["Georgia", "South Carolina", "North Carolina", "Florida"],
        "southwest": ["Arizona", "New Mexico", "Nevada"],
        "pacific northwest": ["Oregon", "Washington"],
        "new england": ["Massachusetts", "Connecticut", "Maine"],
        "houston": ["Texas"],
        "miami": ["Florida"],
        "los angeles": ["California"],
        "new york city": ["New York"],
        "chicago": ["Illinois"],
    }
    for alias, states in region_aliases.items():
        if alias in desc_lower:
            regions_found.extend(states)

    regions_found = list(set(regions_found))
    if not regions_found:
        regions_found = ["USA"]

    return {
        "event_type": event_type,
        "regions": regions_found,
    }


@router.post("/run")
async def run_cascade_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Run agent-based cascade simulation for a free-form climate event.

    Each company in the portfolio becomes an agent. The simulation:
    1. Parses the event description to identify type and affected regions
    2. Computes direct impact on agents in those regions
    3. Propagates cascade effects through supply chain and dependency networks
    4. Generates a narrative explaining what happened
    """
    # Get holdings for portfolio
    holdings = db.query(Holding).filter(
        Holding.portfolio_id == request.portfolio_id
    ).all()

    if not holdings:
        raise HTTPException(status_code=404, detail="No holdings found for this portfolio")

    # Convert to dicts
    holdings_data = []
    for h in holdings:
        holdings_data.append({
            "id": str(h.id),
            "asset_name": h.asset_name,
            "issuer_name": h.issuer_name,
            "sector": h.sector,
            "country": h.country,
            "state_region": h.state_region,
            "market_value": float(h.market_value),
            "carbon_intensity_proxy": float(h.carbon_intensity_proxy) if h.carbon_intensity_proxy else 0,
            "insurance_dependency_score": float(h.insurance_dependency_score) if h.insurance_dependency_score else 0,
            "supply_chain_dependency_score": float(h.supply_chain_dependency_score) if h.supply_chain_dependency_score else 0,
        })

    # Parse event (LLM-powered when available, keyword fallback)
    parsed = parse_event(request.event_description)

    # Run simulation - build_agents dynamically generates companies
    # relevant to the disaster type and region, not just portfolio holdings
    engine = CascadeSimulationEngine()
    agents = engine.build_agents(
        holdings_data,
        event_type=parsed["event_type"],
        affected_regions=parsed["regions"],
        event_description=request.event_description,
        num_companies=request.num_companies,
    )
    result = engine.run_simulation(
        agents=agents,
        event_type=parsed["event_type"],
        event_description=request.event_description,
        affected_regions=parsed["regions"],
        severity=request.severity,
        num_rounds=request.num_rounds,
        llm_sector_impact=parsed.get("sector_impact"),
        llm_affected_sectors=parsed.get("affected_sectors"),
    )

    return {
        "scenario": request.event_description,
        "event_type": parsed["event_type"],
        "affected_regions": parsed["regions"],
        "severity": request.severity,
        "event_reasoning": parsed.get("reasoning", ""),
        "simulation_rounds": result.total_rounds,
        "total_direct_loss": result.total_direct_loss,
        "total_cascaded_loss": result.total_cascaded_loss,
        "total_loss": result.total_direct_loss + result.total_cascaded_loss,
        "cascade_amplification": round(
            (result.total_cascaded_loss / result.total_direct_loss * 100) if result.total_direct_loss > 0 else 0, 1
        ),
        "narrative": result.narrative,
        "cascade_events": [
            {
                "round": e.round_num,
                "source": e.source_entity,
                "target": e.target_entity,
                "type": e.event_type,
                "description": e.description,
                "loss": e.loss_amount,
                "severity": e.severity,
            }
            for e in result.cascade_events
        ],
        "affected_entities": result.affected_entities,
        "dependency_chains": result.dependency_chains,
        "recommendations": result.recommendations,
    }
