"""Shared pytest fixtures for LionAGI QE Fleet tests"""

import pytest
import asyncio
import warnings
from typing import Dict, Any
from lionagi import iModel
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.fleet import QEFleet
from lionagi_qe.core.router import ModelRouter
from lionagi_qe.core.task import QETask
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.agents.test_generator import TestGeneratorAgent
from lionagi_qe.agents.test_executor import TestExecutorAgent
from lionagi_qe.agents.fleet_commander import FleetCommanderAgent
from lionagi_qe.agents.flaky_test_hunter import FlakyTestHunterAgent


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real databases"
    )
    config.addinivalue_line(
        "markers", "postgres: mark test as requiring PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def qe_memory():
    """Create a fresh QE memory instance"""
    return QEMemory()


@pytest.fixture
def model_router():
    """Create a model router instance"""
    return ModelRouter(enable_routing=False)  # Disable for tests


@pytest.fixture
def simple_model():
    """Create a simple test model"""
    return iModel(provider="openai", model="gpt-3.5-turbo")


@pytest.fixture
async def qe_orchestrator(qe_memory, model_router):
    """Create QE orchestrator with memory and router"""
    return QEOrchestrator(
        memory=qe_memory,
        router=model_router,
        enable_learning=False
    )


@pytest.fixture
async def qe_fleet():
    """Create QE fleet instance
    
    Returns actual QEFleet wrapper (not just orchestrator).
    Tests expect fleet.orchestrator to exist.
    """
    fleet = QEFleet(
        enable_routing=False,
        enable_learning=False
    )
    await fleet.initialize()
    return fleet


@pytest.fixture
async def test_generator_agent(qe_memory, simple_model):
    """Create test generator agent"""
    return TestGeneratorAgent(
        agent_id="test-generator",
        model=simple_model,
        memory=qe_memory,
        skills=["agentic-quality-engineering", "tdd-london-chicago"],
        enable_learning=False
    )


@pytest.fixture
async def test_executor_agent(qe_memory, simple_model):
    """Create test executor agent"""
    return TestExecutorAgent(
        agent_id="test-executor",
        model=simple_model,
        memory=qe_memory,
        skills=["agentic-quality-engineering"],
        enable_learning=False
    )


@pytest.fixture
async def fleet_commander_agent(qe_memory, simple_model):
    """Create fleet commander agent"""
    return FleetCommanderAgent(
        agent_id="fleet-commander",
        model=simple_model,
        memory=qe_memory,
        skills=["agentic-quality-engineering", "holistic-testing-pact"],
        enable_learning=False
    )


@pytest.fixture
async def flaky_test_hunter_agent(qe_memory, simple_model):
    """Create flaky test hunter agent"""
    return FlakyTestHunterAgent(
        agent_id="flaky-test-hunter",
        model=simple_model,
        memory=qe_memory,
        skills=["agentic-quality-engineering"],
        enable_learning=False
    )


@pytest.fixture
def sample_qe_task():
    """Create a sample QE task"""
    return QETask(
        task_type="test_generation",
        context={
            "code": "def add(a, b): return a + b",
            "framework": "pytest",
            "test_type": "unit"
        },
        priority="medium"
    )


@pytest.fixture
def sample_code():
    """Sample Python code for testing"""
    return """
def calculate_total(items):
    '''Calculate total price with tax'''
    subtotal = sum(item['price'] for item in items)
    tax = subtotal * 0.1
    return subtotal + tax

class UserService:
    def __init__(self, db):
        self.db = db

    def create_user(self, name, email):
        if self.db.exists(email):
            raise ValueError("Email already exists")
        user = {"name": name, "email": email}
        return self.db.save(user)
"""


@pytest.fixture
def sample_test_suite():
    """Sample test suite for execution"""
    return """
import pytest

def test_add():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 5) == 5
"""


@pytest.fixture
def complex_task_context():
    """Complex task context for hierarchical coordination"""
    return {
        "request": """
        We need comprehensive QE for a new REST API:
        - Generate unit tests for all endpoints
        - Execute integration tests
        - Perform security scanning
        - Run performance benchmarks
        - Validate API contracts
        - Check code coverage
        """,
        "target": "production",
        "frameworks": ["pytest", "k6"],
        "coverage_threshold": 80
    }


# Mock objects for external dependencies

@pytest.fixture
def mock_lionagi_branch(mocker):
    """Mock LionAGI Branch for testing"""
    mock_branch = mocker.MagicMock()
    mock_branch.communicate = mocker.AsyncMock(return_value="Mock response")
    mock_branch.operate = mocker.AsyncMock()
    return mock_branch


@pytest.fixture
def mock_db():
    """Mock database for testing"""
    class MockDB:
        def __init__(self):
            self.data = {}

        def exists(self, key):
            return key in self.data

        def save(self, item):
            self.data[item.get('email', 'unknown')] = item
            return item

        def get(self, key):
            return self.data.get(key)

    return MockDB()


# Test data generators

def generate_test_tasks(count: int = 5):
    """Generate multiple test tasks"""
    return [
        QETask(
            task_type=f"test_task_{i}",
            context={"data": f"task_{i}"},
            priority="medium"
        )
        for i in range(count)
    ]


def generate_agent_results(count: int = 3):
    """Generate mock agent results"""
    return [
        {
            "agent_id": f"agent_{i}",
            "status": "completed",
            "result": {
                "tests_generated": 10 + i,
                "coverage": 85.0 + i,
                "duration": 1.5 + (i * 0.5)
            }
        }
        for i in range(count)
    ]


# Assertions helpers

def assert_task_completed(task: QETask):
    """Assert task is completed successfully"""
    assert task.status == "completed"
    assert task.result is not None
    assert task.error is None
    assert task.completed_at is not None


def assert_task_failed(task: QETask):
    """Assert task failed with error"""
    assert task.status == "failed"
    assert task.error is not None
    assert task.completed_at is not None


def assert_memory_key_exists(memory: QEMemory, key: str):
    """Assert memory key exists (async wrapper needed)"""
    async def _check():
        value = await memory.retrieve(key)
        assert value is not None
        return value
    return _check()
