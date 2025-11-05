-- ============================================================================
-- Seed Data for Q-Learning Database
-- ============================================================================
-- Purpose: Insert sample data for testing and development
-- ============================================================================

-- Note: agent_types are already seeded in qlearning_schema.sql
-- This file contains additional sample data for testing

-- ============================================================================
-- Sample Sessions
-- ============================================================================

INSERT INTO sessions (session_id, agent_type, session_name, start_time, status, environment, metadata) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'test-generator', 'Auth Module Test Gen', NOW() - INTERVAL '2 hours', 'completed', 'development', '{"project": "qe-fleet", "module": "auth"}'),
    ('550e8400-e29b-41d4-a716-446655440002', 'coverage-analyzer', 'Coverage Analysis Session', NOW() - INTERVAL '1 hour', 'completed', 'development', '{"project": "qe-fleet", "module": "core"}'),
    ('550e8400-e29b-41d4-a716-446655440003', 'test-executor', 'Test Execution Run', NOW() - INTERVAL '30 minutes', 'active', 'development', '{"project": "qe-fleet", "suite": "unit-tests"}')
ON CONFLICT (session_id) DO NOTHING;

-- ============================================================================
-- Sample Q-Values
-- ============================================================================

-- Test Generator Q-values
INSERT INTO q_values (agent_type, session_id, state_hash, state_data, action_hash, action_data, q_value, visit_count, confidence_score, expires_at) VALUES
    ('test-generator', '550e8400-e29b-41d4-a716-446655440001',
     'a1b2c3d4', '{"module": "auth", "complexity": "high", "coverage": 0.65}',
     'e5f6g7h8', '{"action": "generate_unit_test", "framework": "pytest", "pattern": "arrange_act_assert"}',
     0.85, 5, 0.75, NOW() + INTERVAL '30 days'),

    ('test-generator', '550e8400-e29b-41d4-a716-446655440001',
     'a1b2c3d4', '{"module": "auth", "complexity": "high", "coverage": 0.65}',
     'i9j0k1l2', '{"action": "generate_integration_test", "framework": "pytest", "pattern": "bdd_style"}',
     0.72, 3, 0.65, NOW() + INTERVAL '30 days'),

    ('test-generator', '550e8400-e29b-41d4-a716-446655440001',
     'm3n4o5p6', '{"module": "auth", "complexity": "low", "coverage": 0.90}',
     'e5f6g7h8', '{"action": "generate_unit_test", "framework": "pytest", "pattern": "arrange_act_assert"}',
     0.50, 2, 0.55, NOW() + INTERVAL '30 days')
ON CONFLICT (agent_type, state_hash, action_hash) DO NOTHING;

-- Coverage Analyzer Q-values
INSERT INTO q_values (agent_type, session_id, state_hash, state_data, action_hash, action_data, q_value, visit_count, confidence_score, expires_at) VALUES
    ('coverage-analyzer', '550e8400-e29b-41d4-a716-446655440002',
     'q7r8s9t0', '{"module": "core", "line_coverage": 0.75, "branch_coverage": 0.60}',
     'u1v2w3x4', '{"action": "identify_gaps", "strategy": "branch_analysis"}',
     0.90, 8, 0.85, NOW() + INTERVAL '30 days'),

    ('coverage-analyzer', '550e8400-e29b-41d4-a716-446655440002',
     'q7r8s9t0', '{"module": "core", "line_coverage": 0.75, "branch_coverage": 0.60}',
     'y5z6a7b8', '{"action": "suggest_tests", "priority": "high_complexity"}',
     0.78, 4, 0.70, NOW() + INTERVAL '30 days')
ON CONFLICT (agent_type, state_hash, action_hash) DO NOTHING;

-- ============================================================================
-- Sample Trajectories
-- ============================================================================

