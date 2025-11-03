"""Unit tests for TestGeneratorAgent - Test generation agent"""

import pytest
from unittest.mock import AsyncMock, Mock
from lionagi_qe.agents.test_generator import TestGeneratorAgent, GeneratedTest
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel


class TestGeneratedTest:
    """Test GeneratedTest model"""

    def test_generated_test_creation(self):
        """Test creating GeneratedTest"""
        test = GeneratedTest(
            test_name="test_add_function",
            test_code="def test_add(): assert add(2, 3) == 5",
            framework="pytest",
            test_type="unit",
            assertions=["assert add(2, 3) == 5"],
            edge_cases=["negative numbers", "zero"],
            dependencies=["pytest"],
            coverage_estimate=85.0
        )

        assert test.test_name == "test_add_function"
        assert test.framework == "pytest"
        assert test.coverage_estimate == 85.0

    def test_generated_test_defaults(self):
        """Test GeneratedTest default values"""
        test = GeneratedTest(
            test_name="test_basic",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[],
            edge_cases=[]
        )

        assert test.dependencies == []
        assert test.coverage_estimate == 0.0


class TestTestGeneratorAgent:
    """Test TestGeneratorAgent functionality"""

    @pytest.mark.asyncio
    async def test_init(self, qe_memory, simple_model):
        """Test TestGeneratorAgent initialization"""
        agent = TestGeneratorAgent(
            agent_id="test-generator",
            model=simple_model,
            memory=qe_memory,
            skills=["agentic-quality-engineering", "tdd-london-chicago"]
        )

        assert agent.agent_id == "test-generator"
        assert "agentic-quality-engineering" in agent.skills

    @pytest.mark.asyncio
    async def test_system_prompt(self, test_generator_agent):
        """Test system prompt is comprehensive"""
        prompt = test_generator_agent.get_system_prompt()

        # Check for key concepts
        assert "property-based" in prompt.lower() or "testing" in prompt.lower()
        assert "edge case" in prompt.lower() or "boundary" in prompt.lower()
        assert "pytest" in prompt.lower() or "jest" in prompt.lower()

    @pytest.mark.asyncio
    async def test_execute_basic_test_generation(self, test_generator_agent, mocker):
        """Test basic test generation"""
        # Mock the operate method
        mock_result = GeneratedTest(
            test_name="test_calculate_total",
            test_code="""
def test_calculate_total():
    items = [{'price': 10}, {'price': 20}]
    result = calculate_total(items)
    assert result == 33.0  # 30 + 10% tax
""",
            framework="pytest",
            test_type="unit",
            assertions=["assert result == 33.0"],
            edge_cases=["empty list", "negative prices"],
            coverage_estimate=85.0
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def calculate_total(items): return sum(i['price'] for i in items)",
                "framework": "pytest",
                "test_type": "unit"
            }
        )

        result = await test_generator_agent.execute(task)

        assert result.test_name == "test_calculate_total"
        assert result.framework == "pytest"
        assert result.coverage_estimate == 85.0

    @pytest.mark.asyncio
    async def test_execute_with_coverage_target(self, test_generator_agent, mocker):
        """Test generation with specific coverage target"""
        mock_result = GeneratedTest(
            test_name="test_with_high_coverage",
            test_code="test code",
            framework="pytest",
            test_type="unit",
            assertions=["assert True"],
            edge_cases=["boundary cases"],
            coverage_estimate=95.0
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def func(): pass",
                "framework": "pytest",
                "coverage_target": 90
            }
        )

        result = await test_generator_agent.execute(task)

        assert result.coverage_estimate >= 90

    @pytest.mark.asyncio
    async def test_execute_stores_learned_pattern(self, test_generator_agent, mocker):
        """Test that high coverage patterns are learned"""
        mock_result = GeneratedTest(
            test_name="test_learned",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[],
            edge_cases=[],
            coverage_estimate=90.0
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        initial_patterns = test_generator_agent.metrics["patterns_learned"]

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def func(): pass",
                "framework": "pytest",
                "coverage_target": 80
            }
        )

        await test_generator_agent.execute(task)

        # Should have learned a pattern
        assert test_generator_agent.metrics["patterns_learned"] > initial_patterns

    @pytest.mark.asyncio
    async def test_execute_uses_learned_patterns(self, test_generator_agent, mocker):
        """Test that learned patterns are retrieved and used"""
        # Store a learned pattern
        await test_generator_agent.store_learned_pattern(
            "pytest_unit_pattern",
            {
                "framework": "pytest",
                "test_type": "unit",
                "pattern": "high_coverage_achieved",
                "coverage": 92.0
            }
        )

        mock_get_patterns = mocker.patch.object(
            test_generator_agent,
            'get_learned_patterns',
            new=AsyncMock(return_value={
                "aqe/patterns/test-generator/pytest_unit_pattern": {
                    "framework": "pytest",
                    "test_type": "unit",
                    "pattern": "high_coverage_achieved"
                }
            })
        )

        mock_result = GeneratedTest(
            test_name="test_with_patterns",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[],
            edge_cases=[],
            coverage_estimate=93.0
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def func(): pass",
                "framework": "pytest"
            }
        )

        await test_generator_agent.execute(task)

        # Verify patterns were retrieved
        mock_get_patterns.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_different_frameworks(self, test_generator_agent, mocker):
        """Test generation for different test frameworks"""
        frameworks = ["pytest", "jest", "mocha", "cypress"]

        for framework in frameworks:
            mock_result = GeneratedTest(
                test_name=f"test_{framework}",
                test_code="code",
                framework=framework,
                test_type="unit",
                assertions=[],
                edge_cases=[]
            )

            mocker.patch.object(
                test_generator_agent,
                'operate',
                new=AsyncMock(return_value=mock_result)
            )

            task = QETask(
                task_type="test_generation",
                context={
                    "code": "function test() {}",
                    "framework": framework
                }
            )

            result = await test_generator_agent.execute(task)
            assert result.framework == framework

    @pytest.mark.asyncio
    async def test_execute_different_test_types(self, test_generator_agent, mocker):
        """Test generation for different test types"""
        test_types = ["unit", "integration", "e2e"]

        for test_type in test_types:
            mock_result = GeneratedTest(
                test_name=f"test_{test_type}",
                test_code="code",
                framework="pytest",
                test_type=test_type,
                assertions=[],
                edge_cases=[]
            )

            mocker.patch.object(
                test_generator_agent,
                'operate',
                new=AsyncMock(return_value=mock_result)
            )

            task = QETask(
                task_type="test_generation",
                context={
                    "code": "def func(): pass",
                    "test_type": test_type
                }
            )

            result = await test_generator_agent.execute(task)
            assert result.test_type == test_type

    @pytest.mark.asyncio
    async def test_edge_case_detection(self, test_generator_agent, mocker):
        """Test that edge cases are identified"""
        mock_result = GeneratedTest(
            test_name="test_with_edges",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=["assert result"],
            edge_cases=[
                "empty input",
                "null/None values",
                "maximum values",
                "negative numbers",
                "boundary conditions"
            ]
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def calculate(value): return value * 2"
            }
        )

        result = await test_generator_agent.execute(task)

        assert len(result.edge_cases) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_assertions(self, test_generator_agent, mocker):
        """Test that comprehensive assertions are generated"""
        mock_result = GeneratedTest(
            test_name="test_comprehensive",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[
                "assert result is not None",
                "assert isinstance(result, dict)",
                "assert 'key' in result",
                "assert result['key'] == expected"
            ],
            edge_cases=[]
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def get_data(): return {'key': 'value'}"
            }
        )

        result = await test_generator_agent.execute(task)

        assert len(result.assertions) > 0

    @pytest.mark.asyncio
    async def test_default_framework(self, test_generator_agent, mocker):
        """Test default framework is pytest"""
        mock_result = GeneratedTest(
            test_name="test_default",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[],
            edge_cases=[]
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def func(): pass"
                # No framework specified
            }
        )

        result = await test_generator_agent.execute(task)

        assert result.framework == "pytest"

    @pytest.mark.asyncio
    async def test_default_test_type(self, test_generator_agent, mocker):
        """Test default test type is unit"""
        mock_result = GeneratedTest(
            test_name="test_default_type",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[],
            edge_cases=[]
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def func(): pass"
                # No test_type specified
            }
        )

        result = await test_generator_agent.execute(task)

        assert result.test_type == "unit"

    @pytest.mark.asyncio
    async def test_pattern_not_stored_low_coverage(self, test_generator_agent, mocker):
        """Test pattern is not stored when coverage is low"""
        mock_result = GeneratedTest(
            test_name="test_low_coverage",
            test_code="code",
            framework="pytest",
            test_type="unit",
            assertions=[],
            edge_cases=[],
            coverage_estimate=50.0  # Below 80% target
        )

        mocker.patch.object(
            test_generator_agent,
            'operate',
            new=AsyncMock(return_value=mock_result)
        )

        initial_patterns = test_generator_agent.metrics["patterns_learned"]

        task = QETask(
            task_type="test_generation",
            context={
                "code": "def func(): pass",
                "coverage_target": 80
            }
        )

        await test_generator_agent.execute(task)

        # Should not learn pattern
        assert test_generator_agent.metrics["patterns_learned"] == initial_patterns
