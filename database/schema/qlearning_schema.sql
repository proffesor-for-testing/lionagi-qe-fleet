-- ============================================================================
-- Agentic QE Fleet - Q-Learning Database Schema
-- ============================================================================
-- Version: 1.0.0
-- PostgreSQL Version: 14+
-- Description: Production-ready schema for storing Q-learning data across
--              18 specialized QE agents with high-throughput writes and
--              optimized reads for action selection.
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For pattern search optimization
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- ============================================================================
-- Core Tables
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Table: agent_types
-- Purpose: Registry of agent types with their learning configurations
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_types (
    agent_type VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    state_space_dimensions INT NOT NULL DEFAULT 10,
    action_space_dimensions INT NOT NULL DEFAULT 5,
    learning_rate DECIMAL(5,4) NOT NULL DEFAULT 0.1000,
    discount_factor DECIMAL(5,4) NOT NULL DEFAULT 0.9500,
    exploration_rate DECIMAL(5,4) NOT NULL DEFAULT 0.2000,
    min_exploration_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0100,
    exploration_decay DECIMAL(6,5) NOT NULL DEFAULT 0.99500,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE agent_types IS 'Registry of 18 QE agent types with learning configurations';
COMMENT ON COLUMN agent_types.state_space_dimensions IS 'Dimensionality of state representation';
COMMENT ON COLUMN agent_types.action_space_dimensions IS 'Number of possible actions';
COMMENT ON COLUMN agent_types.metadata IS 'Flexible storage for agent-specific config';

-- -----------------------------------------------------------------------------
-- Table: sessions
-- Purpose: Group related task executions for context and analytics
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL REFERENCES agent_types(agent_type) ON DELETE CASCADE,
    session_name VARCHAR(200),
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'cancelled')),
    task_count INT NOT NULL DEFAULT 0,
    total_reward DECIMAL(12,4) DEFAULT 0.0000,
    environment VARCHAR(50) DEFAULT 'development',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sessions IS 'Groups related task executions for context tracking';
COMMENT ON COLUMN sessions.environment IS 'Execution environment: development, staging, production';
COMMENT ON COLUMN sessions.metadata IS 'Session context: project, module, branch, etc.';

CREATE INDEX idx_sessions_agent_type ON sessions(agent_type);
CREATE INDEX idx_sessions_status ON sessions(status) WHERE status = 'active';
CREATE INDEX idx_sessions_start_time ON sessions(start_time DESC);
CREATE INDEX idx_sessions_metadata ON sessions USING GIN(metadata);

-- -----------------------------------------------------------------------------
-- Table: q_values
-- Purpose: Store state-action-value tuples (core Q-learning data)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS q_values (
    q_value_id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL REFERENCES agent_types(agent_type) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,

    -- State representation (flexible JSONB for varying state spaces)
    state_hash VARCHAR(64) NOT NULL, -- SHA256 hash of normalized state for fast lookups
    state_data JSONB NOT NULL,       -- Full state representation

    -- Action representation
    action_hash VARCHAR(64) NOT NULL,
    action_data JSONB NOT NULL,

    -- Q-learning values
    q_value DECIMAL(12,6) NOT NULL DEFAULT 0.000000,
    visit_count INT NOT NULL DEFAULT 1,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Confidence metrics
    confidence_score DECIMAL(5,4) DEFAULT 0.5000, -- 0.0 to 1.0
    uncertainty DECIMAL(5,4) DEFAULT 0.5000,      -- 0.0 to 1.0

    -- Temporal tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Prevent duplicate state-action pairs per agent
    CONSTRAINT uq_agent_state_action UNIQUE (agent_type, state_hash, action_hash)
);

COMMENT ON TABLE q_values IS 'Core Q-learning data: state-action-value mappings';
COMMENT ON COLUMN q_values.state_hash IS 'SHA256 hash of normalized state for O(1) lookups';
COMMENT ON COLUMN q_values.state_data IS 'Full state representation (varies by agent type)';
COMMENT ON COLUMN q_values.action_data IS 'Full action representation';
COMMENT ON COLUMN q_values.visit_count IS 'Number of times this state-action pair was selected';
COMMENT ON COLUMN q_values.confidence_score IS 'Confidence in Q-value estimate (UCB-based)';
COMMENT ON COLUMN q_values.expires_at IS 'TTL for data retention policy (default 30 days)';

