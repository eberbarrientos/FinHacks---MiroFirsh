"""
MiroFish-inspired Agent Cascade Simulation Engine

Dynamically generates company agents RELEVANT to the disaster type and region.
A hurricane in Texas creates agents for Texas energy companies, Gulf Coast
shipping, Houston real estate, etc. - not random unrelated companies.

Each company agent has:
- A persona derived from its sector, location, and risk profile
- Dependencies on other entities (supply chain, insurance, grid, etc.)
- Ability to react to climate events and propagate impacts

Uses Gemini (or any OpenAI-compatible LLM) for agent reasoning.
Falls back to rule-based simulation when no LLM is available.
"""

import json
import logging
import os
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Real-world company registry keyed by (sector, region/state)
# When a disaster hits a region we pull the companies that actually operate
# there, plus their cross-sector dependencies.
# ---------------------------------------------------------------------------

COMPANIES_BY_SECTOR_REGION: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "Energy": {
        "Texas": [
            {"name": "ExxonMobil", "type": "Oil & Gas", "hq": "Houston", "value": 450_000_000, "carbon": 480, "ins": 70, "sc": 85},
            {"name": "ConocoPhillips", "type": "Oil & Gas", "hq": "Houston", "value": 140_000_000, "carbon": 420, "ins": 68, "sc": 80},
            {"name": "Phillips 66", "type": "Refining", "hq": "Houston", "value": 55_000_000, "carbon": 380, "ins": 65, "sc": 88},
            {"name": "Valero Energy", "type": "Refining", "hq": "San Antonio", "value": 48_000_000, "carbon": 400, "ins": 67, "sc": 85},
            {"name": "Marathon Petroleum", "type": "Refining", "hq": "Texas City", "value": 60_000_000, "carbon": 390, "ins": 66, "sc": 84},
            {"name": "Kinder Morgan", "type": "Pipelines", "hq": "Houston", "value": 42_000_000, "carbon": 310, "ins": 60, "sc": 78},
            {"name": "Enterprise Products", "type": "Midstream", "hq": "Houston", "value": 65_000_000, "carbon": 290, "ins": 62, "sc": 82},
        ],
        "Louisiana": [
            {"name": "Entergy Louisiana", "type": "Electric Utility", "hq": "New Orleans", "value": 22_000_000, "carbon": 270, "ins": 72, "sc": 75},
            {"name": "Cheniere Energy", "type": "LNG", "hq": "Sabine Pass", "value": 38_000_000, "carbon": 350, "ins": 68, "sc": 80},
        ],
        "Oklahoma": [
            {"name": "Devon Energy", "type": "Oil & Gas", "hq": "Oklahoma City", "value": 30_000_000, "carbon": 350, "ins": 64, "sc": 75},
            {"name": "Continental Resources", "type": "Oil & Gas", "hq": "Oklahoma City", "value": 25_000_000, "carbon": 340, "ins": 62, "sc": 72},
        ],
        "North Dakota": [
            {"name": "Hess Corporation", "type": "Oil & Gas", "hq": "Williston Basin", "value": 35_000_000, "carbon": 360, "ins": 60, "sc": 70},
        ],
        "California": [
            {"name": "Chevron", "type": "Oil & Gas", "hq": "San Ramon", "value": 300_000_000, "carbon": 450, "ins": 72, "sc": 82},
            {"name": "Occidental Petroleum", "type": "Oil & Gas", "hq": "Los Angeles", "value": 55_000_000, "carbon": 410, "ins": 69, "sc": 78},
        ],
        "Wyoming": [
            {"name": "Arch Resources", "type": "Coal", "hq": "Gillette", "value": 18_000_000, "carbon": 550, "ins": 55, "sc": 70},
        ],
        "_default": [
            {"name": "EOG Resources", "type": "Oil & Gas", "hq": "Houston", "value": 70_000_000, "carbon": 330, "ins": 60, "sc": 70},
            {"name": "Pioneer Natural Resources", "type": "Oil & Gas", "hq": "Midland", "value": 55_000_000, "carbon": 340, "ins": 62, "sc": 72},
        ],
    },
    "Utilities": {
        "Texas": [
            {"name": "CenterPoint Energy", "type": "Electric Utility", "hq": "Houston", "value": 20_000_000, "carbon": 250, "ins": 65, "sc": 72},
            {"name": "Oncor Electric", "type": "Electric Utility", "hq": "Dallas", "value": 18_000_000, "carbon": 230, "ins": 60, "sc": 70},
            {"name": "ERCOT Grid Operator", "type": "Grid Operator", "hq": "Austin", "value": 0, "carbon": 200, "ins": 50, "sc": 95},
        ],
        "California": [
            {"name": "Pacific Gas & Electric", "type": "Electric Utility", "hq": "San Francisco", "value": 35_000_000, "carbon": 180, "ins": 80, "sc": 75},
            {"name": "Southern California Edison", "type": "Electric Utility", "hq": "Rosemead", "value": 28_000_000, "carbon": 170, "ins": 78, "sc": 72},
            {"name": "San Diego Gas & Electric", "type": "Electric Utility", "hq": "San Diego", "value": 15_000_000, "carbon": 160, "ins": 75, "sc": 68},
        ],
        "Florida": [
            {"name": "Florida Power & Light", "type": "Electric Utility", "hq": "Juno Beach", "value": 30_000_000, "carbon": 200, "ins": 82, "sc": 74},
            {"name": "Duke Energy Florida", "type": "Electric Utility", "hq": "St. Petersburg", "value": 22_000_000, "carbon": 220, "ins": 78, "sc": 70},
        ],
        "Arizona": [
            {"name": "Arizona Public Service", "type": "Electric Utility", "hq": "Phoenix", "value": 18_000_000, "carbon": 240, "ins": 60, "sc": 68},
            {"name": "Salt River Project", "type": "Water & Power", "hq": "Phoenix", "value": 12_000_000, "carbon": 200, "ins": 55, "sc": 72},
        ],
        "_default": [
            {"name": "NextEra Energy", "type": "Electric Utility", "hq": "Juno Beach", "value": 45_000_000, "carbon": 120, "ins": 55, "sc": 65},
            {"name": "Duke Energy", "type": "Electric Utility", "hq": "Charlotte", "value": 38_000_000, "carbon": 280, "ins": 60, "sc": 70},
            {"name": "Southern Company", "type": "Electric Utility", "hq": "Atlanta", "value": 32_000_000, "carbon": 300, "ins": 62, "sc": 72},
        ],
    },
    "Real Estate": {
        "Florida": [
            {"name": "St. Joe Company", "type": "Coastal RE", "hq": "Panama City Beach", "value": 8_000_000, "carbon": 40, "ins": 92, "sc": 45},
            {"name": "Consolidated-Tomoka", "type": "Diversified RE", "hq": "Daytona Beach", "value": 6_000_000, "carbon": 35, "ins": 88, "sc": 40},
            {"name": "Armada Hoffler", "type": "Mixed-Use RE", "hq": "Miami", "value": 12_000_000, "carbon": 50, "ins": 90, "sc": 50},
        ],
        "Texas": [
            {"name": "Camden Property Trust", "type": "Residential REIT", "hq": "Houston", "value": 14_000_000, "carbon": 45, "ins": 75, "sc": 42},
            {"name": "Whitestone REIT", "type": "Retail REIT", "hq": "Houston", "value": 5_000_000, "carbon": 38, "ins": 70, "sc": 40},
        ],
        "California": [
            {"name": "Prologis", "type": "Industrial REIT", "hq": "San Francisco", "value": 55_000_000, "carbon": 45, "ins": 70, "sc": 40},
            {"name": "Essex Property Trust", "type": "Residential REIT", "hq": "San Mateo", "value": 18_000_000, "carbon": 38, "ins": 72, "sc": 38},
            {"name": "Kilroy Realty", "type": "Office REIT", "hq": "Los Angeles", "value": 12_000_000, "carbon": 42, "ins": 68, "sc": 42},
        ],
        "_default": [
            {"name": "Simon Property Group", "type": "Retail REIT", "hq": "Indianapolis", "value": 42_000_000, "carbon": 55, "ins": 75, "sc": 50},
            {"name": "AvalonBay Communities", "type": "Residential REIT", "hq": "Arlington", "value": 28_000_000, "carbon": 38, "ins": 80, "sc": 35},
        ],
    },
    "Transportation": {
        "Texas": [
            {"name": "Southwest Airlines", "type": "Airlines", "hq": "Dallas", "value": 22_000_000, "carbon": 260, "ins": 68, "sc": 82},
            {"name": "BNSF Railway (Texas)", "type": "Railroad", "hq": "Fort Worth", "value": 35_000_000, "carbon": 180, "ins": 55, "sc": 90},
        ],
        "Florida": [
            {"name": "Carnival Corporation", "type": "Cruise Lines", "hq": "Miami", "value": 25_000_000, "carbon": 320, "ins": 85, "sc": 78},
            {"name": "Royal Caribbean", "type": "Cruise Lines", "hq": "Miami", "value": 22_000_000, "carbon": 310, "ins": 82, "sc": 75},
        ],
        "California": [
            {"name": "Union Pacific (West)", "type": "Railroad", "hq": "Los Angeles", "value": 30_000_000, "carbon": 180, "ins": 55, "sc": 90},
        ],
        "_default": [
            {"name": "FedEx", "type": "Logistics", "hq": "Memphis", "value": 65_000_000, "carbon": 220, "ins": 60, "sc": 95},
            {"name": "UPS", "type": "Logistics", "hq": "Atlanta", "value": 60_000_000, "carbon": 210, "ins": 58, "sc": 94},
            {"name": "CSX Corporation", "type": "Railroad", "hq": "Jacksonville", "value": 35_000_000, "carbon": 175, "ins": 52, "sc": 88},
            {"name": "Norfolk Southern", "type": "Railroad", "hq": "Atlanta", "value": 30_000_000, "carbon": 170, "ins": 54, "sc": 87},
        ],
    },
    "Financials": {
        "Texas": [
            {"name": "Culberson Bankers", "type": "Regional Bank", "hq": "Houston", "value": 8_000_000, "carbon": 12, "ins": 40, "sc": 30},
        ],
        "Florida": [
            {"name": "Citizens Property Insurance", "type": "State Insurer", "hq": "Tallahassee", "value": 15_000_000, "carbon": 8, "ins": 20, "sc": 25},
        ],
        "_default": [
            {"name": "JPMorgan Chase", "type": "Banking", "hq": "New York", "value": 500_000_000, "carbon": 15, "ins": 40, "sc": 35},
            {"name": "Bank of America", "type": "Banking", "hq": "Charlotte", "value": 300_000_000, "carbon": 14, "ins": 38, "sc": 32},
            {"name": "Chubb", "type": "Insurance", "hq": "Zurich", "value": 85_000_000, "carbon": 10, "ins": 20, "sc": 25},
            {"name": "Berkshire Hathaway", "type": "Conglomerate", "hq": "Omaha", "value": 750_000_000, "carbon": 85, "ins": 30, "sc": 55},
        ],
    },
    "Agriculture": {
        "California": [
            {"name": "Wonderful Company", "type": "Agriculture", "hq": "Los Angeles", "value": 12_000_000, "carbon": 120, "ins": 65, "sc": 80},
            {"name": "Driscoll's", "type": "Berry Farming", "hq": "Watsonville", "value": 8_000_000, "carbon": 80, "ins": 70, "sc": 75},
        ],
        "Iowa": [
            {"name": "Archer-Daniels-Midland", "type": "Ag Processing", "hq": "Decatur", "value": 45_000_000, "carbon": 180, "ins": 65, "sc": 90},
            {"name": "Corteva Agriscience", "type": "Ag Chemicals", "hq": "Indianapolis", "value": 35_000_000, "carbon": 120, "ins": 55, "sc": 82},
        ],
        "Nebraska": [
            {"name": "Cargill (Midwest)", "type": "Ag Trading", "hq": "Omaha", "value": 40_000_000, "carbon": 200, "ins": 60, "sc": 95},
        ],
        "Arizona": [
            {"name": "Shamrock Farms", "type": "Dairy", "hq": "Phoenix", "value": 5_000_000, "carbon": 150, "ins": 60, "sc": 70},
        ],
        "_default": [
            {"name": "Deere & Company", "type": "Ag Equipment", "hq": "Moline", "value": 55_000_000, "carbon": 95, "ins": 50, "sc": 85},
            {"name": "Tyson Foods", "type": "Food Processing", "hq": "Springdale", "value": 30_000_000, "carbon": 220, "ins": 68, "sc": 92},
            {"name": "Bunge", "type": "Ag Processing", "hq": "St. Louis", "value": 18_000_000, "carbon": 170, "ins": 62, "sc": 88},
        ],
    },
    "Materials": {
        "Texas": [
            {"name": "LyondellBasell", "type": "Chemicals", "hq": "Houston", "value": 30_000_000, "carbon": 420, "ins": 62, "sc": 85},
            {"name": "Celanese", "type": "Chemicals", "hq": "Dallas", "value": 18_000_000, "carbon": 350, "ins": 58, "sc": 80},
        ],
        "California": [
            {"name": "Vulcan Materials (West)", "type": "Construction", "hq": "Los Angeles", "value": 12_000_000, "carbon": 280, "ins": 55, "sc": 75},
        ],
        "_default": [
            {"name": "Dow Inc", "type": "Chemicals", "hq": "Midland", "value": 40_000_000, "carbon": 380, "ins": 62, "sc": 85},
            {"name": "Nucor", "type": "Steel", "hq": "Charlotte", "value": 35_000_000, "carbon": 520, "ins": 58, "sc": 82},
            {"name": "Freeport-McMoRan", "type": "Mining", "hq": "Phoenix", "value": 55_000_000, "carbon": 350, "ins": 60, "sc": 70},
        ],
    },
    "Technology": {
        "Texas": [
            {"name": "Dell Technologies", "type": "Hardware", "hq": "Round Rock", "value": 40_000_000, "carbon": 55, "ins": 45, "sc": 88},
            {"name": "Texas Instruments", "type": "Semiconductors", "hq": "Dallas", "value": 45_000_000, "carbon": 65, "ins": 40, "sc": 82},
        ],
        "California": [
            {"name": "Apple", "type": "Consumer Electronics", "hq": "Cupertino", "value": 350_000_000, "carbon": 25, "ins": 35, "sc": 90},
            {"name": "Alphabet", "type": "Internet Services", "hq": "Mountain View", "value": 200_000_000, "carbon": 45, "ins": 32, "sc": 50},
            {"name": "NVIDIA", "type": "Semiconductors", "hq": "Santa Clara", "value": 280_000_000, "carbon": 35, "ins": 38, "sc": 88},
            {"name": "Meta Platforms", "type": "Social Media", "hq": "Menlo Park", "value": 150_000_000, "carbon": 40, "ins": 28, "sc": 45},
        ],
        "Washington": [
            {"name": "Microsoft", "type": "Software", "hq": "Redmond", "value": 320_000_000, "carbon": 30, "ins": 30, "sc": 55},
            {"name": "Amazon", "type": "E-commerce", "hq": "Seattle", "value": 200_000_000, "carbon": 120, "ins": 45, "sc": 95},
        ],
        "_default": [
            {"name": "Salesforce", "type": "Software", "hq": "San Francisco", "value": 55_000_000, "carbon": 22, "ins": 25, "sc": 40},
        ],
    },
    "Healthcare": {
        "Texas": [
            {"name": "Tenet Healthcare", "type": "Hospitals", "hq": "Dallas", "value": 18_000_000, "carbon": 90, "ins": 72, "sc": 82},
        ],
        "Florida": [
            {"name": "HCA Healthcare (FL)", "type": "Hospitals", "hq": "Miami", "value": 25_000_000, "carbon": 80, "ins": 75, "sc": 85},
        ],
        "_default": [
            {"name": "UnitedHealth Group", "type": "Health Insurance", "hq": "Minnetonka", "value": 500_000_000, "carbon": 18, "ins": 45, "sc": 60},
            {"name": "Johnson & Johnson", "type": "Pharma", "hq": "New Brunswick", "value": 400_000_000, "carbon": 65, "ins": 55, "sc": 80},
            {"name": "CVS Health", "type": "Healthcare Services", "hq": "Woonsocket", "value": 100_000_000, "carbon": 35, "ins": 58, "sc": 85},
        ],
    },
    "Consumer Discretionary": {
        "Florida": [
            {"name": "Walt Disney (Parks)", "type": "Entertainment", "hq": "Orlando", "value": 85_000_000, "carbon": 70, "ins": 80, "sc": 72},
            {"name": "Darden Restaurants", "type": "Restaurants", "hq": "Orlando", "value": 18_000_000, "carbon": 55, "ins": 60, "sc": 75},
        ],
        "Texas": [
            {"name": "AT&T", "type": "Telecom", "hq": "Dallas", "value": 120_000_000, "carbon": 48, "ins": 50, "sc": 70},
        ],
        "_default": [
            {"name": "Home Depot", "type": "Home Improvement", "hq": "Atlanta", "value": 350_000_000, "carbon": 45, "ins": 55, "sc": 88},
            {"name": "Marriott International", "type": "Hotels", "hq": "Bethesda", "value": 55_000_000, "carbon": 65, "ins": 72, "sc": 70},
            {"name": "Target", "type": "Retail", "hq": "Minneapolis", "value": 70_000_000, "carbon": 48, "ins": 58, "sc": 90},
        ],
    },
    "Consumer Staples": {
        "_default": [
            {"name": "Walmart", "type": "Retail", "hq": "Bentonville", "value": 400_000_000, "carbon": 65, "ins": 55, "sc": 95},
            {"name": "Procter & Gamble", "type": "Consumer Products", "hq": "Cincinnati", "value": 350_000_000, "carbon": 55, "ins": 45, "sc": 85},
            {"name": "Coca-Cola", "type": "Beverages", "hq": "Atlanta", "value": 260_000_000, "carbon": 48, "ins": 42, "sc": 80},
            {"name": "PepsiCo", "type": "Beverages", "hq": "Purchase", "value": 230_000_000, "carbon": 52, "ins": 44, "sc": 82},
        ],
    },
}

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
    "hurricane": {"Real Estate": 0.9, "Energy": 0.8, "Transportation": 0.85, "Agriculture": 0.7, "Utilities": 0.8, "Financials": 0.4, "Consumer Discretionary": 0.5, "Healthcare": 0.45},
    "wildfire": {"Real Estate": 0.85, "Agriculture": 0.9, "Utilities": 0.7, "Energy": 0.5, "Healthcare": 0.4, "Consumer Discretionary": 0.3},
    "flood": {"Real Estate": 0.9, "Transportation": 0.8, "Agriculture": 0.85, "Energy": 0.6, "Utilities": 0.7, "Consumer Discretionary": 0.4},
    "drought": {"Agriculture": 0.95, "Utilities": 0.7, "Energy": 0.6, "Consumer Staples": 0.5, "Materials": 0.3},
    "heatwave": {"Agriculture": 0.7, "Energy": 0.8, "Utilities": 0.85, "Healthcare": 0.6, "Transportation": 0.5, "Consumer Discretionary": 0.3},
    "carbon_tax": {"Energy": 0.9, "Materials": 0.8, "Transportation": 0.75, "Utilities": 0.7, "Consumer Discretionary": 0.4},
    "emissions_regulation": {"Energy": 0.85, "Materials": 0.8, "Utilities": 0.75, "Transportation": 0.7},
    "tornado": {"Real Estate": 0.85, "Agriculture": 0.8, "Utilities": 0.75, "Transportation": 0.6},
    "winter_storm": {"Utilities": 0.9, "Transportation": 0.85, "Energy": 0.7, "Real Estate": 0.5, "Agriculture": 0.4},
    "supply_shock": {"Technology": 0.9, "Consumer Discretionary": 0.7, "Transportation": 0.6, "Materials": 0.8, "Healthcare": 0.5, "Energy": 0.4},
}