INSERT INTO trajectories (
    trajectory_id, agent_type, session_id, task_id,
    initial_state, final_state, actions_taken, states_visited,
    step_rewards, total_reward, discounted_reward,
    execution_time_ms, success, started_at, completed_at, expires_at
) VALUES
    ('650e8400-e29b-41d4-a716-446655440001',
     'test-generator',
     '550e8400-e29b-41d4-a716-446655440001',
     'task-001',
     '{"module": "auth", "coverage": 0.50, "test_count": 10}',
     '{"module": "auth", "coverage": 0.75, "test_count": 15}',
     '[{"action": "generate_unit_test", "target": "login"}, {"action": "generate_unit_test", "target": "logout"}]',
     '[{"module": "auth", "coverage": 0.50}, {"module": "auth", "coverage": 0.65}, {"module": "auth", "coverage": 0.75}]',
     '[0.5, 0.3]',
     0.8,
     0.785,
     1500,
     true,
     NOW() - INTERVAL '2 hours',
     NOW() - INTERVAL '2 hours' + INTERVAL '1.5 seconds',
     NOW() + INTERVAL '30 days'),

    ('650e8400-e29b-41d4-a716-446655440002',
     'coverage-analyzer',
     '550e8400-e29b-41d4-a716-446655440002',
     'task-002',
     '{"module": "core", "line_coverage": 0.60, "branch_coverage": 0.45}',
     '{"module": "core", "line_coverage": 0.75, "branch_coverage": 0.60}',
     '[{"action": "identify_gaps", "method": "branch_analysis"}, {"action": "suggest_tests", "priority": "high"}]',
     '[{"line_coverage": 0.60}, {"line_coverage": 0.70}, {"line_coverage": 0.75}]',
     '[0.6, 0.4]',
     1.0,
     0.98,
     2000,
     true,
     NOW() - INTERVAL '1 hour',
     NOW() - INTERVAL '1 hour' + INTERVAL '2 seconds',
     NOW() + INTERVAL '30 days')
ON CONFLICT (trajectory_id) DO NOTHING;

-- ============================================================================
-- Sample Rewards
-- ============================================================================

INSERT INTO rewards (agent_type, session_id, trajectory_id, state_hash, action_hash, reward_value, reward_type, reward_source, observed_at) VALUES
    ('test-generator', '550e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440001',
     'a1b2c3d4', 'e5f6g7h8', 0.5, 'immediate', 'test_passed', NOW() - INTERVAL '2 hours'),

    ('test-generator', '550e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440001',
     'm3n4o5p6', 'e5f6g7h8', 0.3, 'delayed', 'coverage_increased', NOW() - INTERVAL '2 hours' + INTERVAL '1 second'),

    ('coverage-analyzer', '550e8400-e29b-41d4-a716-446655440002', '650e8400-e29b-41d4-a716-446655440002',
     'q7r8s9t0', 'u1v2w3x4', 0.6, 'immediate', 'gaps_identified', NOW() - INTERVAL '1 hour'),

    ('coverage-analyzer', '550e8400-e29b-41d4-a716-446655440002', '650e8400-e29b-41d4-a716-446655440002',
     'q7r8s9t0', 'y5z6a7b8', 0.4, 'terminal', 'coverage_target_met', NOW() - INTERVAL '1 hour' + INTERVAL '1 second')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Sample Patterns
-- ============================================================================

