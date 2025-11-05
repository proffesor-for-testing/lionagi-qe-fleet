-- LionAGI QE Fleet - Development Schema Extensions
-- Additional tables and utilities for local development

SET search_path TO public, qlearning;

-- ============================================================================
-- Development-Only Tables
-- ============================================================================

-- Local Test Run Log
-- Lightweight logging for local test runs during development
CREATE TABLE IF NOT EXISTS qlearning.dev_test_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Test run identification
    run_id VARCHAR(255) NOT NULL UNIQUE,
    developer_name VARCHAR(255),
    branch_name VARCHAR(255),
    commit_message TEXT,

    -- Test statistics
    tests_run INT NOT NULL DEFAULT 0,
    tests_passed INT NOT NULL DEFAULT 0,
    tests_failed INT NOT NULL DEFAULT 0,
    coverage_percentage DECIMAL(5, 2),

    -- Quick metadata
    notes TEXT,
    tags TEXT[],

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dev_runs_created_at ON qlearning.dev_test_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dev_runs_branch ON qlearning.dev_test_runs(branch_name);

-- Development Query Examples
-- Helpful queries for development and debugging
CREATE TABLE IF NOT EXISTS qlearning.dev_query_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Query metadata
    query_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),                     -- Debugging, Analysis, Reporting, etc.
    description TEXT,

    -- Query content
    sql_query TEXT NOT NULL,
    expected_results TEXT,

    -- Usage
    usage_count INT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert helpful query examples
INSERT INTO qlearning.dev_query_examples (query_name, category, description, sql_query)
VALUES
    (
        'Agent Q-Values Summary',
        'Analysis',
        'View all Q-values for an agent with latest metrics',
        E'SELECT agent_id, test_category, test_framework,\n  action_run_all, action_run_critical, action_run_regression,\n  visits, updates, updated_at\nFROM q_values\nWHERE agent_id = $1\nORDER BY updated_at DESC;'
    ),
    (
        'Test Failure Rate by Category',
        'Reporting',
        'Calculate failure rates for each test category',
        E'SELECT test_category,\n  COUNT(*) as total_tests,\n  COUNT(*) FILTER (WHERE status = \'failed\') as failed_tests,\n  ROUND(COUNT(*) FILTER (WHERE status = \'failed\')::DECIMAL / COUNT(*) * 100, 2) as failure_rate\nFROM test_execution_history\nWHERE created_at > CURRENT_TIMESTAMP - INTERVAL \'7 days\'\nGROUP BY test_category\nORDER BY failure_rate DESC;'
    ),
    (
        'Flaky Tests Report',
        'Reporting',
        'Identify flaky tests and their failure patterns',
        E'SELECT test_name, test_category,\n  COUNT(*) as occurrences,\n  COUNT(*) FILTER (WHERE status = \'passed\') as pass_count,\n  COUNT(*) FILTER (WHERE status = \'failed\') as fail_count,\n  ROUND(COUNT(*) FILTER (WHERE flaky)::DECIMAL / COUNT(*) * 100, 2) as flakiness_percent\nFROM test_execution_history\nWHERE created_at > CURRENT_TIMESTAMP - INTERVAL \'30 days\'\nGROUP BY test_name, test_category\nHAVING COUNT(*) > 5 AND COUNT(*) FILTER (WHERE status = \'failed\') > 0\nORDER BY flakiness_percent DESC;'
    ),
    (
        'Agent Learning Progress',
        'Analysis',
        'Track agent learning improvement over time',
        E'SELECT agent_id, episode_number, tests_executed, tests_passed,\n  ROUND(tests_passed::DECIMAL / NULLIF(tests_executed, 0) * 100, 2) as pass_rate,\n  coverage_achieved, total_reward, started_at\nFROM agent_learning_episodes\nWHERE agent_id = $1 AND status = \'completed\'\nORDER BY episode_number DESC\nLIMIT 20;'
    ),
    (
        'Coverage Trend Analysis',
        'Analysis',
        'View code coverage trends over time',
        E'SELECT snapshot_date, coverage_percentage,\n  LAG(coverage_percentage) OVER (ORDER BY snapshot_date) as previous_coverage,\n  coverage_percentage - LAG(coverage_percentage) OVER (ORDER BY snapshot_date) as delta\nFROM coverage_snapshots\nWHERE agent_id = $1\nORDER BY snapshot_date DESC\nLIMIT 30;'
    )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Sample Data for Testing