# Which sectors are most relevant to each disaster type
EVENT_RELEVANT_SECTORS = {
    "hurricane": ["Energy", "Real Estate", "Utilities", "Transportation", "Financials", "Healthcare", "Consumer Discretionary"],
    "wildfire": ["Real Estate", "Agriculture", "Utilities", "Energy", "Healthcare", "Consumer Discretionary"],
    "flood": ["Real Estate", "Transportation", "Agriculture", "Utilities", "Energy", "Consumer Discretionary"],
    "drought": ["Agriculture", "Utilities", "Energy", "Consumer Staples", "Materials"],
    "heatwave": ["Energy", "Utilities", "Agriculture", "Healthcare", "Transportation"],
    "carbon_tax": ["Energy", "Materials", "Transportation", "Utilities", "Technology"],
    "emissions_regulation": ["Energy", "Materials", "Utilities", "Transportation"],
    "tornado": ["Real Estate", "Agriculture", "Utilities", "Transportation", "Financials"],
    "winter_storm": ["Utilities", "Transportation", "Energy", "Real Estate", "Agriculture"],
    "supply_shock": ["Technology", "Materials", "Consumer Discretionary", "Transportation", "Healthcare", "Energy"],
    "compound": ["Energy", "Utilities", "Real Estate", "Transportation", "Agriculture", "Materials", "Financials", "Healthcare"],
}


