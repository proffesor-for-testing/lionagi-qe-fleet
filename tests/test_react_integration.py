"""Tests for ReAct reasoning integration in TestGeneratorAgent"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from lionagi_qe.agents.test_generator import TestGeneratorAgent, GeneratedTest, TestScenario, EdgeCase
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.tools.code_analyzer import CodeAnalyzerTool, ASTParserTool
from lionagi import iModel


# Sample code to test
SAMPLE_CODE = """
def divide(a: float, b: float) -> float:
    '''Divide a by b'''
    return a / b

def calculate_average(numbers: list) -> float:
    '''Calculate average of numbers'''
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
"""


@pytest.fixture
async def test_agent():
    """Create a test agent instance"""
    # Mock iModel
    mock_model = MagicMock(spec=iModel)

    # Mock memory
    mock_memory = MagicMock(spec=QEMemory)
    mock_memory.retrieve = AsyncMock(return_value=None)
    mock_memory.store = AsyncMock()
    mock_memory.search = AsyncMock(return_value={})

    agent = TestGeneratorAgent(
        agent_id="test-generator",
        model=mock_model,
        memory=mock_memory,
        enable_learning=True
    )

    return agent


@pytest.mark.asyncio
async def test_code_analyzer_tool():
    """Test CodeAnalyzerTool can analyze code structure"""
    tool = CodeAnalyzerTool()

    result = tool.analyze_code(code_content=SAMPLE_CODE)

    # Verify structure extraction
    assert "functions" in result
    assert "classes" in result
    assert "complexity" in result
    assert "dependencies" in result

    # Verify function extraction
    assert len(result["functions"]) == 2
    function_names = [f["name"] for f in result["functions"]]
    assert "divide" in function_names
    assert "calculate_average" in function_names

    # Verify complexity analysis
    assert "divide" in result["complexity"]
    assert "calculate_average" in result["complexity"]

    print(f"✓ CodeAnalyzerTool successfully analyzed {len(result['functions'])} functions")


@pytest.mark.asyncio
async def test_ast_parser_edge_cases():
    """Test ASTParserTool can detect edge cases"""
    tool = ASTParserTool()

    result = tool.detect_edge_cases(code_content=SAMPLE_CODE)

    # Verify edge case detection
    assert "boundary_checks" in result
    assert "null_checks" in result
    assert "total_edge_cases" in result

    # Should detect division in divide() function
    boundary_checks = result["boundary_checks"]
    assert len(boundary_checks) > 0

    division_checks = [b for b in boundary_checks if b["type"] == "division"]
    assert len(division_checks) > 0

    print(f"✓ ASTParserTool detected {result['total_edge_cases']} potential edge cases")


@pytest.mark.asyncio
async def test_pydantic_models():
    """Test Pydantic models are correctly defined"""
    # Test TestScenario
    scenario = TestScenario(
        scenario_name="test_division_by_zero",
        description="Test handling of division by zero",
        test_type="edge_case",
        priority="critical",
        estimated_coverage=15.0
    )

    assert scenario.scenario_name == "test_division_by_zero"
    assert scenario.priority == "critical"
    assert scenario.estimated_coverage == 15.0

    # Test EdgeCase
    edge_case = EdgeCase(
        case_name="division_by_zero",
        description="Dividing by zero should raise ZeroDivisionError",
        risk_level="high",
        test_approach="Use pytest.raises to verify exception"
    )

    assert edge_case.case_name == "division_by_zero"
    assert edge_case.risk_level == "high"

    # Test GeneratedTest
    test = GeneratedTest(
        test_name="test_divide",
        test_code="def test_divide(): assert divide(10, 2) == 5",
        framework="pytest",
        test_type="unit",
        assertions=["divide(10, 2) == 5"],
        edge_cases=["division_by_zero"],
        coverage_estimate=85.0
    )

    assert test.test_name == "test_divide"
    assert test.framework == "pytest"
    assert test.coverage_estimate == 85.0

    print("✓ All Pydantic models are correctly defined")


@pytest.mark.asyncio
async def test_execute_with_reasoning_structure(test_agent):
    """Test execute_with_reasoning method structure (mocked)"""

    # Create task
    task = QETask(
        task_id="test-1",
        task_type="generate",
        context={
            "code": SAMPLE_CODE,
            "framework": "pytest",
            "test_type": "unit",
            "coverage_target": 80
        }
    )

    # Mock the branch.ReAct method
    mock_react_result = {
        "response": GeneratedTest(
            test_name="test_divide_comprehensive",
            test_code="""
