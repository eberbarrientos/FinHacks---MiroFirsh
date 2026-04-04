"""Add performance indexes

Revision ID: 20240116_add_performance_indexes
Revises: 20240115_initial_schema
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20240116_add_performance_indexes'
down_revision = '20240115_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for frequently queried columns"""
    
    # Add index on scenario_id in risk_results for faster scenario-based queries
    op.create_index(
        'idx_risk_results_scenario',
        'risk_results',
        ['scenario_id'],
        unique=False
    )
    
    # Add index on combined_score in risk_results for faster sorting and filtering
    op.create_index(
        'idx_risk_results_combined_score',
        'risk_results',
        ['combined_score'],
        unique=False
    )
    
    # Add index on portfolio_id in mirofish_runs for faster portfolio queries
    op.create_index(
        'idx_mirofish_runs_portfolio',
        'mirofish_runs',
        ['portfolio_id'],
        unique=False
    )
    
    # Add index on status in mirofish_runs for faster status filtering
    op.create_index(
        'idx_mirofish_runs_status',
        'mirofish_runs',
        ['status'],
        unique=False
    )


def downgrade():
    """Remove performance indexes"""
    
    op.drop_index('idx_mirofish_runs_status', table_name='mirofish_runs')
    op.drop_index('idx_mirofish_runs_portfolio', table_name='mirofish_runs')
    op.drop_index('idx_risk_results_combined_score', table_name='risk_results')
    op.drop_index('idx_risk_results_scenario', table_name='risk_results')
