"""Initial Q-learning schema

Revision ID: 001_qlearning_initial
Revises:
Create Date: 2025-11-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_qlearning_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Q-learning schema"""

    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    # Create agent_types table
    op.create_table(
        'agent_types',
        sa.Column('agent_type', sa.VARCHAR(50), primary_key=True),
        sa.Column('display_name', sa.VARCHAR(100), nullable=False),
        sa.Column('description', sa.TEXT),
        sa.Column('state_space_dimensions', sa.INTEGER, nullable=False, server_default='10'),
        sa.Column('action_space_dimensions', sa.INTEGER, nullable=False, server_default='5'),
        sa.Column('learning_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0.1000'),
        sa.Column('discount_factor', sa.DECIMAL(5, 4), nullable=False, server_default='0.9500'),
        sa.Column('exploration_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0.2000'),
        sa.Column('min_exploration_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0.0100'),
        sa.Column('exploration_decay', sa.DECIMAL(6, 5), nullable=False, server_default='0.99500'),
        sa.Column('is_active', sa.BOOLEAN, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
    )

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('agent_type', sa.VARCHAR(50), sa.ForeignKey('agent_types.agent_type', ondelete='CASCADE'), nullable=False),
        sa.Column('session_name', sa.VARCHAR(200)),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True)),
        sa.Column('status', sa.VARCHAR(20), nullable=False, server_default='active'),
        sa.Column('task_count', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('total_reward', sa.DECIMAL(12, 4), server_default='0.0000'),
        sa.Column('environment', sa.VARCHAR(50), server_default='development'),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active', 'completed', 'failed', 'cancelled')", name='sessions_status_check')
    )

    # Create indexes for sessions
    op.create_index('idx_sessions_agent_type', 'sessions', ['agent_type'])
    op.create_index('idx_sessions_status', 'sessions', ['status'], postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_sessions_start_time', 'sessions', [sa.text('start_time DESC')])
    op.create_index('idx_sessions_metadata', 'sessions', ['metadata'], postgresql_using='gin')

    # Create q_values table
    op.create_table(
        'q_values',
        sa.Column('q_value_id', sa.BIGINT, primary_key=True, autoincrement=True),
        sa.Column('agent_type', sa.VARCHAR(50), sa.ForeignKey('agent_types.agent_type', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.session_id', ondelete='SET NULL')),
        sa.Column('state_hash', sa.VARCHAR(64), nullable=False),
        sa.Column('state_data', postgresql.JSONB, nullable=False),
        sa.Column('action_hash', sa.VARCHAR(64), nullable=False),
        sa.Column('action_data', postgresql.JSONB, nullable=False),
        sa.Column('q_value', sa.DECIMAL(12, 6), nullable=False, server_default='0.000000'),
        sa.Column('visit_count', sa.INTEGER, nullable=False, server_default='1'),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('confidence_score', sa.DECIMAL(5, 4), server_default='0.5000'),
        sa.Column('uncertainty', sa.DECIMAL(5, 4), server_default='0.5000'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
        sa.UniqueConstraint('agent_type', 'state_hash', 'action_hash', name='uq_agent_state_action')
    )

    # Create indexes for q_values
    op.create_index('idx_q_values_agent_state', 'q_values', ['agent_type', 'state_hash'])
    op.create_index('idx_q_values_agent_state_action', 'q_values', ['agent_type', 'state_hash', 'action_hash'])
    op.create_index('idx_q_values_lookup', 'q_values', ['agent_type', 'state_hash', sa.text('q_value DESC')])
    op.create_index('idx_q_values_expires', 'q_values', ['expires_at'], postgresql_where=sa.text('expires_at IS NOT NULL'))
    op.create_index('idx_q_values_state_data', 'q_values', ['state_data'], postgresql_using='gin')
    op.create_index('idx_q_values_action_data', 'q_values', ['action_data'], postgresql_using='gin')

    # Create trajectories table
    op.create_table(
        'trajectories',
        sa.Column('trajectory_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('agent_type', sa.VARCHAR(50), sa.ForeignKey('agent_types.agent_type', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.session_id', ondelete='CASCADE')),
        sa.Column('task_id', sa.VARCHAR(100), nullable=False),
        sa.Column('initial_state', postgresql.JSONB, nullable=False),
        sa.Column('final_state', postgresql.JSONB, nullable=False),
        sa.Column('actions_taken', postgresql.JSONB, nullable=False),
        sa.Column('states_visited', postgresql.JSONB, nullable=False),
        sa.Column('step_rewards', postgresql.JSONB, nullable=False),
        sa.Column('total_reward', sa.DECIMAL(12, 4), nullable=False),
        sa.Column('discounted_reward', sa.DECIMAL(12, 4), nullable=False),
        sa.Column('execution_time_ms', sa.INTEGER, nullable=False),
        sa.Column('success', sa.BOOLEAN, nullable=False),
        sa.Column('error_message', sa.TEXT),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
    )

    # Create indexes for trajectories
    op.create_index('idx_trajectories_agent_type', 'trajectories', ['agent_type'])
    op.create_index('idx_trajectories_session', 'trajectories', ['session_id'])
    op.create_index('idx_trajectories_task', 'trajectories', ['task_id'])
    op.create_index('idx_trajectories_reward', 'trajectories', [sa.text('total_reward DESC')])
    op.create_index('idx_trajectories_success', 'trajectories', ['success'])
    op.create_index('idx_trajectories_completed', 'trajectories', [sa.text('completed_at DESC')])
    op.create_index('idx_trajectories_expires', 'trajectories', ['expires_at'], postgresql_where=sa.text('expires_at IS NOT NULL'))

    # Create rewards table
    op.create_table(
        'rewards',
        sa.Column('reward_id', sa.BIGINT, primary_key=True, autoincrement=True),
        sa.Column('agent_type', sa.VARCHAR(50), sa.ForeignKey('agent_types.agent_type', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.session_id', ondelete='CASCADE')),
        sa.Column('trajectory_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('trajectories.trajectory_id', ondelete='CASCADE')),
        sa.Column('state_hash', sa.VARCHAR(64), nullable=False),
        sa.Column('action_hash', sa.VARCHAR(64), nullable=False),
        sa.Column('reward_value', sa.DECIMAL(12, 4), nullable=False),
        sa.Column('reward_type', sa.VARCHAR(50), nullable=False),
        sa.Column('reward_source', sa.VARCHAR(100)),
        sa.Column('observed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
    )

    # Create indexes for rewards
    op.create_index('idx_rewards_agent_type', 'rewards', ['agent_type'])
    op.create_index('idx_rewards_session', 'rewards', ['session_id'])
    op.create_index('idx_rewards_trajectory', 'rewards', ['trajectory_id'])
    op.create_index('idx_rewards_state_action', 'rewards', ['agent_type', 'state_hash', 'action_hash'])
    op.create_index('idx_rewards_observed', 'rewards', [sa.text('observed_at DESC')])

    # Create patterns table
    op.create_table(
        'patterns',
        sa.Column('pattern_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('agent_type', sa.VARCHAR(50), sa.ForeignKey('agent_types.agent_type', ondelete='CASCADE'), nullable=False),
        sa.Column('pattern_name', sa.VARCHAR(200), nullable=False),
        sa.Column('pattern_type', sa.VARCHAR(50), nullable=False),
        sa.Column('pattern_category', sa.VARCHAR(50)),
        sa.Column('pattern_data', postgresql.JSONB, nullable=False),
        sa.Column('trigger_conditions', postgresql.JSONB),
        sa.Column('expected_outcome', postgresql.JSONB),
        sa.Column('usage_count', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('success_count', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('failure_count', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('avg_reward', sa.DECIMAL(12, 4), server_default='0.0000'),
        sa.Column('confidence_score', sa.DECIMAL(5, 4), server_default='0.5000'),
        sa.Column('first_seen', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used', sa.TIMESTAMP(timezone=True)),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('version', sa.INTEGER, nullable=False, server_default='1'),
        sa.Column('parent_pattern_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patterns.pattern_id', ondelete='SET NULL')),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
        sa.UniqueConstraint('agent_type', 'pattern_name', 'version', name='uq_agent_pattern')
    )

    # Create indexes for patterns
    op.create_index('idx_patterns_agent_type', 'patterns', ['agent_type'])
    op.create_index('idx_patterns_type', 'patterns', ['pattern_type'])
    op.create_index('idx_patterns_category', 'patterns', ['pattern_category'])
    op.create_index('idx_patterns_name', 'patterns', ['pattern_name'], postgresql_using='gin', postgresql_ops={'pattern_name': 'gin_trgm_ops'})
    op.create_index('idx_patterns_performance', 'patterns', ['agent_type', sa.text('avg_reward DESC')])
    op.create_index('idx_patterns_usage', 'patterns', [sa.text('usage_count DESC')])
    op.create_index('idx_patterns_last_used', 'patterns', [sa.text('last_used DESC NULLS LAST')])
    op.create_index('idx_patterns_data', 'patterns', ['pattern_data'], postgresql_using='gin')
    op.create_index('idx_patterns_triggers', 'patterns', ['trigger_conditions'], postgresql_using='gin')

    # Create agent_states table with computed column
    op.create_table(
        'agent_states',
        sa.Column('state_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('agent_type', sa.VARCHAR(50), sa.ForeignKey('agent_types.agent_type', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_instance_id', sa.VARCHAR(100), nullable=False),
        sa.Column('total_tasks', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('successful_tasks', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('failed_tasks', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('total_reward', sa.DECIMAL(12, 4), nullable=False, server_default='0.0000'),
        sa.Column('avg_reward', sa.DECIMAL(12, 4), nullable=False, server_default='0.0000'),
        sa.Column('current_exploration_rate', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('current_learning_rate', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('patterns_learned', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('q_values_stored', sa.INTEGER, nullable=False, server_default='0'),
        sa.Column('status', sa.VARCHAR(20), nullable=False, server_default='idle'),
        sa.Column('last_activity', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('initialized_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB, server_default="'{}'::jsonb"),
        sa.UniqueConstraint('agent_type', 'agent_instance_id', name='uq_agent_instance'),
        sa.CheckConstraint("status IN ('idle', 'active', 'learning', 'paused', 'error')", name='agent_states_status_check')
    )

    # Add computed column for success_rate
    op.execute("""
        ALTER TABLE agent_states ADD COLUMN success_rate DECIMAL(5,4)
        GENERATED ALWAYS AS (
            CASE
                WHEN total_tasks > 0 THEN ROUND(successful_tasks::DECIMAL / total_tasks, 4)
                ELSE 0.0
            END
        ) STORED
    """)

    # Create indexes for agent_states
    op.create_index('idx_agent_states_type', 'agent_states', ['agent_type'])
    op.create_index('idx_agent_states_instance', 'agent_states', ['agent_instance_id'])
    op.create_index('idx_agent_states_status', 'agent_states', ['status'])
    op.create_index('idx_agent_states_performance', 'agent_states', ['agent_type', sa.text('avg_reward DESC')])
    op.create_index('idx_agent_states_activity', 'agent_states', [sa.text('last_activity DESC')])

    # Create triggers for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("CREATE TRIGGER update_agent_types_updated_at BEFORE UPDATE ON agent_types FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_agent_states_updated_at BEFORE UPDATE ON agent_states FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")

    # Create upsert_q_value function
    op.execute("""
        CREATE OR REPLACE FUNCTION upsert_q_value(
            p_agent_type VARCHAR(50),
            p_state_hash VARCHAR(64),
            p_state_data JSONB,
            p_action_hash VARCHAR(64),
            p_action_data JSONB,
            p_q_value DECIMAL(12,6),
            p_session_id UUID DEFAULT NULL
        ) RETURNS BIGINT AS $$
        DECLARE
            v_q_value_id BIGINT;
        BEGIN
            INSERT INTO q_values (
                agent_type, session_id, state_hash, state_data,
                action_hash, action_data, q_value, visit_count,
                expires_at
            ) VALUES (
                p_agent_type, p_session_id, p_state_hash, p_state_data,
                p_action_hash, p_action_data, p_q_value, 1,
                NOW() + INTERVAL '30 days'
            )
            ON CONFLICT (agent_type, state_hash, action_hash)
            DO UPDATE SET
                q_value = EXCLUDED.q_value,
                visit_count = q_values.visit_count + 1,
                last_updated = NOW(),
                confidence_score = LEAST(1.0, q_values.confidence_score + 0.01),
                uncertainty = GREATEST(0.0, q_values.uncertainty - 0.01)
            RETURNING q_value_id INTO v_q_value_id;

            RETURN v_q_value_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create get_best_action function
    op.execute("""
        CREATE OR REPLACE FUNCTION get_best_action(
            p_agent_type VARCHAR(50),
            p_state_hash VARCHAR(64)
        ) RETURNS TABLE(
            action_data JSONB,
            q_value DECIMAL(12,6),
            confidence_score DECIMAL(5,4)
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                q.action_data,
                q.q_value,
                q.confidence_score
            FROM q_values q
            WHERE q.agent_type = p_agent_type
                AND q.state_hash = p_state_hash
            ORDER BY q.q_value DESC, q.confidence_score DESC
            LIMIT 1;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create cleanup_expired_data function
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_expired_data()
        RETURNS TABLE(
            table_name TEXT,
            deleted_count BIGINT
        ) AS $$
        DECLARE
            v_q_deleted BIGINT;
            v_traj_deleted BIGINT;
            v_pattern_deleted BIGINT;
        BEGIN
            DELETE FROM q_values WHERE expires_at < NOW();
            GET DIAGNOSTICS v_q_deleted = ROW_COUNT;

            DELETE FROM trajectories WHERE expires_at < NOW();
            GET DIAGNOSTICS v_traj_deleted = ROW_COUNT;

            DELETE FROM patterns WHERE expires_at < NOW();
            GET DIAGNOSTICS v_pattern_deleted = ROW_COUNT;

            RETURN QUERY
            SELECT 'q_values'::TEXT, v_q_deleted
            UNION ALL
            SELECT 'trajectories'::TEXT, v_traj_deleted
            UNION ALL
            SELECT 'patterns'::TEXT, v_pattern_deleted;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Insert initial agent types
    op.execute("""
        INSERT INTO agent_types (agent_type, display_name, description, state_space_dimensions, action_space_dimensions) VALUES
            ('test-generator', 'Test Generator', 'AI-powered test generation with sublinear optimization', 15, 8),
            ('test-executor', 'Test Executor', 'Multi-framework test execution with parallel processing', 10, 6),
            ('coverage-analyzer', 'Coverage Analyzer', 'Real-time gap detection with O(log n) algorithms', 12, 5),
            ('quality-gate', 'Quality Gate', 'Intelligent quality gate with risk assessment', 10, 4),
            ('quality-analyzer', 'Quality Analyzer', 'Comprehensive quality metrics analysis', 12, 6),
            ('performance-tester', 'Performance Tester', 'Load testing with k6, JMeter, Gatling', 14, 7),
            ('security-scanner', 'Security Scanner', 'Multi-layer security with SAST/DAST', 16, 8),
            ('requirements-validator', 'Requirements Validator', 'INVEST criteria validation and BDD', 10, 5),
            ('production-intelligence', 'Production Intelligence', 'Production data to test scenarios', 12, 6),
            ('fleet-commander', 'Fleet Commander', 'Hierarchical fleet coordination (50+ agents)', 20, 10),
            ('deployment-readiness', 'Deployment Readiness', 'Multi-factor risk assessment', 11, 5),
            ('regression-risk-analyzer', 'Regression Risk Analyzer', 'Smart test selection with ML', 13, 7),
            ('test-data-architect', 'Test Data Architect', 'High-speed data generation (10k+/sec)', 12, 6),
            ('api-contract-validator', 'API Contract Validator', 'Breaking change detection', 14, 7),
            ('flaky-test-hunter', 'Flaky Test Hunter', 'Statistical flakiness detection', 11, 6),
            ('visual-tester', 'Visual Tester', 'Visual regression with AI comparison', 13, 6),
            ('chaos-engineer', 'Chaos Engineer', 'Resilience testing with fault injection', 15, 8),
            ('code-complexity', 'Code Complexity Analyzer', 'Complexity metrics and recommendations', 10, 5)
    """)


def downgrade() -> None:
    """Remove Q-learning schema"""

    # Drop materialized views (will be added in future migration)
    # op.execute('DROP MATERIALIZED VIEW IF EXISTS pattern_effectiveness')
    # op.execute('DROP MATERIALIZED VIEW IF EXISTS agent_performance_summary')

    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS cleanup_expired_data()')
    op.execute('DROP FUNCTION IF EXISTS get_best_action(VARCHAR, VARCHAR)')
    op.execute('DROP FUNCTION IF EXISTS upsert_q_value(VARCHAR, VARCHAR, JSONB, VARCHAR, JSONB, DECIMAL, UUID)')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop tables in reverse order
    op.drop_table('agent_states')
    op.drop_table('patterns')
    op.drop_table('rewards')
    op.drop_table('trajectories')
    op.drop_table('q_values')
    op.drop_table('sessions')
    op.drop_table('agent_types')

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "btree_gin"')
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
