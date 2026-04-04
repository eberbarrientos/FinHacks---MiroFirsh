"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('base_currency', sa.String(3), server_default='USD'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # Create scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('scenario_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50)),
        sa.Column('time_horizon', sa.String(50)),
        sa.Column('parameters_json', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # Create holdings table
    op.create_table(
        'holdings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', sa.String(255), nullable=False),
        sa.Column('asset_name', sa.String(255), nullable=False),
        sa.Column('asset_type', sa.String(100)),
        sa.Column('issuer_name', sa.String(255)),
        sa.Column('sector', sa.String(100)),
        sa.Column('country', sa.String(100)),
        sa.Column('state_region', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 8)),
        sa.Column('longitude', sa.Numeric(11, 8)),
        sa.Column('market_value', sa.Numeric(20, 2), nullable=False),
        sa.Column('revenue_exposure_pct', sa.Numeric(5, 2)),
        sa.Column('carbon_intensity_proxy', sa.Numeric(10, 2)),
        sa.Column('insurance_dependency_score', sa.Numeric(5, 2)),
        sa.Column('supply_chain_dependency_score', sa.Numeric(5, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE')
    )

    # Create indexes for holdings
    op.create_index('idx_holdings_portfolio', 'holdings', ['portfolio_id'])
    op.create_index('idx_holdings_issuer', 'holdings', ['issuer_name'])
    op.create_index('idx_holdings_sector', 'holdings', ['sector'])
    op.create_index('idx_holdings_location', 'holdings', ['latitude', 'longitude'])

    # Create risk_results table
    op.create_table(
        'risk_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('holding_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('physical_score', sa.Numeric(5, 2)),
        sa.Column('transition_score', sa.Numeric(5, 2)),
        sa.Column('combined_score', sa.Numeric(5, 2)),
        sa.Column('expected_loss', sa.Numeric(20, 2)),
        sa.Column('stressed_return_delta', sa.Numeric(5, 2)),
        sa.Column('confidence', sa.String(50)),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['holding_id'], ['holdings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('holding_id', 'scenario_id', name='uq_holding_scenario')
    )

    # Create index for risk_results
    op.create_index('idx_risk_results_portfolio_scenario', 'risk_results', ['portfolio_id', 'scenario_id'])

    # Create mirofish_runs table
    op.create_table(
        'mirofish_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('input_json', postgresql.JSONB),
        sa.Column('output_json', postgresql.JSONB),
        sa.Column('cascade_events', postgresql.JSONB),
        sa.Column('dependency_narrative', sa.Text),
        sa.Column('propagated_loss', sa.Numeric(20, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE')
    )

    # Create index for mirofish_runs
    op.create_index('idx_mirofish_runs_scenario', 'mirofish_runs', ['scenario_id'])

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_type', sa.String(100), nullable=False),
        sa.Column('priority', sa.String(50), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('affected_holdings', postgresql.JSONB),
        sa.Column('potential_impact', sa.Numeric(20, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE')
    )

    # Create index for recommendations
    op.create_index('idx_recommendations_portfolio_scenario', 'recommendations', ['portfolio_id', 'scenario_id'])


def downgrade() -> None:
    op.drop_table('recommendations')
    op.drop_table('mirofish_runs')
    op.drop_table('risk_results')
    op.drop_table('holdings')
    op.drop_table('scenarios')
    op.drop_table('portfolios')