# ---------------------------------------------------------------------------
# Graph RAG — MiroFish-style knowledge graph for agent context enrichment
# ---------------------------------------------------------------------------

import networkx as nx


class CompanyKnowledgeGraph:
    """
    In-memory knowledge graph built from agents and their dependencies.

    MiroFish uses Zep as its graph store and queries it to enrich each agent's
    persona before the LLM call.  We do the same thing with networkx:

    1. Each company is a node with attributes (sector, region, market_value, …)
    2. Edges represent dependency relationships (supply_chain, grid, insurance, …)
    3. get_agent_context() walks the 2-hop neighborhood to build a rich text
       context that gets injected into the agent's LLM system prompt.

    This is the graph RAG pattern: retrieve relevant subgraph → augment prompt.
    """

    def __init__(self, agents: list, dep_graph: dict):
        self.G = nx.DiGraph()

        # Add nodes
        for a in agents:
            self.G.add_node(a.name, **{
                "sector": a.sector,
                "region": a.region,
                "market_value": a.market_value,
                "carbon_intensity": a.carbon_intensity,
                "insurance_dep": a.insurance_dependency,
                "supply_chain_dep": a.supply_chain_dependency,
                "company_type": a.company_type,
                "is_portfolio": a.is_portfolio_holding,
            })

        # Add edges from dependency graph
        for source, targets in dep_graph.items():
            for target in targets:
                if self.G.has_node(source) and self.G.has_node(target):
                    # Determine edge type from sector mapping
                    src_sector = self.G.nodes[source].get("sector", "")
                    tgt_sector = self.G.nodes[target].get("sector", "")
                    edge_type = self._infer_edge_type(src_sector, tgt_sector)
                    self.G.add_edge(source, target, relationship=edge_type)

    @staticmethod
    def _infer_edge_type(src_sector: str, tgt_sector: str) -> str:
        if tgt_sector == "Financials":
            return "insured_by" if "insur" in tgt_sector.lower() else "financed_by"
        if tgt_sector == "Utilities":
            return "powered_by"
        if tgt_sector == "Transportation":
            return "shipped_by"
        if tgt_sector == "Materials":
            return "supplied_by"
        if tgt_sector == "Energy":
            return "fueled_by"
        if tgt_sector == "Technology":
            return "tech_dependent"
        return "depends_on"

    def get_agent_context(self, agent_name: str, damage_state: dict, max_hops: int = 2) -> str:
        """
        Graph RAG: retrieve the agent's neighborhood and build rich context.

        Walks up to `max_hops` from the agent node, collecting:
        - Direct dependencies and their current damage state
        - Indirect (2nd-hop) dependencies
        - Relationship types along each path
        - Sector-level aggregates

        Returns a text block ready to inject into the agent's LLM prompt.
        """
        if agent_name not in self.G:
            return ""

        node = self.G.nodes[agent_name]
        lines = [
            f"=== Knowledge Graph Context for {agent_name} ===",
            f"Sector: {node.get('sector')} | Region: {node.get('region')} | "
            f"Type: {node.get('company_type')}",
            f"Market Value: ${node.get('market_value', 0):,.0f}",
            f"Carbon Intensity: {node.get('carbon_intensity', 0):.0f} | "
            f"Insurance Dep: {node.get('insurance_dep', 0):.0f}/100 | "
            f"Supply Chain Dep: {node.get('supply_chain_dep', 0):.0f}/100",
            "",
        ]

        # 1-hop: direct dependencies
        successors = list(self.G.successors(agent_name))
        predecessors = list(self.G.predecessors(agent_name))

        if successors:
            lines.append("Direct dependencies (you depend on):")
            for dep in successors[:10]:
                dep_node = self.G.nodes[dep]
                edge = self.G.edges[agent_name, dep]
                dmg = damage_state.get(dep, 0)
                dmg_pct = (dmg / dep_node.get("market_value", 1)) * 100 if dep_node.get("market_value") else 0
                status = f"DAMAGED ${dmg:,.0f} ({dmg_pct:.1f}%)" if dmg > 0 else "operational"
                lines.append(
                    f"  → {dep} ({dep_node.get('sector')}, {dep_node.get('region')}) "
                    f"[{edge.get('relationship', 'depends_on')}] — {status}"
                )

        if predecessors:
            lines.append("Entities that depend on you:")
            for pred in predecessors[:10]:
                pred_node = self.G.nodes[pred]
                lines.append(
                    f"  ← {pred} ({pred_node.get('sector')}, {pred_node.get('region')})"
                )

        # 2-hop: indirect dependencies
        if max_hops >= 2 and successors:
            indirect = set()
            for dep in successors:
                for hop2 in self.G.successors(dep):
                    if hop2 != agent_name and hop2 not in successors:
                        indirect.add((dep, hop2))
            if indirect:
                lines.append("Indirect dependencies (2nd-hop):")
                for via, target in list(indirect)[:8]:
                    t_node = self.G.nodes.get(target, {})
                    dmg = damage_state.get(target, 0)
                    status = f"DAMAGED ${dmg:,.0f}" if dmg > 0 else "ok"
                    lines.append(
                        f"  → {via} → {target} ({t_node.get('sector', '?')}) — {status}"
                    )

        # Sector damage summary
        sector_damage: dict = {}
        for name, dmg in damage_state.items():
            if dmg > 0 and name in self.G:
                s = self.G.nodes[name].get("sector", "Unknown")
                sector_damage.setdefault(s, {"count": 0, "total": 0.0})
                sector_damage[s]["count"] += 1
                sector_damage[s]["total"] += dmg
        if sector_damage:
            lines.append("Sector-level damage summary:")
            for sector, info in sorted(sector_damage.items(), key=lambda x: -x[1]["total"]):
                lines.append(
                    f"  {sector}: {info['count']} companies damaged, "
                    f"${info['total']:,.0f} total loss"
                )

        return "\n".join(lines)# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentPersona:
    """An entity/company represented as an autonomous agent"""
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
    is_portfolio_holding: bool = True  # False = dynamically generated
    company_type: str = ""

    @property
    def persona_text(self) -> str:
        return (
            f"You are {self.name}, a {self.sector} company ({self.company_type}) "
            f"based in {self.region}. Market value ${self.market_value:,.0f}. "
            f"Dependencies: {', '.join(self.dependencies)}. "
            f"Carbon intensity {self.carbon_intensity:.0f}, "
            f"insurance dependency {self.insurance_dependency:.0f}/100, "
            f"supply chain dependency {self.supply_chain_dependency:.0f}/100."
        )


