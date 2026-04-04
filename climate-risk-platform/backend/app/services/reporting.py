"""Reporting service for generating executive PDF reports"""

import io
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio as PortfolioModel
from app.models.holding import Holding as HoldingModel
from app.models.scenario import Scenario as ScenarioModel
from app.models.risk_result import RiskResult as RiskResultModel
from app.models.recommendation import Recommendation as RecommendationModel
from app.models.mirofish_run import MiroFishRun as MiroFishRunModel

logger = logging.getLogger(__name__)


class ReportingService:
    """
    Service for generating executive reports in PDF format.
    
    Responsibilities:
    - Aggregate portfolio summary, risk scores, scenario results, recommendations, cascade insights
    - Generate chart images for inclusion in reports
    - Generate static map images
    - Format and generate PDF reports with branding
    """
    
    def __init__(self, db: Session):
        """
        Initialize the reporting service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_executive_report(
        self,
        portfolio_id: str,
        scenario_id: str
    ) -> bytes:
        """
        Generate executive report aggregating all analysis results.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            
        Returns:
            PDF file as bytes
        """
        logger.info(f"Generating executive report for portfolio {portfolio_id}, scenario {scenario_id}")
        
        # Gather all data needed for the report
        report_data = self._gather_report_data(portfolio_id, scenario_id)
        
        # Generate chart images
        chart_images = self.render_charts(report_data)
        
        # Generate map image
        map_image = self.render_map(report_data)
        
        # Format and generate PDF
        pdf_bytes = self.format_pdf(report_data, chart_images, map_image)
        
        logger.info(f"Executive report generated successfully")
        return pdf_bytes
    
    def _gather_report_data(
        self,
        portfolio_id: str,
        scenario_id: str
    ) -> Dict:
        """
        Gather all data needed for the executive report.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            
        Returns:
            Dictionary containing all report data
        """
        # Fetch portfolio
        portfolio = self.db.query(PortfolioModel).filter(
            PortfolioModel.id == portfolio_id
        ).first()
        
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Fetch scenario
        scenario = self.db.query(ScenarioModel).filter(
            ScenarioModel.id == scenario_id
        ).first()
        
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Fetch holdings
        holdings = self.db.query(HoldingModel).filter(
            HoldingModel.portfolio_id == portfolio_id
        ).all()
        
        # Fetch risk results
        risk_results = self.db.query(RiskResultModel).filter(
            RiskResultModel.portfolio_id == portfolio_id,
            RiskResultModel.scenario_id == scenario_id
        ).all()
        
        # Fetch recommendations
        recommendations = self.db.query(RecommendationModel).filter(
            RecommendationModel.portfolio_id == portfolio_id,
            RecommendationModel.scenario_id == scenario_id
        ).order_by(
            RecommendationModel.priority.desc(),
            RecommendationModel.potential_impact.desc()
        ).all()
        
        # Fetch MiroFish cascade results
        mirofish_run = self.db.query(MiroFishRunModel).filter(
            MiroFishRunModel.portfolio_id == portfolio_id,
            MiroFishRunModel.scenario_id == scenario_id,
            MiroFishRunModel.status == "completed"
        ).order_by(MiroFishRunModel.completed_at.desc()).first()
        
        # Calculate portfolio summary metrics
        total_portfolio_value = sum(float(h.market_value) for h in holdings)
        total_expected_loss = sum(float(r.expected_loss) for r in risk_results) if risk_results else 0
        stressed_drawdown = (total_expected_loss / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Calculate sector breakdown
        sector_breakdown = self._calculate_sector_breakdown(holdings, risk_results)
        
        # Calculate geographic breakdown
        geographic_breakdown = self._calculate_geographic_breakdown(holdings, risk_results)
        
        # Get top risks
        top_risks = sorted(
            risk_results,
            key=lambda r: float(r.combined_score),
            reverse=True
        )[:10] if risk_results else []
        
        # Prepare report data
        report_data = {
            "metadata": {
                "portfolio_name": portfolio.name,
                "scenario_name": scenario.name,
                "generation_date": datetime.utcnow().isoformat(),
                "analysis_parameters": {
                    "scenario_type": scenario.scenario_type,
                    "severity": scenario.severity,
                    "time_horizon": scenario.time_horizon,
                    "parameters": scenario.parameters_json or {}
                }
            },
            "portfolio_summary": {
                "total_value": total_portfolio_value,
                "holdings_count": len(holdings),
                "base_currency": portfolio.base_currency,
                "climate_var": total_expected_loss,
                "stressed_drawdown": stressed_drawdown
            },
            "risk_scores": {
                "average_physical_score": self._calculate_average_score(risk_results, "physical_score"),
                "average_transition_score": self._calculate_average_score(risk_results, "transition_score"),
                "average_combined_score": self._calculate_average_score(risk_results, "combined_score"),
                "high_risk_holdings_count": len([r for r in risk_results if float(r.combined_score) > 75]),
                "medium_risk_holdings_count": len([r for r in risk_results if 40 <= float(r.combined_score) <= 75]),
                "low_risk_holdings_count": len([r for r in risk_results if float(r.combined_score) < 40])
            },
            "sector_breakdown": sector_breakdown,
            "geographic_breakdown": geographic_breakdown,
            "top_risks": [
                {
                    "holding_id": str(r.holding_id),
                    "asset_name": self._get_holding_name(r.holding_id, holdings),
                    "issuer_name": self._get_holding_issuer(r.holding_id, holdings),
                    "combined_score": float(r.combined_score),
                    "expected_loss": float(r.expected_loss)
                }
                for r in top_risks
            ],
            "recommendations": [
                {
                    "type": r.recommendation_type,
                    "priority": r.priority,
                    "message": r.message,
                    "potential_impact": float(r.potential_impact) if r.potential_impact else 0
                }
                for r in recommendations
            ],
            "cascade_insights": self._format_cascade_insights(mirofish_run) if mirofish_run else None,
            "holdings": [
                {
                    "id": str(h.id),
                    "asset_name": h.asset_name,
                    "issuer_name": h.issuer_name,
                    "sector": h.sector,
                    "latitude": float(h.latitude),
                    "longitude": float(h.longitude),
                    "market_value": float(h.market_value)
                }
                for h in holdings
            ],
            "risk_results": [
                {
                    "holding_id": str(r.holding_id),
                    "combined_score": float(r.combined_score),
                    "expected_loss": float(r.expected_loss)
                }
                for r in risk_results
            ]
        }
        
        return report_data
    
    def _calculate_sector_breakdown(
        self,
        holdings: List[HoldingModel],
        risk_results: List[RiskResultModel]
    ) -> Dict[str, Dict]:
        """Calculate sector-level breakdown of risk and exposure."""
        sector_data = {}
        
        # Create risk lookup
        risk_lookup = {str(r.holding_id): r for r in risk_results}
        
        for holding in holdings:
            sector = holding.sector or "Unknown"
            
            if sector not in sector_data:
                sector_data[sector] = {
                    "total_value": 0,
                    "total_loss": 0,
                    "holdings_count": 0,
                    "avg_risk_score": 0,
                    "risk_scores": []
                }
            
            sector_data[sector]["total_value"] += float(holding.market_value)
            sector_data[sector]["holdings_count"] += 1
            
            # Add risk data if available
            risk = risk_lookup.get(str(holding.id))
            if risk:
                sector_data[sector]["total_loss"] += float(risk.expected_loss)
                sector_data[sector]["risk_scores"].append(float(risk.combined_score))
        
        # Calculate averages
        for sector, data in sector_data.items():
            if data["risk_scores"]:
                data["avg_risk_score"] = sum(data["risk_scores"]) / len(data["risk_scores"])
            del data["risk_scores"]  # Remove temporary list
        
        return sector_data
    
    def _calculate_geographic_breakdown(
        self,
        holdings: List[HoldingModel],
        risk_results: List[RiskResultModel]
    ) -> Dict[str, Dict]:
        """Calculate geographic breakdown of risk and exposure."""
        geo_data = {}
        
        # Create risk lookup
        risk_lookup = {str(r.holding_id): r for r in risk_results}
        
        for holding in holdings:
            region = holding.state_region or holding.country or "Unknown"
            
            if region not in geo_data:
                geo_data[region] = {
                    "total_value": 0,
                    "total_loss": 0,
                    "holdings_count": 0,
                    "avg_risk_score": 0,
                    "risk_scores": []
                }
            
            geo_data[region]["total_value"] += float(holding.market_value)
            geo_data[region]["holdings_count"] += 1
            
            # Add risk data if available
            risk = risk_lookup.get(str(holding.id))
            if risk:
                geo_data[region]["total_loss"] += float(risk.expected_loss)
                geo_data[region]["risk_scores"].append(float(risk.combined_score))
        
        # Calculate averages
        for region, data in geo_data.items():
            if data["risk_scores"]:
                data["avg_risk_score"] = sum(data["risk_scores"]) / len(data["risk_scores"])
            del data["risk_scores"]  # Remove temporary list
        
        return geo_data
    
    def _calculate_average_score(
        self,
        risk_results: List[RiskResultModel],
        score_field: str
    ) -> float:
        """Calculate average of a specific score field."""
        if not risk_results:
            return 0.0
        
        scores = [float(getattr(r, score_field)) for r in risk_results]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_holding_name(self, holding_id: str, holdings: List[HoldingModel]) -> str:
        """Get holding name by ID."""
        holding = next((h for h in holdings if str(h.id) == str(holding_id)), None)
        return holding.asset_name if holding else "Unknown"
    
    def _get_holding_issuer(self, holding_id: str, holdings: List[HoldingModel]) -> str:
        """Get holding issuer by ID."""
        holding = next((h for h in holdings if str(h.id) == str(holding_id)), None)
        return holding.issuer_name if holding else "Unknown"
    
    def _format_cascade_insights(self, mirofish_run: MiroFishRunModel) -> Dict:
        """Format MiroFish cascade insights for the report."""
        return {
            "status": mirofish_run.status,
            "propagated_loss": float(mirofish_run.propagated_loss) if mirofish_run.propagated_loss else 0,
            "dependency_narrative": mirofish_run.dependency_narrative or "No cascade narrative available",
            "cascade_events": mirofish_run.cascade_events or [],
            "completed_at": mirofish_run.completed_at.isoformat() if mirofish_run.completed_at else None
        }
    
    def render_charts(self, report_data: Dict) -> Dict[str, bytes]:
        """
        Generate chart images for inclusion in the report.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            Dictionary mapping chart names to image bytes
        """
        logger.info("Generating chart images for report")
        
        # Import matplotlib for chart generation
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            logger.warning("Matplotlib not available, skipping chart generation")
            return {}
        
        charts = {}
        
        # Chart 1: Sector Risk Distribution
        sector_chart = self._generate_sector_chart(report_data, plt)
        if sector_chart:
            charts["sector_distribution"] = sector_chart
        
        # Chart 2: Risk Score Distribution
        risk_distribution_chart = self._generate_risk_distribution_chart(report_data, plt)
        if risk_distribution_chart:
            charts["risk_distribution"] = risk_distribution_chart
        
        # Chart 3: Geographic Exposure
        geo_chart = self._generate_geographic_chart(report_data, plt)
        if geo_chart:
            charts["geographic_exposure"] = geo_chart
        
        plt.close('all')  # Clean up
        
        return charts
    
    def _generate_sector_chart(self, report_data: Dict, plt) -> Optional[bytes]:
        """Generate sector risk distribution chart."""
        try:
            sector_data = report_data.get("sector_breakdown", {})
            if not sector_data:
                return None
            
            sectors = list(sector_data.keys())
            values = [data["total_value"] for data in sector_data.values()]
            risks = [data["avg_risk_score"] for data in sector_data.values()]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create bar chart with color based on risk
            colors = ['#ef4444' if r > 75 else '#f59e0b' if r > 40 else '#10b981' for r in risks]
            bars = ax.bar(sectors, values, color=colors, alpha=0.7)
            
            ax.set_xlabel('Sector')
            ax.set_ylabel('Total Value ($)')
            ax.set_title('Portfolio Exposure by Sector')
            ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Error generating sector chart: {e}")
            return None
    
    def _generate_risk_distribution_chart(self, report_data: Dict, plt) -> Optional[bytes]:
        """Generate risk score distribution chart."""
        try:
            risk_scores = report_data.get("risk_scores", {})
            
            categories = ['Low Risk\n(<40)', 'Medium Risk\n(40-75)', 'High Risk\n(>75)']
            counts = [
                risk_scores.get("low_risk_holdings_count", 0),
                risk_scores.get("medium_risk_holdings_count", 0),
                risk_scores.get("high_risk_holdings_count", 0)
            ]
            colors = ['#10b981', '#f59e0b', '#ef4444']
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(counts, labels=categories, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Risk Distribution Across Holdings')
            
            plt.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Error generating risk distribution chart: {e}")
            return None
    
    def _generate_geographic_chart(self, report_data: Dict, plt) -> Optional[bytes]:
        """Generate geographic exposure chart."""
        try:
            geo_data = report_data.get("geographic_breakdown", {})
            if not geo_data:
                return None
            
            # Sort by total value and take top 10
            sorted_regions = sorted(
                geo_data.items(),
                key=lambda x: x[1]["total_value"],
                reverse=True
            )[:10]
            
            regions = [r[0] for r in sorted_regions]
            values = [r[1]["total_value"] for r in sorted_regions]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(regions, values, color='#06b6d4', alpha=0.7)
            ax.set_xlabel('Total Value ($)')
            ax.set_ylabel('Region')
            ax.set_title('Top 10 Geographic Exposures')
            
            plt.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Error generating geographic chart: {e}")
            return None
    
    def render_map(self, report_data: Dict) -> Optional[bytes]:
        """
        Generate static map image showing portfolio holdings.
        
        Args:
            report_data: Dictionary containing report data
            
        Returns:
            Map image as bytes, or None if generation fails
        """
        logger.info("Generating map image for report")
        
        # For now, return None - map generation requires additional dependencies
        # In a full implementation, this would use matplotlib basemap or similar
        # to generate a static map with markers
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            holdings = report_data.get("holdings", [])
            risk_results = report_data.get("risk_results", [])
            
            if not holdings:
                return None
            
            # Create risk lookup
            risk_lookup = {r["holding_id"]: r for r in risk_results}
            
            # Extract coordinates and risk scores
            lats = [h["latitude"] for h in holdings]
            lons = [h["longitude"] for h in holdings]
            risks = [risk_lookup.get(h["id"], {}).get("combined_score", 0) for h in holdings]
            
            # Create scatter plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Color based on risk
            colors = ['#ef4444' if r > 75 else '#f59e0b' if r > 40 else '#10b981' for r in risks]
            sizes = [max(50, r * 2) for r in risks]  # Size based on risk
            
            ax.scatter(lons, lats, c=colors, s=sizes, alpha=0.6, edgecolors='white', linewidth=1)
            
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.set_title('Portfolio Holdings Geographic Distribution')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Error generating map image: {e}")
            return None
    
    def format_pdf(
        self,
        report_data: Dict,
        chart_images: Dict[str, bytes],
        map_image: Optional[bytes]
    ) -> bytes:
        """
        Format and generate PDF report using ReportLab.
        
        Args:
            report_data: Dictionary containing all report data
            chart_images: Dictionary of chart images
            map_image: Map image bytes
            
        Returns:
            PDF file as bytes
        """
        logger.info("Formatting PDF report")
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, Image as RLImage
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            logger.error("ReportLab not available, cannot generate PDF")
            return b"PDF generation requires ReportLab library"
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0891b2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0891b2'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#06b6d4'),
            spaceAfter=6
        )
        
        # Build report sections
        story.extend(self._build_title_page(report_data, title_style, styles))
        story.append(PageBreak())
        
        story.extend(self._build_executive_summary(report_data, heading_style, subheading_style, styles))
        story.append(PageBreak())
        
        story.extend(self._build_portfolio_overview(report_data, heading_style, subheading_style, styles))
        
        # Add charts if available
        if chart_images:
            story.append(PageBreak())
            story.extend(self._build_charts_section(chart_images, heading_style, styles))
        
        # Add map if available
        if map_image:
            story.append(PageBreak())
            story.extend(self._build_map_section(map_image, heading_style, styles))
        
        story.append(PageBreak())
        story.extend(self._build_risk_analysis(report_data, heading_style, subheading_style, styles))
        
        story.append(PageBreak())
        story.extend(self._build_recommendations(report_data, heading_style, subheading_style, styles))
        
        # Add cascade insights if available
        if report_data.get("cascade_insights"):
            story.append(PageBreak())
            story.extend(self._build_cascade_insights(report_data, heading_style, subheading_style, styles))
        
        story.append(PageBreak())
        story.extend(self._build_disclaimer(styles))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info("PDF report generated successfully")
        return pdf_bytes
    
    def _build_title_page(self, report_data: Dict, title_style, styles) -> List:
        """Build title page section."""
        elements = []
        
        metadata = report_data.get("metadata", {})
        
        # Title
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("Climate Risk Intelligence Report", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Metadata
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        elements.append(Paragraph(f"<b>Portfolio:</b> {metadata.get('portfolio_name', 'N/A')}", info_style))
        elements.append(Paragraph(f"<b>Scenario:</b> {metadata.get('scenario_name', 'N/A')}", info_style))
        
        analysis_params = metadata.get('analysis_parameters', {})
        elements.append(Paragraph(
            f"<b>Scenario Type:</b> {analysis_params.get('scenario_type', 'N/A')}", 
            info_style
        ))
        elements.append(Paragraph(
            f"<b>Severity:</b> {analysis_params.get('severity', 'N/A')}", 
            info_style
        ))
        elements.append(Paragraph(
            f"<b>Time Horizon:</b> {analysis_params.get('time_horizon', 'N/A')}", 
            info_style
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Generation date
        gen_date = metadata.get('generation_date', '')
        if gen_date:
            try:
                date_obj = datetime.fromisoformat(gen_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%B %d, %Y at %H:%M UTC')
            except:
                formatted_date = gen_date
        else:
            formatted_date = 'N/A'
        
        elements.append(Paragraph(f"<b>Generated:</b> {formatted_date}", info_style))
        
        return elements
    
    def _build_executive_summary(self, report_data: Dict, heading_style, subheading_style, styles) -> List:
        """Build executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", heading_style))
        
        portfolio_summary = report_data.get("portfolio_summary", {})
        risk_scores = report_data.get("risk_scores", {})
        
        # Key metrics table
        metrics_data = [
            ["Metric", "Value"],
            ["Total Portfolio Value", f"${portfolio_summary.get('total_value', 0):,.2f}"],
            ["Number of Holdings", str(portfolio_summary.get('holdings_count', 0))],
            ["Climate Value at Risk (VaR)", f"${portfolio_summary.get('climate_var', 0):,.2f}"],
            ["Stressed Drawdown", f"{portfolio_summary.get('stressed_drawdown', 0):.2f}%"],
            ["Average Risk Score", f"{risk_scores.get('average_combined_score', 0):.1f}/100"],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891b2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Risk distribution summary
        elements.append(Paragraph("Risk Distribution", subheading_style))
        
        risk_dist_text = f"""
        The portfolio contains {risk_scores.get('high_risk_holdings_count', 0)} high-risk holdings 
        (score > 75), {risk_scores.get('medium_risk_holdings_count', 0)} medium-risk holdings 
        (score 40-75), and {risk_scores.get('low_risk_holdings_count', 0)} low-risk holdings 
        (score < 40). The average physical risk score is {risk_scores.get('average_physical_score', 0):.1f}, 
        while the average transition risk score is {risk_scores.get('average_transition_score', 0):.1f}.
        """
        
        elements.append(Paragraph(risk_dist_text, styles['Normal']))
        
        return elements
    
    def _build_portfolio_overview(self, report_data: Dict, heading_style, subheading_style, styles) -> List:
        """Build portfolio overview section."""
        elements = []
        
        elements.append(Paragraph("Portfolio Overview", heading_style))
        
        # Sector breakdown
        elements.append(Paragraph("Sector Breakdown", subheading_style))
        
        sector_data = report_data.get("sector_breakdown", {})
        if sector_data:
            sector_table_data = [["Sector", "Value", "Holdings", "Avg Risk", "Total Loss"]]
            
            for sector, data in sorted(sector_data.items(), key=lambda x: x[1]['total_value'], reverse=True):
                sector_table_data.append([
                    sector,
                    f"${data['total_value']:,.0f}",
                    str(data['holdings_count']),
                    f"{data['avg_risk_score']:.1f}",
                    f"${data['total_loss']:,.0f}"
                ])
            
            sector_table = Table(sector_table_data, colWidths=[1.5*inch, 1.3*inch, 0.9*inch, 0.9*inch, 1.3*inch])
            sector_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891b2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(sector_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Geographic breakdown
        elements.append(Paragraph("Geographic Breakdown", subheading_style))
        
        geo_data = report_data.get("geographic_breakdown", {})
        if geo_data:
            # Show top 10 regions
            sorted_regions = sorted(geo_data.items(), key=lambda x: x[1]['total_value'], reverse=True)[:10]
            
            geo_table_data = [["Region", "Value", "Holdings", "Avg Risk", "Total Loss"]]
            
            for region, data in sorted_regions:
                geo_table_data.append([
                    region,
                    f"${data['total_value']:,.0f}",
                    str(data['holdings_count']),
                    f"{data['avg_risk_score']:.1f}",
                    f"${data['total_loss']:,.0f}"
                ])
            
            geo_table = Table(geo_table_data, colWidths=[1.5*inch, 1.3*inch, 0.9*inch, 0.9*inch, 1.3*inch])
            geo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891b2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(geo_table)
        
        return elements
    
    def _build_charts_section(self, chart_images: Dict[str, bytes], heading_style, styles) -> List:
        """Build charts section with embedded images."""
        from reportlab.platypus import Image as RLImage
        
        elements = []
        
        elements.append(Paragraph("Risk Visualizations", heading_style))
        
        for chart_name, image_bytes in chart_images.items():
            try:
                img = RLImage(io.BytesIO(image_bytes), width=6*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.3*inch))
            except Exception as e:
                logger.error(f"Error adding chart {chart_name}: {e}")
        
        return elements
    
    def _build_map_section(self, map_image: bytes, heading_style, styles) -> List:
        """Build map section with embedded image."""
        from reportlab.platypus import Image as RLImage
        
        elements = []
        
        elements.append(Paragraph("Geographic Distribution", heading_style))
        
        try:
            img = RLImage(io.BytesIO(map_image), width=6.5*inch, height=4.5*inch)
            elements.append(img)
        except Exception as e:
            logger.error(f"Error adding map image: {e}")
            elements.append(Paragraph("Map image unavailable", styles['Normal']))
        
        return elements
    
    def _build_risk_analysis(self, report_data: Dict, heading_style, subheading_style, styles) -> List:
        """Build detailed risk analysis section."""
        elements = []
        
        elements.append(Paragraph("Risk Analysis", heading_style))
        
        # Top risks
        elements.append(Paragraph("Top 10 Highest Risk Holdings", subheading_style))
        
        top_risks = report_data.get("top_risks", [])[:10]
        
        if top_risks:
            risk_table_data = [["Asset Name", "Issuer", "Risk Score", "Expected Loss"]]
            
            for risk in top_risks:
                risk_table_data.append([
                    risk.get('asset_name', 'N/A'),
                    risk.get('issuer_name', 'N/A'),
                    f"{risk.get('combined_score', 0):.1f}",
                    f"${risk.get('expected_loss', 0):,.0f}"
                ])
            
            risk_table = Table(risk_table_data, colWidths=[2*inch, 2*inch, 1*inch, 1.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891b2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(risk_table)
        
        return elements
    
    def _build_recommendations(self, report_data: Dict, heading_style, subheading_style, styles) -> List:
        """Build recommendations section."""
        elements = []
        
        elements.append(Paragraph("Recommendations", heading_style))
        
        recommendations = report_data.get("recommendations", [])
        
        if recommendations:
            elements.append(Paragraph(
                f"Based on the risk analysis, we have identified {len(recommendations)} actionable recommendations:",
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            # Group by priority
            priority_groups = {}
            for rec in recommendations:
                priority = rec.get('priority', 'low')
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(rec)
            
            # Display by priority
            for priority in ['critical', 'high', 'medium', 'low']:
                if priority in priority_groups:
                    elements.append(Paragraph(f"{priority.upper()} Priority", subheading_style))
                    
                    for rec in priority_groups[priority]:
                        rec_text = f"• <b>{rec.get('type', 'N/A').upper()}:</b> {rec.get('message', 'N/A')}"
                        if rec.get('potential_impact', 0) > 0:
                            rec_text += f" (Potential impact: ${rec.get('potential_impact', 0):,.0f})"
                        
                        elements.append(Paragraph(rec_text, styles['Normal']))
                        elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("No specific recommendations available.", styles['Normal']))
        
        return elements
    
    def _build_cascade_insights(self, report_data: Dict, heading_style, subheading_style, styles) -> List:
        """Build cascade insights section."""
        elements = []
        
        elements.append(Paragraph("Cascade Analysis Insights", heading_style))
        
        cascade_insights = report_data.get("cascade_insights", {})
        
        if cascade_insights:
            # Summary metrics
            elements.append(Paragraph("Cascade Impact Summary", subheading_style))
            
            summary_text = f"""
            The dependency cascade simulation identified propagated losses of 
            ${cascade_insights.get('propagated_loss', 0):,.2f} beyond direct exposures. 
            This represents second-order and systemic risk effects through supply chains, 
            financial networks, and operational dependencies.
            """
            
            elements.append(Paragraph(summary_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Narrative
            elements.append(Paragraph("Cascade Narrative", subheading_style))
            
            narrative = cascade_insights.get('dependency_narrative', 'No narrative available')
            elements.append(Paragraph(narrative, styles['Normal']))
        else:
            elements.append(Paragraph("Cascade analysis not available for this scenario.", styles['Normal']))
        
        return elements
    
    def _build_disclaimer(self, styles) -> List:
        """Build disclaimer section."""
        elements = []
        
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_LEFT
        )
        
        disclaimer_text = """
        <b>DISCLAIMER:</b> This report contains model-based projections of climate-related 
        financial risks that are subject to significant uncertainty. The risk estimates, 
        loss projections, and recommendations provided herein are based on historical data, 
        climate scenarios, and quantitative models that may not accurately predict future 
        events. Actual climate impacts and financial losses may differ materially from 
        these projections. This report should be used as one input among many in investment 
        decision-making and risk management processes. Users should conduct their own due 
        diligence and consult with qualified professionals before making investment decisions 
        based on this analysis. The authors and publishers of this report make no warranties 
        or representations regarding the accuracy, completeness, or suitability of this 
        information for any particular purpose.
        """
        
        elements.append(Paragraph(disclaimer_text, disclaimer_style))
        
        return elements