def test_divide_normal_case():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
""",
            framework="pytest",
            test_type="unit",
            assertions=["divide(10, 2) == 5.0"],
            edge_cases=["division_by_zero"],
            coverage_estimate=90.0
        ),
        "trace": [
            {
                "thought": "I need to analyze the code structure",
                "action": "analyze_code",
                "action_input": {"code_content": SAMPLE_CODE},
                "observation": {"functions": ["divide", "calculate_average"]}
            },
            {
                "thought": "I identified edge case: division by zero",
                "intermediate": EdgeCase(
                    case_name="division_by_zero",
                    description="Division by zero",
                    risk_level="high",
                    test_approach="pytest.raises"
                )
            }
        ]
    }

    # Patch the branch.ReAct method
    with patch.object(test_agent.branch, 'ReAct', new_callable=AsyncMock) as mock_react:
        mock_react.return_value = mock_react_result

        # Execute with reasoning
        result = await test_agent.execute_with_reasoning(task, verbose=True)

        # Verify result structure
        assert "final_tests" in result
        assert "scenarios_identified" in result
        assert "edge_cases_identified" in result
        assert "reasoning_steps" in result
        assert "tool_calls" in result
        assert "quality_improvement" in result

        # Verify final_tests
        assert isinstance(result["final_tests"], GeneratedTest)
        assert result["final_tests"].framework == "pytest"

        # Verify ReAct was called with correct parameters
        mock_react.assert_called_once()
        call_args = mock_react.call_args

        # Check instruction was passed
        assert "instruct" in call_args.kwargs
        assert "tools" in call_args.kwargs
        assert "max_extensions" in call_args.kwargs

        # Check tools were registered
        tools = call_args.kwargs["tools"]
        assert len(tools) == 2  # CodeAnalyzerTool and ASTParserTool

        print("✓ execute_with_reasoning has correct structure")
        print(f"  - Edge cases identified: {len(result['edge_cases_identified'])}")
        print(f"  - Tool calls: {len(result['tool_calls'])}")
        print(f"  - Quality improvement: {result['quality_improvement']:.1f}%")


@pytest.mark.asyncio
async def test_reasoning_fallback(test_agent):
    """Test fallback to standard generation if ReAct fails"""

    task = QETask(
        task_id="test-2",
        task_type="generate",
        context={
            "code": SAMPLE_CODE,
            "framework": "pytest"
        }
    )

    # Mock execute() method (standard generation)
    mock_standard_result = GeneratedTest(
        test_name="test_fallback",
        test_code="def test_fallback(): pass",
        framework="pytest",
        test_type="unit",
        assertions=[],
        edge_cases=[],
        coverage_estimate=50.0
    )

    # Mock ReAct to raise exception
    with patch.object(test_agent.branch, 'ReAct', new_callable=AsyncMock) as mock_react, \
         patch.object(test_agent, 'execute', new_callable=AsyncMock) as mock_execute:

        mock_react.side_effect = Exception("ReAct failed")
        mock_execute.return_value = mock_standard_result

        # Execute with reasoning (should fallback)
        result = await test_agent.execute_with_reasoning(task, verbose=False)

        # Verify fallback occurred
        assert "error" in result
        assert result["final_tests"] == mock_standard_result
        assert result["quality_improvement"] == 0.0

        # Verify execute was called as fallback
        mock_execute.assert_called_once()

        print("✓ Fallback to standard generation works correctly")


@pytest.mark.asyncio
async def test_tools_integration():
    """Test that tools are properly integrated with ReAct"""

    # Test CodeAnalyzerTool function signature
    tool = CodeAnalyzerTool()
    result = tool.analyze_code(code_content="def foo(): pass")

    assert isinstance(result, dict)
    assert "functions" in result

    # Test ASTParserTool function signature
    parser = ASTParserTool()
    result = parser.detect_edge_cases(code_content="def divide(a, b): return a / b")

    assert isinstance(result, dict)
    assert "boundary_checks" in result

    # Verify tools can be passed as callables (which is what ReAct accepts)
    # LionAGI automatically wraps callables in Tool objects
    assert callable(tool.analyze_code)
    assert callable(parser.detect_edge_cases)

    # Test that we can pass them to ReAct as tools list
    tools = [tool.analyze_code, parser.detect_edge_cases]
    assert len(tools) == 2
    assert all(callable(t) for t in tools)

    print("✓ Tools are properly integrated with ReAct")


def test_example_reasoning_flow():
    """Document example reasoning flow for reference"""

    example_flow = """
    ReAct Reasoning Flow Example:

    Step 1 (Think): "I need to analyze the code structure to understand testable units"
    Step 2 (Act): Call CodeAnalyzerTool.analyze_code(code_content="def divide(a, b): return a / b")
    Step 3 (Observe): {
        "functions": [{"name": "divide", "args": ["a", "b"], ...}],
        "complexity": {"divide": 1},
        "dependencies": []
    }
    Step 4 (Think): "I identified function 'divide' with potential edge case: division by zero"
    Step 5 (Act): Generate TestScenario(
        scenario_name="test_divide_normal",
        description="Test normal division cases",
        test_type="unit",
        priority="medium"
    )
    Step 6 (Act): Call ASTParserTool.detect_edge_cases(code_content="...")
    Step 7 (Observe): {
        "boundary_checks": [{"type": "division", "edge_case": "Division by zero"}],
        "total_edge_cases": 1
    }
    Step 8 (Act): Generate EdgeCase(
        case_name="division_by_zero",
        description="Division by zero should raise ZeroDivisionError",
        risk_level="high",
        test_approach="Use pytest.raises"
    )
    Step 9 (Think): "All scenarios and edge cases identified. Ready to generate comprehensive tests"
    Step 10 (Final): Generate GeneratedTest with:
        - test_normal_division()
        - test_division_by_zero()
        - test_division_negative_numbers()
        - Coverage: 95%

    Result:
    - 3 test scenarios identified
    - 2 edge cases identified
    - 8 reasoning steps
    - 2 tool calls
    - 40% quality improvement vs standard generation
    """

    print(example_flow)
    print("✓ Example reasoning flow documented")


if __name__ == "__main__":
    # Run basic tests
    import asyncio

    async def main():
        print("\n=== Testing ReAct Integration ===\n")

        # Test 1: Code analyzer
        await test_code_analyzer_tool()

        # Test 2: AST parser
        await test_ast_parser_edge_cases()

        # Test 3: Pydantic models
        await test_pydantic_models()

        # Test 4: Tools integration
        await test_tools_integration()

        # Test 5: Example flow
        test_example_reasoning_flow()

        print("\n=== All Tests Passed ===\n")

    asyncio.run(main())