@dataclass
class CascadeEvent:
    """A single event in the cascade chain"""
    round_num: int
    source_entity: str
    target_entity: str
    event_type: str
    description: str
    loss_amount: float
    severity: str
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


# ---------------------------------------------------------------------------
# LLM Client (optional - falls back to rule-based)
# ---------------------------------------------------------------------------

import time as _time


class LLMClient:
    """
    LLM client with aggressive rate-limit protection.

    Gemini free tier: 15 RPM, 1M tokens/min, 1500 RPD.
    When we get a 429, we stop ALL calls for the retry delay period
    instead of hammering the API with retries.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("LLM_BASE_URL", "")
        self.model = os.environ.get("LLM_MODEL", "")
        self.available = False
        self._rate_limited_until = 0.0  # timestamp when we can try again
        self._consecutive_429s = 0

        if self.api_key:
            try:
                if os.environ.get("GEMINI_API_KEY") and not self.base_url:
                    self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
                    self.model = self.model or "gemini-2.0-flash"
                elif not self.base_url:
                    self.base_url = "https://api.openai.com/v1"
                    self.model = self.model or "gpt-4o-mini"

                from openai import OpenAI
                # Disable the SDK's built-in retries — we handle rate limits ourselves
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    max_retries=0,  # No automatic retries
                    timeout=15.0,
                )
                self.available = True
                logger.info(f"LLM client ready: model={self.model}")
            except Exception as e:
                logger.warning(f"LLM client init failed: {e}")
        else:
            logger.info("No LLM API key found, using rule-based cascade simulation")

    def _is_rate_limited(self) -> bool:
        """Check if we're in a cooldown period from a previous 429."""
        if _time.time() < self._rate_limited_until:
            return True
        return False

    def _handle_rate_limit(self, error_msg: str):
        """Parse retry delay from 429 response and set cooldown."""
        self._consecutive_429s += 1
        # Extract retry delay from error message if present
        import re
        match = re.search(r'retry in ([\d.]+)s', str(error_msg))
        if match:
            delay = float(match.group(1))
        else:
            delay = min(30 * self._consecutive_429s, 120)  # Exponential backoff, max 2 min

        self._rate_limited_until = _time.time() + delay
        logger.warning(
            f"Rate limited (429 #{self._consecutive_429s}). "
            f"Cooling down for {delay:.0f}s. All LLM calls will skip until then."
        )

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> Optional[str]:
        if not self.available:
            return None
        if self._is_rate_limited():
            remaining = self._rate_limited_until - _time.time()
            logger.debug(f"LLM call skipped — rate limited for {remaining:.0f}s more")
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
            self._consecutive_429s = 0  # Reset on success
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate" in err_str.lower() or "quota" in err_str.lower():
                self._handle_rate_limit(err_str)
            else:
                logger.warning(f"LLM call failed: {err_str[:200]}")
            return None