-- ============================================================================

-- Sample Q-Values for development testing
INSERT INTO qlearning.q_values (agent_id, test_category, test_framework, context_hash, test_count, coverage_gap, complexity_score, visits, updates)
VALUES
    ('qe-test-generator', 'unit', 'jest', 'hash_001', 45, 15.5, 3.2, 100, 25),
    ('qe-test-generator', 'integration', 'jest', 'hash_002', 12, 8.3, 7.8, 85, 15),
    ('qe-test-executor', 'unit', 'pytest', 'hash_003', 67, 5.2, 2.1, 200, 50),
    ('qe-test-executor', 'e2e', 'pytest', 'hash_004', 8, 22.1, 9.5, 45, 10)
ON CONFLICT (agent_id, test_category, test_framework, context_hash) DO NOTHING;

-- ============================================================================
-- Development Utility Functions
-- ============================================================================

-- Function to get recent test execution stats
CREATE OR REPLACE FUNCTION qlearning.get_recent_stats(
    hours_back INT DEFAULT 24
)
RETURNS TABLE (
    metric_name VARCHAR,
    value NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'Total Tests Run'::VARCHAR,
        COUNT(*)::NUMERIC
    FROM test_execution_history
    WHERE created_at > CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL

    UNION ALL

    SELECT
        'Tests Passed'::VARCHAR,
        COUNT(*) FILTER (WHERE status = 'passed')::NUMERIC
    FROM test_execution_history
    WHERE created_at > CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL

    UNION ALL

    SELECT
        'Tests Failed'::VARCHAR,
        COUNT(*) FILTER (WHERE status = 'failed')::NUMERIC
    FROM test_execution_history
    WHERE created_at > CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL

    UNION ALL

    SELECT
        'Average Duration (ms)'::VARCHAR,
        AVG(duration_ms)::NUMERIC
    FROM test_execution_history
    WHERE created_at > CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL

    UNION ALL

    SELECT
        'Success Rate (%)'::VARCHAR,
        (COUNT(*) FILTER (WHERE status = 'passed')::DECIMAL /
         NULLIF(COUNT(*), 0) * 100)::NUMERIC
    FROM test_execution_history
    WHERE created_at > CURRENT_TIMESTAMP - (hours_back || ' hours')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Function to reset development database (careful!)
CREATE OR REPLACE FUNCTION qlearning.dev_reset_database(include_patterns BOOLEAN DEFAULT FALSE)
RETURNS TEXT AS $$
DECLARE
    deleted_count INT;
BEGIN
    -- Delete test execution history
    DELETE FROM test_execution_history;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % test execution records', deleted_count;

    -- Delete learning episodes
    DELETE FROM agent_learning_episodes;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % learning episode records', deleted_count;

    -- Delete performance metrics
    DELETE FROM agent_performance_metrics;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % performance metric records', deleted_count;

    -- Delete error logs
    DELETE FROM error_log;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % error log records', deleted_count;

    -- Reset Q-values if requested
    IF include_patterns THEN
        DELETE FROM test_patterns;
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        RAISE NOTICE 'Deleted % test pattern records', deleted_count;

        DELETE FROM q_values;
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        RAISE NOTICE 'Deleted % Q-value records', deleted_count;
    END IF;

    RETURN 'Database reset completed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Grants for Development Users
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON qlearning.dev_test_runs TO qe_agent;
GRANT SELECT ON qlearning.dev_query_examples TO qe_agent;
GRANT EXECUTE ON FUNCTION qlearning.get_recent_stats(INT) TO qe_agent;
GRANT EXECUTE ON PROCEDURE qlearning.dev_reset_database(BOOLEAN) TO qe_agent;
