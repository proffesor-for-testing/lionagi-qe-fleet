"""Shared pytest fixtures for Q-Learning tests

This module provides mock fixtures for:
- Database connections and pools
- Q-Learning services and components
- Sample tasks, states, and trajectories
- Mock agents with learning capabilities
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime

# Import core types
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_db_pool(mocker):
    """Mock asyncpg database connection pool"""
    pool = mocker.AsyncMock()

    # Mock fetchrow - returns single row
    pool.fetchrow = AsyncMock(return_value={
        "q_value": 0.5,
        "visits": 10,
        "confidence": 0.8,
        "version": 1
    })

    # Mock fetch - returns multiple rows
    pool.fetch = AsyncMock(return_value=[
        {"q_value": 0.5, "action": 1},
        {"q_value": 0.7, "action": 2},
        {"q_value": 0.3, "action": 3}
    ])

    # Mock execute - for inserts/updates
    pool.execute = AsyncMock(return_value="INSERT 0 1")

    # Mock fetchval - returns single value
    pool.fetchval = AsyncMock(return_value=0.5)

    return pool


@pytest.fixture
async def mock_db_connection(mocker):
    """Mock single database connection"""
    conn = mocker.AsyncMock()

    # Transaction support
    conn.transaction = Mock(return_value=AsyncMock())

    # Query methods
    conn.fetchrow = AsyncMock(return_value={"id": 1})
    conn.execute = AsyncMock(return_value="UPDATE 1")

    return conn


@pytest.fixture
def mock_db_manager(mocker, mock_db_pool):
    """Mock DatabaseManager for Q-learning"""
    manager = mocker.Mock()
    manager.pool = mock_db_pool
    manager.initialize = AsyncMock()
    manager.close = AsyncMock()
    manager.get_q_value = AsyncMock(return_value=0.5)
    manager.update_q_value = AsyncMock()
    manager.store_experience = AsyncMock()
    manager.sample_experiences = AsyncMock(return_value=[])

    return manager


# ============================================================================
# Q-Learning Component Fixtures
# ============================================================================

@pytest.fixture
def mock_state_encoder(mocker):
    """Mock StateEncoder for encoding task states"""
    encoder = mocker.Mock()
    encoder.encode = Mock(return_value="encoded_state_hash")
    encoder.extract_features = Mock(return_value={
        "complexity": 5,
        "size": 100,
        "coverage": 0.75,
        "framework": "pytest"
    })
    encoder.bucket_complexity = Mock(return_value="medium")
    encoder.bucket_size = Mock(return_value="medium")
    encoder.bucket_coverage = Mock(return_value="high")

    return encoder


@pytest.fixture
def mock_reward_calculator(mocker):
    """Mock RewardCalculator for computing rewards"""
    calculator = mocker.Mock()
    calculator.calculate = Mock(return_value=10.0)
    calculator.coverage_reward = Mock(return_value=3.0)
    calculator.quality_reward = Mock(return_value=2.5)
    calculator.time_reward = Mock(return_value=1.5)
    calculator.pattern_bonus = Mock(return_value=1.0)

    return calculator


@pytest.fixture
async def mock_q_service(mocker, mock_db_manager, mock_state_encoder, mock_reward_calculator):
    """Mock QLearningService for testing"""
    service = mocker.Mock()
    service.db_manager = mock_db_manager
    service.state_encoder = mock_state_encoder
    service.reward_calculator = mock_reward_calculator

    # Core Q-learning methods
    service.select_action = AsyncMock(return_value=1)
    service.update_q_value = AsyncMock()
    service.get_q_value = AsyncMock(return_value=0.5)
    service.get_best_action = AsyncMock(return_value=2)
    service.get_max_q_value = AsyncMock(return_value=0.8)

    # Experience replay
    service.store_experience = AsyncMock()
    service.replay_experiences = AsyncMock()

    # Configuration
    service.alpha = 0.1  # Learning rate
    service.gamma = 0.95  # Discount factor
    service.epsilon = 0.2  # Exploration rate

    return service


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_qe_task():
    """Create sample QE task for testing"""
    return QETask(
        task_type="test_generation",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest",
            "test_type": "unit",
            "complexity": 5,
            "coverage_target": 0.8,
            "current_coverage": 0.6
        },
        priority="medium"
    )


@pytest.fixture
def sample_task_factory():
    """Factory for creating various QE tasks"""
    def create_task(
        task_type: str = "test_generation",
        complexity: int = 5,
        coverage: float = 0.6,
        framework: str = "pytest"
    ) -> QETask:
        return QETask(
            task_type=task_type,
            context={
                "code": f"# Code with complexity {complexity}",
                "framework": framework,
                "complexity": complexity,
                "coverage_target": 0.8,
                "current_coverage": coverage
            },
            priority="medium"
        )

    return create_task


@pytest.fixture
def sample_state():
    """Sample encoded state"""
    return "test_gen_complexity_medium_coverage_high_pytest"


@pytest.fixture
def sample_trajectory():
    """Sample learning trajectory (state, action, reward, next_state)"""
    return {
        "agent_id": "test-generator",
        "state": "test_gen_complexity_medium_coverage_high_pytest",
        "action": 2,
        "reward": 10.5,
        "next_state": "test_gen_complexity_medium_coverage_higher_pytest",
        "done": False,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "task_id": "task-123",
            "execution_time": 2.5,
            "tests_generated": 15
        }
    }


@pytest.fixture
def sample_q_values():
    """Sample Q-value table entries"""
    return {
        ("state1", 0): 0.5,
        ("state1", 1): 0.7,
        ("state1", 2): 0.3,
        ("state2", 0): 0.8,
        ("state2", 1): 0.6,
        ("state2", 2): 0.9
    }


@pytest.fixture
def sample_experiences():
    """Sample experience replay buffer"""
    return [
        {
            "state": "state1",
            "action": 1,
            "reward": 10.0,
            "next_state": "state2",
            "done": False,
            "priority": 1.0
        },
        {
            "state": "state2",
            "action": 2,
            "reward": 15.0,
            "next_state": "state3",
            "done": False,
            "priority": 1.5
        },
        {
            "state": "state3",
            "action": 0,
            "reward": 5.0,
            "next_state": "state4",
            "done": True,
            "priority": 0.5
        }
    ]


# ============================================================================
# Agent Fixtures with Learning
# ============================================================================

@pytest.fixture
async def qe_memory():
    """Create fresh QE memory instance"""
    return QEMemory()


@pytest.fixture
def simple_model():
    """Create simple test model"""
    return iModel(provider="openai", model="gpt-3.5-turbo")


@pytest.fixture
async def learning_enabled_agent(qe_memory, simple_model, mock_q_service):
    """Create agent with learning enabled"""
    from lionagi_qe.core.base_agent import BaseQEAgent

    class TestLearningAgent(BaseQEAgent):
        def get_system_prompt(self) -> str:
            return "Test learning agent"

        async def execute(self, task: QETask):
            return {
                "tests_generated": 10,
                "coverage": 0.85,
                "execution_time": 2.5
            }

    agent = TestLearningAgent(
        agent_id="learning-agent",
        model=simple_model,
        memory=qe_memory,
        skills=["agentic-quality-engineering"],
        enable_learning=True
    )

    # Inject mock Q-learning service
    agent.q_service = mock_q_service

    return agent


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_states(count: int = 10) -> List[str]:
    """Generate multiple test states"""
    return [
        f"state_{i}_complexity_medium_coverage_high"
        for i in range(count)
    ]


def generate_q_table(states: List[str], actions: List[int]) -> Dict:
    """Generate Q-table with random values"""
    import random
    q_table = {}
    for state in states:
        for action in actions:
            q_table[(state, action)] = random.uniform(0, 1)
    return q_table


def generate_trajectories(agent_id: str, count: int = 5) -> List[Dict]:
    """Generate multiple learning trajectories"""
    trajectories = []
    for i in range(count):
        trajectories.append({
            "agent_id": agent_id,
            "state": f"state_{i}",
            "action": i % 3,
            "reward": 5.0 + i,
            "next_state": f"state_{i+1}",
            "done": i == count - 1,
            "timestamp": datetime.now().isoformat()
        })
    return trajectories


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_q_value_in_range(q_value: float, min_val: float = 0.0, max_val: float = 1.0):
    """Assert Q-value is within valid range"""
    assert min_val <= q_value <= max_val, \
        f"Q-value {q_value} out of range [{min_val}, {max_val}]"


def assert_state_encoded(state: str):
    """Assert state is properly encoded"""
    assert isinstance(state, str)
    assert len(state) > 0
    assert state != "None"


def assert_trajectory_valid(trajectory: Dict):
    """Assert trajectory has all required fields"""
    required_fields = ["agent_id", "state", "action", "reward", "next_state", "done"]
    for field in required_fields:
        assert field in trajectory, f"Missing field: {field}"

    assert isinstance(trajectory["reward"], (int, float))
    assert isinstance(trajectory["done"], bool)


# ============================================================================
# Database Cleanup Fixtures
# ============================================================================

@pytest.fixture
async def clean_db(mock_db_pool):
    """Clean database before/after tests"""
    # Setup: clear tables
    await mock_db_pool.execute("DELETE FROM q_values")
    await mock_db_pool.execute("DELETE FROM learning_experiences")

    yield

    # Teardown: clear tables again
    await mock_db_pool.execute("DELETE FROM q_values")
    await mock_db_pool.execute("DELETE FROM learning_experiences")


@pytest.fixture
def agent_types():
    """List of all 18 agent types for testing"""
    return [
        "test-generator",
        "test-executor",
        "coverage-analyzer",
        "quality-gate",
        "quality-analyzer",
        "performance-tester",
        "security-scanner",
        "requirements-validator",
        "production-intelligence",
        "fleet-commander",
        "deployment-readiness",
        "regression-risk-analyzer",
        "test-data-architect",
        "api-contract-validator",
        "flaky-test-hunter",
        "visual-tester",
        "chaos-engineer",
        "mobile-tester"
    ]


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def q_learning_config():
    """Q-learning configuration for testing"""
    return {
        "learning_rate": 0.1,
        "discount_factor": 0.95,
        "initial_epsilon": 0.2,
        "min_epsilon": 0.01,
        "epsilon_decay": 0.995,
        "experience_buffer_size": 10000,
        "batch_size": 32,
        "update_frequency": 4
    }


@pytest.fixture
def reward_weights():
    """Reward calculation weights"""
    return {
        "coverage": 0.30,
        "quality": 0.25,
        "time": 0.15,
        "cost": 0.10,
        "improvement": 0.10,
        "reusability": 0.10
    }