_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# ---------------------------------------------------------------------------
# Dynamic agent generation
# ---------------------------------------------------------------------------

def _lookup_companies(
    event_type: str,
    affected_regions: List[str],
) -> List[Dict[str, Any]]:
    """
    Dynamically pull companies relevant to the disaster type + region.

    Strategy:
    1. Get sectors relevant to this event type
    2. For each sector, pull companies headquartered in the affected regions
    3. Always add _default companies for cross-region dependencies
    4. De-duplicate by name
    """
    relevant_sectors = EVENT_RELEVANT_SECTORS.get(
        event_type, list(SECTOR_DEPENDENCIES.keys())
    )
    normalized_regions = [r.strip() for r in affected_regions if r != "USA"]

    seen_names: set = set()
    companies: List[Dict[str, Any]] = []

    for sector in relevant_sectors:
        sector_registry = COMPANIES_BY_SECTOR_REGION.get(sector, {})

        # 1. Pull region-specific companies
        for region in normalized_regions:
            for co in sector_registry.get(region, []):
                if co["name"] not in seen_names:
                    seen_names.add(co["name"])
                    companies.append({**co, "sector": sector, "region": region})

        # 2. Always pull defaults (national-scale companies)
        for co in sector_registry.get("_default", []):
            if co["name"] not in seen_names:
                seen_names.add(co["name"])
                companies.append({**co, "sector": sector, "region": co.get("hq", "USA")})

    return companies


# ---------------------------------------------------------------------------
# Main simulation engine
# ---------------------------------------------------------------------------