INSERT INTO patterns (
    pattern_id, agent_type, pattern_name, pattern_type, pattern_category,
    pattern_data, trigger_conditions, expected_outcome,
    usage_count, success_count, failure_count, avg_reward, confidence_score,
    first_seen, last_used, expires_at
) VALUES
    ('750e8400-e29b-41d4-a716-446655440001',
     'test-generator',
     'AAA Pattern for Unit Tests',
     'test_template',
     'unit_testing',
     '{"template": "def test_{name}():\n    # Arrange\n    {setup}\n    # Act\n    {execution}\n    # Assert\n    {assertion}", "framework": "pytest"}',
     '{"complexity": {"$lt": 5}, "coverage": {"$lt": 0.80}}',
     '{"test_passes": true, "coverage_increase": 0.05}',
     15,
     13,
     2,
     0.65,
     0.87,
     NOW() - INTERVAL '7 days',
     NOW() - INTERVAL '2 hours',
     NOW() + INTERVAL '30 days'),

    ('750e8400-e29b-41d4-a716-446655440002',
     'test-generator',
     'BDD Style Integration Test',
     'test_template',
     'integration_testing',
     '{"template": "def test_{name}():\n    # Given\n    {preconditions}\n    # When\n    {action}\n    # Then\n    {verification}", "framework": "pytest-bdd"}',
     '{"complexity": {"$gte": 5}, "dependencies": {"$exists": true}}',
     '{"integration_success": true, "coverage_increase": 0.10}',
     8,
     7,
     1,
     0.75,
     0.88,
     NOW() - INTERVAL '5 days',
     NOW() - INTERVAL '1 day',
     NOW() + INTERVAL '30 days'),

    ('750e8400-e29b-41d4-a716-446655440003',
     'coverage-analyzer',
     'Branch Coverage Priority',
     'coverage_strategy',
     'gap_analysis',
     '{"strategy": "prioritize_branches", "method": "complexity_weighted", "threshold": 0.80}',
     '{"branch_coverage": {"$lt": 0.80}}',
     '{"gaps_identified": true, "priority_score": {"$gte": 0.70}}',
     20,
     18,
     2,
     0.85,
     0.90,
     NOW() - INTERVAL '10 days',
     NOW() - INTERVAL '1 hour',
     NOW() + INTERVAL '30 days')
ON CONFLICT (agent_type, pattern_name, version) DO NOTHING;

-- ============================================================================
-- Sample Agent States
-- ============================================================================

INSERT INTO agent_states (
    state_id, agent_type, agent_instance_id,
    total_tasks, successful_tasks, failed_tasks,
    total_reward, avg_reward,
    current_exploration_rate, current_learning_rate,
    patterns_learned, q_values_stored,
    status, last_activity, initialized_at, metadata
) VALUES
    ('850e8400-e29b-41d4-a716-446655440001',
     'test-generator',
     'test-generator-1',
     25, 23, 2,
     18.5, 0.74,
     0.15, 0.10,
     2, 3,
     'idle', NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '7 days',
     '{"version": "1.0.0", "skills": ["agentic-quality-engineering", "tdd-london-chicago"]}'),

    ('850e8400-e29b-41d4-a716-446655440002',
     'coverage-analyzer',
     'coverage-analyzer-1',
     15, 15, 0,
     14.0, 0.93,
     0.10, 0.10,
     1, 2,
     'active', NOW() - INTERVAL '1 minute', NOW() - INTERVAL '5 days',
     '{"version": "1.0.0", "skills": ["agentic-quality-engineering", "quality-metrics"]}'),

    ('850e8400-e29b-41d4-a716-446655440003',
     'test-executor',
     'test-executor-1',
     10, 9, 1,
     8.5, 0.85,
     0.20, 0.10,
     0, 0,
     'learning', NOW(), NOW() - INTERVAL '2 days',
     '{"version": "1.0.0", "skills": ["agentic-quality-engineering"]}')
ON CONFLICT (agent_type, agent_instance_id) DO NOTHING;

-- ============================================================================
-- Verify Seed Data
-- ============================================================================

-- Check row counts
DO $$
DECLARE
    v_sessions INT;
    v_q_values INT;
    v_trajectories INT;
    v_rewards INT;
    v_patterns INT;
    v_agent_states INT;
BEGIN
    SELECT COUNT(*) INTO v_sessions FROM sessions;
    SELECT COUNT(*) INTO v_q_values FROM q_values;
    SELECT COUNT(*) INTO v_trajectories FROM trajectories;
    SELECT COUNT(*) INTO v_rewards FROM rewards;
    SELECT COUNT(*) INTO v_patterns FROM patterns;
    SELECT COUNT(*) INTO v_agent_states FROM agent_states;

    RAISE NOTICE '=== Seed Data Summary ===';
    RAISE NOTICE 'Sessions: %', v_sessions;
    RAISE NOTICE 'Q-values: %', v_q_values;
    RAISE NOTICE 'Trajectories: %', v_trajectories;
    RAISE NOTICE 'Rewards: %', v_rewards;
    RAISE NOTICE 'Patterns: %', v_patterns;
    RAISE NOTICE 'Agent States: %', v_agent_states;
END $$;