-- Optimized indexes for Q-value lookups
CREATE INDEX idx_q_values_agent_state ON q_values(agent_type, state_hash);
CREATE INDEX idx_q_values_agent_state_action ON q_values(agent_type, state_hash, action_hash);
CREATE INDEX idx_q_values_lookup ON q_values(agent_type, state_hash, q_value DESC);
CREATE INDEX idx_q_values_expires ON q_values(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_q_values_state_data ON q_values USING GIN(state_data);
CREATE INDEX idx_q_values_action_data ON q_values USING GIN(action_data);

-- -----------------------------------------------------------------------------
-- Table: trajectories
-- Purpose: Store full execution trajectories for experience replay
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trajectories (
    trajectory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL REFERENCES agent_types(agent_type) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    task_id VARCHAR(100) NOT NULL,

    -- Trajectory data
    initial_state JSONB NOT NULL,
    final_state JSONB NOT NULL,
    actions_taken JSONB NOT NULL,  -- Array of actions in sequence
    states_visited JSONB NOT NULL, -- Array of states in sequence

    -- Rewards
    step_rewards JSONB NOT NULL,   -- Array of per-step rewards
    total_reward DECIMAL(12,4) NOT NULL,
    discounted_reward DECIMAL(12,4) NOT NULL,

    -- Execution metadata
    execution_time_ms INT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,

    -- Temporal tracking
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE trajectories IS 'Complete execution trajectories for experience replay and analysis';
COMMENT ON COLUMN trajectories.actions_taken IS 'Sequential array of actions taken during execution';
COMMENT ON COLUMN trajectories.step_rewards IS 'Reward received at each step';
COMMENT ON COLUMN trajectories.discounted_reward IS 'Reward with discount factor applied';

CREATE INDEX idx_trajectories_agent_type ON trajectories(agent_type);
CREATE INDEX idx_trajectories_session ON trajectories(session_id);
CREATE INDEX idx_trajectories_task ON trajectories(task_id);
CREATE INDEX idx_trajectories_reward ON trajectories(total_reward DESC);
CREATE INDEX idx_trajectories_success ON trajectories(success);
CREATE INDEX idx_trajectories_completed ON trajectories(completed_at DESC);
CREATE INDEX idx_trajectories_expires ON trajectories(expires_at) WHERE expires_at IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Table: rewards
-- Purpose: Track individual reward events for analytics
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rewards (
    reward_id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL REFERENCES agent_types(agent_type) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    trajectory_id UUID REFERENCES trajectories(trajectory_id) ON DELETE CASCADE,

    -- State-action context
    state_hash VARCHAR(64) NOT NULL,
    action_hash VARCHAR(64) NOT NULL,

    -- Reward data
    reward_value DECIMAL(12,4) NOT NULL,
    reward_type VARCHAR(50) NOT NULL, -- 'immediate', 'delayed', 'terminal'
    reward_source VARCHAR(100),       -- What generated this reward

    -- Temporal tracking
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE rewards IS 'Individual reward events for granular analysis';
COMMENT ON COLUMN rewards.reward_type IS 'immediate: instant feedback, delayed: future impact, terminal: end of episode';

CREATE INDEX idx_rewards_agent_type ON rewards(agent_type);
CREATE INDEX idx_rewards_session ON rewards(session_id);
CREATE INDEX idx_rewards_trajectory ON rewards(trajectory_id);
CREATE INDEX idx_rewards_state_action ON rewards(agent_type, state_hash, action_hash);
CREATE INDEX idx_rewards_observed ON rewards(observed_at DESC);

-- -----------------------------------------------------------------------------
-- Table: patterns
-- Purpose: Store learned test patterns and heuristics
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patterns (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL REFERENCES agent_types(agent_type) ON DELETE CASCADE,

    -- Pattern identification
    pattern_name VARCHAR(200) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL, -- 'test_template', 'coverage_strategy', 'quality_rule', etc.
    pattern_category VARCHAR(50),

    -- Pattern data
    pattern_data JSONB NOT NULL,
    trigger_conditions JSONB,      -- When to apply this pattern
    expected_outcome JSONB,        -- Expected results

    -- Performance metrics
    usage_count INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    failure_count INT NOT NULL DEFAULT 0,
    avg_reward DECIMAL(12,4) DEFAULT 0.0000,
    confidence_score DECIMAL(5,4) DEFAULT 0.5000,

    -- Temporal tracking
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    -- Versioning
    version INT NOT NULL DEFAULT 1,
    parent_pattern_id UUID REFERENCES patterns(pattern_id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Prevent duplicate patterns per agent
    CONSTRAINT uq_agent_pattern UNIQUE (agent_type, pattern_name, version)
);

COMMENT ON TABLE patterns IS 'Learned test patterns, heuristics, and strategies';
COMMENT ON COLUMN patterns.pattern_data IS 'Core pattern definition (template, rules, etc.)';
COMMENT ON COLUMN patterns.trigger_conditions IS 'Context where pattern should be applied';
COMMENT ON COLUMN patterns.confidence_score IS 'Statistical confidence in pattern effectiveness';

CREATE INDEX idx_patterns_agent_type ON patterns(agent_type);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_category ON patterns(pattern_category);
CREATE INDEX idx_patterns_name ON patterns USING GIN(pattern_name gin_trgm_ops);
CREATE INDEX idx_patterns_performance ON patterns(agent_type, avg_reward DESC);
CREATE INDEX idx_patterns_usage ON patterns(usage_count DESC);
CREATE INDEX idx_patterns_last_used ON patterns(last_used DESC NULLS LAST);
CREATE INDEX idx_patterns_data ON patterns USING GIN(pattern_data);
CREATE INDEX idx_patterns_triggers ON patterns USING GIN(trigger_conditions);

-- -----------------------------------------------------------------------------
-- Table: agent_states
-- Purpose: Track learning progress and current state of each agent
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_states (
    state_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL REFERENCES agent_types(agent_type) ON DELETE CASCADE,
    agent_instance_id VARCHAR(100) NOT NULL, -- Specific agent instance (multiple per type)

    -- Learning progress
    total_tasks INT NOT NULL DEFAULT 0,
    successful_tasks INT NOT NULL DEFAULT 0,
    failed_tasks INT NOT NULL DEFAULT 0,
    total_reward DECIMAL(12,4) NOT NULL DEFAULT 0.0000,
    avg_reward DECIMAL(12,4) NOT NULL DEFAULT 0.0000,

    -- Current learning parameters (may differ from agent_type defaults)
    current_exploration_rate DECIMAL(5,4) NOT NULL,
    current_learning_rate DECIMAL(5,4) NOT NULL,

    -- Performance metrics
    success_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE
            WHEN total_tasks > 0 THEN ROUND(successful_tasks::DECIMAL / total_tasks, 4)
            ELSE 0.0
        END
    ) STORED,
    patterns_learned INT NOT NULL DEFAULT 0,
    q_values_stored INT NOT NULL DEFAULT 0,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'active', 'learning', 'paused', 'error')),
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Temporal tracking
    initialized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- One state record per agent instance
    CONSTRAINT uq_agent_instance UNIQUE (agent_type, agent_instance_id)
);

COMMENT ON TABLE agent_states IS 'Current learning state and progress for each agent instance';
COMMENT ON COLUMN agent_states.agent_instance_id IS 'Unique instance ID (e.g., test-generator-1)';
COMMENT ON COLUMN agent_states.success_rate IS 'Computed column: successful_tasks / total_tasks';

CREATE INDEX idx_agent_states_type ON agent_states(agent_type);
CREATE INDEX idx_agent_states_instance ON agent_states(agent_instance_id);
CREATE INDEX idx_agent_states_status ON agent_states(status);
CREATE INDEX idx_agent_states_performance ON agent_states(agent_type, avg_reward DESC);
CREATE INDEX idx_agent_states_activity ON agent_states(last_activity DESC);

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- -----------------------------------------------------------------------------
-- View: agent_performance_summary
-- Purpose: Fast access to agent performance metrics
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW agent_performance_summary AS
SELECT
    a.agent_type,
    a.display_name,
    COUNT(DISTINCT s.session_id) as total_sessions,
    COUNT(t.trajectory_id) as total_trajectories,
    SUM(CASE WHEN t.success THEN 1 ELSE 0 END) as successful_trajectories,
    AVG(t.total_reward) as avg_reward,
    SUM(t.total_reward) as cumulative_reward,
    AVG(t.execution_time_ms) as avg_execution_time_ms,
    COUNT(DISTINCT p.pattern_id) as unique_patterns,
    AVG(q.visit_count) as avg_state_visits,
    MAX(ast.last_activity) as last_active,
    COUNT(DISTINCT ast.agent_instance_id) as active_instances
FROM agent_types a
LEFT JOIN sessions s ON a.agent_type = s.agent_type
LEFT JOIN trajectories t ON s.session_id = t.session_id
LEFT JOIN patterns p ON a.agent_type = p.agent_type
LEFT JOIN q_values q ON a.agent_type = q.agent_type
LEFT JOIN agent_states ast ON a.agent_type = ast.agent_type
GROUP BY a.agent_type, a.display_name;

CREATE UNIQUE INDEX idx_agent_perf_summary_type ON agent_performance_summary(agent_type);

COMMENT ON MATERIALIZED VIEW agent_performance_summary IS 'Aggregated performance metrics per agent type (refresh periodically)';

-- -----------------------------------------------------------------------------
-- View: pattern_effectiveness
-- Purpose: Analyze pattern performance across agents
-- -----------------------------------------------------------------------------
CREATE MATERIALIZED VIEW pattern_effectiveness AS
SELECT
    p.pattern_id,
    p.agent_type,
    p.pattern_name,
    p.pattern_type,
    p.usage_count,
    p.success_count,
    p.failure_count,
    CASE
        WHEN p.usage_count > 0 THEN ROUND(p.success_count::DECIMAL / p.usage_count, 4)
        ELSE 0.0
    END as success_rate,
    p.avg_reward,
    p.confidence_score,
    COUNT(DISTINCT t.trajectory_id) as trajectories_using_pattern,
    AVG(t.total_reward) as avg_trajectory_reward,
    p.last_used,
    EXTRACT(EPOCH FROM (NOW() - p.last_used))/86400 as days_since_used
FROM patterns p
LEFT JOIN trajectories t ON p.agent_type = t.agent_type
    AND t.metadata @> jsonb_build_object('patterns_used', jsonb_build_array(p.pattern_id::text))
GROUP BY
    p.pattern_id, p.agent_type, p.pattern_name, p.pattern_type,
    p.usage_count, p.success_count, p.failure_count,
    p.avg_reward, p.confidence_score, p.last_used;

CREATE UNIQUE INDEX idx_pattern_eff_id ON pattern_effectiveness(pattern_id);
CREATE INDEX idx_pattern_eff_success ON pattern_effectiveness(success_rate DESC);
CREATE INDEX idx_pattern_eff_reward ON pattern_effectiveness(avg_reward DESC);

COMMENT ON MATERIALIZED VIEW pattern_effectiveness IS 'Pattern performance analysis (refresh hourly)';

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Function: update_updated_at_column
-- Purpose: Automatically update updated_at timestamp
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to relevant tables
CREATE TRIGGER update_agent_types_updated_at BEFORE UPDATE ON agent_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_states_updated_at BEFORE UPDATE ON agent_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- Function: update_q_value
-- Purpose: Upsert Q-value with optimistic locking
-- -----------------------------------------------------------------------------
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
        NOW() + INTERVAL '30 days'  -- Default TTL
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

COMMENT ON FUNCTION upsert_q_value IS 'Atomic upsert of Q-value with visit count and confidence tracking';

-- -----------------------------------------------------------------------------
-- Function: get_best_action
-- Purpose: Select action with highest Q-value for given state
-- -----------------------------------------------------------------------------
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

COMMENT ON FUNCTION get_best_action IS 'Retrieve optimal action for given state (exploitation)';

-- -----------------------------------------------------------------------------
-- Function: cleanup_expired_data
-- Purpose: Remove expired records (TTL enforcement)
-- -----------------------------------------------------------------------------
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
    -- Clean expired Q-values
    DELETE FROM q_values WHERE expires_at < NOW();
    GET DIAGNOSTICS v_q_deleted = ROW_COUNT;

    -- Clean expired trajectories
    DELETE FROM trajectories WHERE expires_at < NOW();
    GET DIAGNOSTICS v_traj_deleted = ROW_COUNT;

    -- Clean expired patterns
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

COMMENT ON FUNCTION cleanup_expired_data IS 'Batch delete expired records (run daily via cron)';

-- -----------------------------------------------------------------------------
-- Function: refresh_materialized_views
-- Purpose: Refresh all materialized views
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY agent_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY pattern_effectiveness;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_materialized_views IS 'Refresh all materialized views (run hourly)';

-- ============================================================================
-- Data Retention Policies
-- ============================================================================

-- Default TTL: 30 days for all learning data
-- Can be customized per agent type via agent_types.metadata

-- PostgreSQL native partitioning (optional, for high-volume deployments)
-- Partition trajectories by month for efficient archival
-- ALTER TABLE trajectories PARTITION BY RANGE (completed_at);

-- ============================================================================
-- Initial Data: Agent Types
-- ============================================================================

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
ON CONFLICT (agent_type) DO NOTHING;

-- ============================================================================
-- Performance Tuning Recommendations
-- ============================================================================

-- 1. Connection Pooling (PgBouncer recommended for 18+ concurrent agents)
-- 2. Autovacuum tuning for high-write tables (q_values, trajectories, rewards)
-- 3. Increase shared_buffers to 25% of RAM (for caching hot Q-values)
-- 4. Enable parallel query execution for aggregations
-- 5. Monitor and adjust work_mem for complex queries

-- Recommended postgresql.conf settings:
-- shared_buffers = 2GB (for 8GB RAM system)
-- effective_cache_size = 6GB
-- maintenance_work_mem = 512MB
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB
-- default_statistics_target = 100
-- random_page_cost = 1.1 (for SSD)
-- effective_io_concurrency = 200
-- work_mem = 64MB
-- max_connections = 100
-- max_worker_processes = 8

-- ============================================================================
-- Monitoring Queries
-- ============================================================================

-- Check table sizes
-- SELECT schemaname, tablename,
--        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan DESC;

-- Monitor Q-value lookup performance
-- SELECT agent_type, COUNT(*), AVG(q_value), MAX(visit_count)
-- FROM q_values
-- GROUP BY agent_type
-- ORDER BY COUNT(*) DESC;

-- ============================================================================
-- End of Schema
-- ============================================================================