class CascadeSimulationEngine:
    """
    MiroFish-inspired agent-based cascade simulation.

    Key difference from the old approach: agents are NOT just the portfolio
    holdings. The engine dynamically generates agents for real companies
    relevant to the disaster type and region, PLUS the portfolio holdings.
    This means a hurricane in Texas creates agents for ExxonMobil,
    CenterPoint Energy, ERCOT, etc. regardless of whether they are in the
    portfolio - because they are part of the dependency chain.

    Flow:
    1. Parse event -> identify type + regions
    2. build_agents() merges portfolio holdings with dynamically looked-up
       companies relevant to the disaster
    3. Direct impact round: agents in affected region/sector take damage
    4. Cascade rounds: damage propagates through dependency graph
    5. Narrative generation (LLM or rule-based fallback)
    """

    def __init__(self):
        self.llm = get_llm_client()

    # ------------------------------------------------------------------
    # Agent construction
    # ------------------------------------------------------------------

    def build_agents(
        self,
        holdings: List[Dict],
        event_type: str = "compound",
        affected_regions: Optional[List[str]] = None,
    ) -> List[AgentPersona]:
        """
        Build agent list by merging:
        - Portfolio holdings (the user's actual positions)
        - Dynamically generated companies relevant to the disaster
        """
        agents: List[AgentPersona] = []
        seen_names: set = set()

        # 1. Portfolio holdings become agents first
        for h in holdings:
            name = h.get("issuer_name", h.get("asset_name", "Unknown"))
            if name in seen_names:
                continue
            seen_names.add(name)
            sector = h.get("sector", "Unknown")
            deps = SECTOR_DEPENDENCIES.get(sector, ["suppliers", "regulators"])
            agents.append(AgentPersona(
                entity_id=str(h.get("id", h.get("holding_id", ""))),
                name=name,
                sector=sector,
                region=h.get("state_region") or h.get("country", "Unknown"),
                market_value=float(h.get("market_value", 0)),
                combined_score=float(h.get("combined_score", 50)),
                expected_loss=float(h.get("expected_loss", 0)),
                dependencies=deps,
                carbon_intensity=float(h.get("carbon_intensity_proxy", 0) or 0),
                insurance_dependency=float(h.get("insurance_dependency_score", 0) or 0),
                supply_chain_dependency=float(h.get("supply_chain_dependency_score", 0) or 0),
                is_portfolio_holding=True,
                company_type=h.get("asset_type", ""),
            ))

        # 2. Dynamically add disaster-relevant companies
        regions = affected_regions or ["USA"]
        dynamic_companies = _lookup_companies(event_type, regions)
        for co in dynamic_companies:
            if co["name"] in seen_names:
                continue
            seen_names.add(co["name"])
            sector = co["sector"]
            deps = SECTOR_DEPENDENCIES.get(sector, ["suppliers", "regulators"])
            agents.append(AgentPersona(
                entity_id=f"dyn_{co['name'].lower().replace(' ', '_')}",
                name=co["name"],
                sector=sector,
                region=co.get("region", co.get("hq", "USA")),
                market_value=float(co.get("value", 10_000_000)),
                combined_score=50.0,
                expected_loss=0.0,
                dependencies=deps,
                carbon_intensity=float(co.get("carbon", 100)),
                insurance_dependency=float(co.get("ins", 50)),
                supply_chain_dependency=float(co.get("sc", 60)),
                is_portfolio_holding=False,
                company_type=co.get("type", ""),
            ))

        logger.info(
            f"Built {len(agents)} agents: "
            f"{sum(1 for a in agents if a.is_portfolio_holding)} from portfolio, "
            f"{sum(1 for a in agents if not a.is_portfolio_holding)} dynamically generated "
            f"for {event_type} in {regions}"
        )
        return agents

    # ------------------------------------------------------------------
    # Simulation runner
    # ------------------------------------------------------------------

    def run_simulation(
        self,
        agents: List[AgentPersona],
        event_type: str,
        event_description: str,
        affected_regions: List[str],
        severity: str = "high",
        num_rounds: int = 3,
        llm_sector_impact: Optional[Dict[str, float]] = None,
        llm_affected_sectors: Optional[List[str]] = None,
    ) -> SimulationResult:
        logger.info(
            f"Cascade simulation: {event_type} in {affected_regions}, "
            f"severity={severity}, {len(agents)} agents"
        )

        all_events: List[CascadeEvent] = []
        severity_mult = {"low": 0.3, "medium": 0.6, "high": 1.0, "extreme": 1.5}.get(severity, 1.0)
        event_key = event_type.lower().replace(" ", "_")

        dep_graph = self._build_dependency_graph(agents)

        # Build knowledge graph for graph RAG
        self.knowledge_graph = CompanyKnowledgeGraph(agents, dep_graph)
        # Round 0: direct impact
        # If the LLM parsed sector impacts, use those instead of hardcoded table
        direct_events = self._compute_direct_impact(
            agents, event_key, affected_regions, severity_mult,
            llm_sector_impact=llm_sector_impact,
            llm_affected_sectors=llm_affected_sectors,
        )
        all_events.extend(direct_events)

        agent_damage: Dict[str, float] = {}
        for e in direct_events:
            agent_damage[e.target_entity] = agent_damage.get(e.target_entity, 0) + e.loss_amount

        # Rounds 1..N: cascade propagation with per-agent LLM reasoning
        for rnd in range(1, num_rounds + 1):
            cascade = self._propagate_cascade_with_reasoning(
                agents, agent_damage, dep_graph, rnd, severity_mult,
                event_description, event_type,
            )
            if not cascade:
                break
            all_events.extend(cascade)
            for e in cascade:
                agent_damage[e.target_entity] = agent_damage.get(e.target_entity, 0) + e.loss_amount

        total_direct = sum(e.loss_amount for e in all_events if e.round_num == 0)
        total_cascaded = sum(e.loss_amount for e in all_events if e.round_num > 0)
        affected = self._summarize_affected(agents, agent_damage)
        chains = self._extract_chains(all_events)
        narrative = self._generate_narrative(
            event_type, event_description, affected_regions, severity,
            all_events, affected, total_direct, total_cascaded,
        )
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


    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _build_dependency_graph(self, agents: List[AgentPersona]) -> Dict[str, List[str]]:
        """Build graph: agent -> list of agents it depends on."""
        graph: Dict[str, List[str]] = {}
        sector_agents: Dict[str, List[str]] = {}
        for a in agents:
            sector_agents.setdefault(a.sector, []).append(a.name)

        dep_sector_map = {
            "grid": "Utilities", "energy": "Energy", "fuel_suppliers": "Energy",
            "insurers": "Financials", "financing": "Financials", "credit_markets": "Financials",
            "transportation": "Transportation", "infrastructure": "Transportation",
            "supply_chain": "Materials", "suppliers": "Materials", "construction": "Materials",
            "agriculture": "Agriculture", "water_supply": "Utilities",
            "data_centers": "Technology", "technology": "Technology", "talent": "Technology",
            "regulators": "Financials", "consumer_confidence": "Consumer Discretionary",
            "labor": "Consumer Staples",
        }

        for a in agents:
            dependents = []
            for dep_type in a.dependencies:
                mapped = dep_sector_map.get(dep_type)
                if mapped and mapped in sector_agents:
                    for dep_name in sector_agents[mapped]:
                        if dep_name != a.name:
                            dependents.append(dep_name)
            graph[a.name] = list(set(dependents))
        return graph

    def _compute_direct_impact(
        self, agents: List[AgentPersona], event_type: str,
        affected_regions: List[str], severity_mult: float,
        llm_sector_impact: Optional[Dict[str, float]] = None,
        llm_affected_sectors: Optional[List[str]] = None,
    ) -> List[CascadeEvent]:
        events = []
        # Use LLM-parsed impacts if available, otherwise fall back to hardcoded
        sector_impacts = llm_sector_impact or EVENT_SECTOR_IMPACT.get(event_type, {})
        norm_regions = [r.lower() for r in affected_regions]
        is_policy = event_type in ("carbon_tax", "emissions_regulation", "compound")
        is_global = event_type in ("supply_shock", "pandemic", "cyberattack") or not norm_regions or "usa" in norm_regions

        # If LLM told us which sectors are affected but didn't give impact scores,
        # assign a default impact of 0.6 to each
        if llm_affected_sectors and not llm_sector_impact:
            sector_impacts = {s: 0.6 for s in llm_affected_sectors}

        for agent in agents:
            if is_policy or is_global:
                region_match = True
            else:
                region_match = (
                    not norm_regions
                    or any(nr in agent.region.lower() for nr in norm_regions)
                    or "usa" in norm_regions
                )
            if not region_match:
                continue

            impact = sector_impacts.get(agent.sector, 0.15 if (is_policy or is_global) else 0.0)
            if impact == 0:
                continue

            if is_policy and agent.carbon_intensity > 0:
                impact *= min(agent.carbon_intensity / 300.0, 1.5)

            loss = agent.market_value * impact * severity_mult * 0.15
            if loss <= 0:
                continue

            sev = "critical" if impact > 0.7 else "high" if impact > 0.5 else "medium"
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

    def _propagate_cascade_with_reasoning(
        self, agents: List[AgentPersona], agent_damage: Dict[str, float],
        dep_graph: Dict[str, List[str]], round_num: int, severity_mult: float,
        event_description: str, event_type: str,
    ) -> List[CascadeEvent]:
        """
        Cascade propagation with per-agent LLM reasoning.

        When an LLM is available, each significantly-affected agent gets its own
        LLM call to reason about how the damage to its dependencies affects it.
        This is the MiroFish-style approach: each agent is a separate context.

        Falls back to rule-based propagation when no LLM is available.
        """
        events = []
        damaged_set = {n for n, d in agent_damage.items() if d > 0}
        agent_map = {a.name: a for a in agents}

        # Collect agents that have damaged dependencies
        candidates = []
        for agent in agents:
            deps = dep_graph.get(agent.name, [])
            damaged_deps = [d for d in deps if d in damaged_set and d != agent.name]
            if damaged_deps:
                candidates.append((agent, deps, damaged_deps))

        # If LLM available and round 1, do per-agent reasoning for top candidates
        # (limit to avoid excessive API calls)
        if self.llm.available and round_num == 1 and candidates:
            # Sort by potential impact (more damaged deps = higher priority)
            candidates.sort(key=lambda x: len(x[2]), reverse=True)
            llm_limit = min(3, len(candidates))  # Max 3 LLM calls to stay within rate limits

            for agent, deps, damaged_deps in candidates[:llm_limit]:
                # Respect rate limits — skip if we got 429'd
                if self.llm._is_rate_limited():
                    event = self._agent_rule_based(agent, deps, damaged_deps, round_num, severity_mult)
                    if event:
                        events.append(event)
                    continue
                event = self._agent_llm_reasoning(
                    agent, damaged_deps, agent_damage, agent_map,
                    event_description, event_type, round_num, severity_mult,
                )
                if event:
                    events.append(event)

            # Rule-based for the rest
            for agent, deps, damaged_deps in candidates[llm_limit:]:
                event = self._agent_rule_based(
                    agent, deps, damaged_deps, round_num, severity_mult,
                )
                if event:
                    events.append(event)
        else:
            # Pure rule-based for all
            for agent, deps, damaged_deps in candidates:
                event = self._agent_rule_based(
                    agent, deps, damaged_deps, round_num, severity_mult,
                )
                if event:
                    events.append(event)

        return events

    def _agent_llm_reasoning(
        self, agent: AgentPersona, damaged_deps: List[str],
        agent_damage: Dict[str, float], agent_map: Dict[str, AgentPersona],
        event_description: str, event_type: str,
        round_num: int, severity_mult: float,
    ) -> Optional[CascadeEvent]:
        """
        Give this agent its own LLM context enriched by graph RAG.

        MiroFish pattern: query the knowledge graph for the agent's neighborhood,
        build a rich context showing direct deps, indirect deps, damage state,
        sector summaries — then let the agent reason about its own cascade impact.
        """
        import json as _json

        # Graph RAG: retrieve agent's subgraph context
        graph_context = ""
        if hasattr(self, 'knowledge_graph'):
            graph_context = self.knowledge_graph.get_agent_context(
                agent.name, agent_damage, max_hops=2
            )

        system = (
            f"You are {agent.name}, a {agent.sector} company ({agent.company_type}) "
            f"based in {agent.region} with market value ${agent.market_value:,.0f}.\n\n"
            f"{graph_context}\n\n"
            f"Based on your position in the dependency network and the damage to "
            f"your dependencies, estimate your cascade loss. "
            f"Respond ONLY with valid JSON."
        )
        user = (
            f"Event: {event_description}\n\n"
            f"As {agent.name}, considering your dependency graph above, "
            f"estimate your cascade loss. Return JSON:\n"
            f'{{"loss_pct": <float 0-30, percent of your market value lost>,'
            f' "cascade_type": "<supply_chain_disruption|insurance_cascade|'
            f'grid_failure_cascade|operational_disruption>",'
            f' "reasoning": "<one sentence explaining why, referencing specific '
            f'dependencies from the graph>"}}'
        )

        try:
            raw = self.llm.chat(system, user, temperature=0.3)
            if raw:
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    import re
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                parsed = _json.loads(cleaned)
                loss_pct = min(float(parsed.get("loss_pct", 0)), 30.0)
                if loss_pct < 0.1:
                    return None
                loss = agent.market_value * (loss_pct / 100.0) * severity_mult
                loss *= 0.6 ** (round_num - 1)
                if loss < 10_000:
                    return None

                cascade_type = parsed.get("cascade_type", "supply_chain_disruption")
                reasoning = parsed.get("reasoning", "")
                sev = "high" if loss_pct > 5 else "medium" if loss_pct > 1 else "low"

                return CascadeEvent(
                    round_num=round_num,
                    source_entity=damaged_deps[0],
                    target_entity=agent.name,
                    event_type=cascade_type,
                    description=reasoning or f"{agent.name} affected by cascade ({cascade_type})",
                    loss_amount=round(loss, 2),
                    severity=sev,
                    propagation_path=[damaged_deps[0], agent.name],
                )
        except Exception as e:
            logger.warning(f"LLM agent reasoning failed for {agent.name}: {e}")

        # Fall back to rule-based
        return self._agent_rule_based(
            agent, agent.dependencies, damaged_deps, round_num, severity_mult,
        )

    def _agent_rule_based(
        self, agent: AgentPersona, deps: List[str],
        damaged_deps: List[str], round_num: int, severity_mult: float,
    ) -> Optional[CascadeEvent]:
        """Rule-based cascade propagation for a single agent."""
        dep_factor = min(len(damaged_deps) / max(len(deps), 1), 1.0)
        sc_factor = agent.supply_chain_dependency / 100.0 if agent.supply_chain_dependency else 0.5
        loss = agent.market_value * dep_factor * sc_factor * 0.05 * severity_mult
        loss *= 0.6 ** (round_num - 1)

        if loss < 10_000:
            return None

        source = damaged_deps[0]
        etype = "supply_chain_disruption"
        if any("insur" in d.lower() or "financ" in d.lower() for d in damaged_deps):
            etype = "insurance_cascade"
        elif any("grid" in d.lower() or "utilit" in d.lower() or "ercot" in d.lower() for d in damaged_deps):
            etype = "grid_failure_cascade"

        sev = (
            "high" if loss > agent.market_value * 0.05
            else "medium" if loss > agent.market_value * 0.01
            else "low"
        )
        return CascadeEvent(
            round_num=round_num,
            source_entity=source,
            target_entity=agent.name,
            event_type=etype,
            description=f"{agent.name} affected by cascade from {source} ({etype.replace('_', ' ')})",
            loss_amount=round(loss, 2),
            severity=sev,
            propagation_path=[source, agent.name],
        )

    def _summarize_affected(self, agents: List[AgentPersona], damage: Dict[str, float]) -> List[Dict]:
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
                    "is_portfolio_holding": a.is_portfolio_holding,
                    "company_type": a.company_type,
                })
        return result

    def _extract_chains(self, events: List[CascadeEvent]) -> List[List[str]]:
        chains, seen = [], set()
        for e in events:
            if e.round_num > 0:
                key = f"{e.source_entity}->{e.target_entity}"
                if key not in seen:
                    seen.add(key)
                    chains.append(e.propagation_path)
        return chains[:20]


    def _generate_narrative(
        self, event_type: str, description: str, regions: List[str],
        severity: str, events: List[CascadeEvent], affected: List[Dict],
        direct_loss: float, cascaded_loss: float,
    ) -> str:
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
                holding_tag = " [PORTFOLIO]" if a.get("is_portfolio_holding") else " [DEPENDENCY]"
                prompt += (
                    f"- {a['entity']} ({a['sector']}, {a['region']}){holding_tag}: "
                    f"${a['total_loss']:,.0f} loss ({a['loss_pct']:.1f}%)\n"
                )
            prompt += (
                f"\nCascade events: {len([e for e in events if e.round_num > 0])}\n"
                f"Write a 3-4 paragraph executive narrative explaining the cascade "
                f"effects, which sectors were most impacted, how dependencies "
                f"amplified losses, and what the key risk drivers are. "
                f"Be specific about company names and numbers. "
                f"Distinguish between portfolio holdings and dependency-chain companies."
            )
            result = self.llm.chat(
                "You are a climate risk analyst writing an executive briefing on "
                "cascade effects from a climate event on a financial portfolio.",
                prompt,
            )
            if result:
                return result

        # Rule-based fallback
        top3 = affected[:3]
        top_names = ", ".join(a["entity"] for a in top3)
        total = direct_loss + cascaded_loss
        cascade_pct = (cascaded_loss / total * 100) if total > 0 else 0
        portfolio_affected = [a for a in affected if a.get("is_portfolio_holding")]
        dependency_affected = [a for a in affected if not a.get("is_portfolio_holding")]

        return (
            f"A {severity}-severity {event_type} event impacting {', '.join(regions)} "
            f"has triggered portfolio losses totaling ${total:,.0f}.\n\n"
            f"Direct impact accounts for ${direct_loss:,.0f}, while cascade effects "
            f"through supply chain disruptions, insurance dependencies, and "
            f"infrastructure failures added ${cascaded_loss:,.0f} "
            f"({cascade_pct:.0f}% of total losses).\n\n"
            f"The most affected entities are {top_names}. "
            f"{len(portfolio_affected)} portfolio holdings and "
            f"{len(dependency_affected)} dependency-chain companies were impacted, "
            f"with cascade effects propagating through "
            f"{len([e for e in events if e.round_num > 0])} secondary events "
            f"across {len(set(a['sector'] for a in affected))} sectors.\n\n"
            f"Key risk amplifiers include high supply chain dependencies in the "
            f"{top3[0]['sector'] if top3 else 'affected'} sector and geographic "
            f"concentration in {', '.join(regions)}."
        )

    def _generate_recommendations(
        self, affected: List[Dict], event_type: str, total_loss: float,
    ) -> List[str]:
        recs = []
        if affected:
            top = affected[0]
            recs.append(
                f"Reduce exposure to {top['entity']} ({top['sector']}) "
                f"- highest loss at ${top['total_loss']:,.0f}"
            )

        sectors: Dict[str, float] = {}
        for a in affected:
            sectors[a["sector"]] = sectors.get(a["sector"], 0) + a["total_loss"]
        if sectors:
            worst = max(sectors, key=sectors.get)  # type: ignore[arg-type]
            recs.append(
                f"Diversify away from {worst} sector "
                f"- ${sectors[worst]:,.0f} in cascade losses"
            )

        regions: Dict[str, float] = {}
        for a in affected:
            regions[a["region"]] = regions.get(a["region"], 0) + a["total_loss"]
        if regions:
            worst_r = max(regions, key=regions.get)  # type: ignore[arg-type]
            recs.append(
                f"Reduce geographic concentration in {worst_r} "
                f"- ${regions[worst_r]:,.0f} exposure"
            )

        high_loss = [a for a in affected if a["loss_pct"] > 10]
        if high_loss:
            recs.append(
                f"Review insurance coverage for {len(high_loss)} entities "
                f"with >10% loss ratios"
            )

        dep_companies = [a for a in affected if not a.get("is_portfolio_holding")]
        if dep_companies:
            recs.append(
                f"Monitor {len(dep_companies)} dependency-chain companies "
                f"(not in portfolio) that amplified cascade losses"
            )

        recs.append(
            "Establish supply chain redundancy for critical dependencies "
            "identified in cascade analysis"
        )
        return recs
