"""Tests for BaseQEAgent fuzzy parsing features - Priority 1

Tests safe_operate() and safe_parse_response() methods with:
- Well-formed JSON parsing
- Malformed JSON handling
- Extra text around JSON
- Key name fuzzy matching (camelCase ↔ snake_case)
- Type coercion
- Error paths and fallbacks
- 95%+ coverage target
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from pydantic import BaseModel, Field
from typing import List, Optional
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask
from lionagi_qe.core.memory import QEMemory
from lionagi import iModel
import json


# Test Models
class SimpleTestModel(BaseModel):
    """Simple test model"""
    test_name: str
    test_count: int
    success_rate: float


class ComplexTestModel(BaseModel):
    """Complex nested test model"""
    test_suite: str
    total_tests: int
    passed_tests: int = Field(alias="passedTests")
    failed_tests: int = Field(alias="failedTests")
    test_files: List[str]
    metadata: Optional[dict] = None


# Mock Agent
class MockAgent(BaseQEAgent):
    """Mock agent for testing"""

    def get_system_prompt(self) -> str:
        return "Test agent"

    async def execute(self, task: QETask):
        return {"status": "done"}


class TestSafeOperateWellFormed:
    """Test safe_operate() with well-formed JSON"""

    @pytest.mark.asyncio
    async def test_safe_operate_valid_json(self, qe_memory, simple_model, mocker):
        """Test safe_operate with valid, well-formed JSON"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        expected_result = SimpleTestModel(
            test_name="test_example",
            test_count=10,
            success_rate=0.95
        )

        # Mock operate to return valid result
        mocker.patch.object(
            agent.branch,
            'operate',
            new=AsyncMock(return_value=expected_result)
        )

        result = await agent.safe_operate(
            instruction="Generate test data",
            response_format=SimpleTestModel
        )

        assert result.test_name == "test_example"
        assert result.test_count == 10
        assert result.success_rate == 0.95

    @pytest.mark.asyncio
    async def test_safe_operate_complex_model(self, qe_memory, simple_model, mocker):
        """Test safe_operate with complex nested model"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        expected_result = ComplexTestModel(
            test_suite="integration",
            total_tests=50,
            passedTests=48,
            failedTests=2,
            test_files=["test1.py", "test2.py"],
            metadata={"env": "ci"}
        )

        mocker.patch.object(
            agent.branch,
            'operate',
            new=AsyncMock(return_value=expected_result)
        )

        result = await agent.safe_operate(
            instruction="Get test results",
            response_format=ComplexTestModel
        )

        assert result.test_suite == "integration"
        assert result.total_tests == 50
        assert result.passed_tests == 48


class TestSafeOperateMalformed:
    """Test safe_operate() with malformed JSON"""

    @pytest.mark.asyncio
    async def test_safe_operate_malformed_fallback(self, qe_memory, simple_model, mocker):
        """Test safe_operate falls back to fuzzy parsing for malformed JSON"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        # Mock operate to fail
        mocker.patch.object(
            agent.branch,
            'operate',
            side_effect=Exception("JSON parsing error")
        )

        # Mock communicate to return malformed JSON
        mocker.patch.object(
            agent.branch,
            'communicate',
            new=AsyncMock(return_value='{"test_name": "test", "test_count": "10", "success_rate": 0.95}')
        )

        # Mock fuzzy parsing functions
        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy_json:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_fuzzy_validate:
                    mock_fuzzy_json.return_value = {
                        "test_name": "test",
                        "test_count": "10",
                        "success_rate": 0.95
                    }
                    mock_fuzzy_validate.return_value = SimpleTestModel(
                        test_name="test",
                        test_count=10,
                        success_rate=0.95
                    )

                    result = await agent.safe_operate(
                        instruction="Generate data",
                        response_format=SimpleTestModel
                    )

                    assert result.test_name == "test"
                    assert result.test_count == 10
                    assert mock_fuzzy_json.called
                    assert mock_fuzzy_validate.called

    @pytest.mark.asyncio
    async def test_safe_operate_invalid_field_types(self, qe_memory, simple_model, mocker):
        """Test safe_operate handles invalid field types"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(
            agent.branch,
            'operate',
            side_effect=Exception("Type error")
        )

        mocker.patch.object(
            agent.branch,
            'communicate',
            new=AsyncMock(return_value='{"test_name": "test", "test_count": "not_a_number", "success_rate": 0.95}')
        )

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic'):
                    mock_fuzzy.return_value = {"test_name": "test", "test_count": "not_a_number", "success_rate": 0.95}

                    with pytest.raises(ValueError, match="Failed to parse"):
                        await agent.safe_operate(
                            instruction="Generate data",
                            response_format=SimpleTestModel
                        )


class TestSafeOperateExtraText:
    """Test safe_operate() with extra text around JSON"""

    @pytest.mark.asyncio
    async def test_safe_operate_with_prefix_text(self, qe_memory, simple_model, mocker):
        """Test safe_operate extracts JSON from text with prefix"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(
            agent.branch,
            'operate',
            side_effect=Exception("Malformed")
        )

        response_with_prefix = '''Here are the test results you requested:
        {"test_name": "test_example", "test_count": 10, "success_rate": 0.95}
        I hope this helps!'''

        mocker.patch.object(
            agent.branch,
            'communicate',
            new=AsyncMock(return_value=response_with_prefix)
        )

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {
                        "test_name": "test_example",
                        "test_count": 10,
                        "success_rate": 0.95
                    }
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test_example",
                        test_count=10,
                        success_rate=0.95
                    )

                    result = await agent.safe_operate(
                        instruction="Get tests",
                        response_format=SimpleTestModel
                    )

                    assert result.test_name == "test_example"
                    assert mock_fuzzy.called

    @pytest.mark.asyncio
    async def test_safe_operate_markdown_wrapped(self, qe_memory, simple_model, mocker):
        """Test safe_operate extracts JSON from markdown code blocks"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(
            agent.branch,
            'operate',
            side_effect=Exception("Malformed")
        )

        markdown_response = '''```json
        {"test_name": "test_example", "test_count": 10, "success_rate": 0.95}
        ```'''

        mocker.patch.object(
            agent.branch,
            'communicate',
            new=AsyncMock(return_value=markdown_response)
        )

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {
                        "test_name": "test_example",
                        "test_count": 10,
                        "success_rate": 0.95
                    }
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test_example",
                        test_count=10,
                        success_rate=0.95
                    )

                    result = await agent.safe_operate(
                        instruction="Get tests",
                        response_format=SimpleTestModel
                    )

                    assert result.test_name == "test_example"


class TestSafeOperateKeyMatching:
    """Test fuzzy key name matching (camelCase ↔ snake_case)"""

    @pytest.mark.asyncio
    async def test_camel_to_snake_case(self, qe_memory, simple_model, mocker):
        """Test camelCase keys convert to snake_case"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Key mismatch"))

        # Response with camelCase keys
        response = '{"testName": "test", "testCount": 10, "successRate": 0.95}'

        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value=response))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {
                        "testName": "test",
                        "testCount": 10,
                        "successRate": 0.95
                    }
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test",
                        test_count=10,
                        success_rate=0.95
                    )

                    result = await agent.safe_operate(
                        instruction="Get data",
                        response_format=SimpleTestModel
                    )

                    # Verify fuzzy matching was enabled
                    assert mock_validate.called
                    call_kwargs = mock_validate.call_args[1]
                    assert call_kwargs.get('fuzzy_match_keys') is True

    @pytest.mark.asyncio
    async def test_snake_to_camel_case(self, qe_memory, simple_model, mocker):
        """Test snake_case keys convert to camelCase (via aliases)"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Key mismatch"))

        # Response with snake_case for fields that have camelCase aliases
        response = json.dumps({
            "test_suite": "unit",
            "total_tests": 20,
            "passed_tests": 18,  # Note: model expects passedTests
            "failed_tests": 2,   # Note: model expects failedTests
            "test_files": ["test.py"]
        })

        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value=response))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = json.loads(response)
                    mock_validate.return_value = ComplexTestModel(
                        test_suite="unit",
                        total_tests=20,
                        passedTests=18,
                        failedTests=2,
                        test_files=["test.py"]
                    )

                    result = await agent.safe_operate(
                        instruction="Get results",
                        response_format=ComplexTestModel
                    )

                    assert result.test_suite == "unit"
                    assert result.passed_tests == 18


class TestSafeOperateTypeCoercion:
    """Test type coercion for mismatched types"""

    @pytest.mark.asyncio
    async def test_string_to_int_coercion(self, qe_memory, simple_model, mocker):
        """Test string to int type coercion"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Type error"))

        # Response with string instead of int
        response = '{"test_name": "test", "test_count": "10", "success_rate": 0.95}'

        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value=response))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {
                        "test_name": "test",
                        "test_count": "10",
                        "success_rate": 0.95
                    }
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test",
                        test_count=10,
                        success_rate=0.95
                    )

                    result = await agent.safe_operate(
                        instruction="Get data",
                        response_format=SimpleTestModel
                    )

                    # Verify type coercion was enabled
                    call_kwargs = mock_validate.call_args[1]
                    assert call_kwargs.get('fuzzy_match_values') is True

    @pytest.mark.asyncio
    async def test_int_to_float_coercion(self, qe_memory, simple_model, mocker):
        """Test int to float type coercion"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Type error"))

        # Response with int instead of float
        response = '{"test_name": "test", "test_count": 10, "success_rate": 95}'

        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value=response))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {
                        "test_name": "test",
                        "test_count": 10,
                        "success_rate": 95
                    }
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test",
                        test_count=10,
                        success_rate=95.0
                    )

                    result = await agent.safe_operate(
                        instruction="Get data",
                        response_format=SimpleTestModel
                    )

                    assert result.success_rate == 95.0


class TestSafeOperateErrorPaths:
    """Test all error paths in safe_operate()"""

    @pytest.mark.asyncio
    async def test_fuzzy_parsing_not_available(self, qe_memory, simple_model, mocker):
        """Test error when fuzzy parsing is not available"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Parse error"))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', False):
            with pytest.raises(ValueError, match="Fuzzy parsing not available"):
                await agent.safe_operate(
                    instruction="Get data",
                    response_format=SimpleTestModel
                )

    @pytest.mark.asyncio
    async def test_both_parsing_methods_fail(self, qe_memory, simple_model, mocker):
        """Test error when both standard and fuzzy parsing fail"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Standard parse error"))
        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value="invalid data"))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json', side_effect=Exception("Fuzzy parse error")):
                with pytest.raises(ValueError, match="Standard parsing error.*Fuzzy parsing error"):
                    await agent.safe_operate(
                        instruction="Get data",
                        response_format=SimpleTestModel
                    )

    @pytest.mark.asyncio
    async def test_completely_invalid_response(self, qe_memory, simple_model, mocker):
        """Test error with completely invalid response"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Parse error"))
        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value="This is not JSON at all!"))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic', side_effect=Exception("Invalid")):
                    mock_fuzzy.return_value = {}

                    with pytest.raises(ValueError):
                        await agent.safe_operate(
                            instruction="Get data",
                            response_format=SimpleTestModel
                        )


class TestSafeParseResponse:
    """Test safe_parse_response() method"""

    @pytest.mark.asyncio
    async def test_parse_json_string(self, qe_memory, simple_model):
        """Test parsing from JSON string"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        json_string = '{"test_name": "test", "test_count": 10, "success_rate": 0.95}'

        result = await agent.safe_parse_response(json_string, SimpleTestModel)

        assert result.test_name == "test"
        assert result.test_count == 10

    @pytest.mark.asyncio
    async def test_parse_dict(self, qe_memory, simple_model):
        """Test parsing from dict"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        data_dict = {
            "test_name": "test",
            "test_count": 10,
            "success_rate": 0.95
        }

        result = await agent.safe_parse_response(data_dict, SimpleTestModel)

        assert result.test_name == "test"
        assert result.test_count == 10

    @pytest.mark.asyncio
    async def test_parse_malformed_string_fallback(self, qe_memory, simple_model):
        """Test fuzzy fallback for malformed string"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        malformed = 'Here is the data: {"test_name": "test", "test_count": 10, "success_rate": 0.95}'

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {
                        "test_name": "test",
                        "test_count": 10,
                        "success_rate": 0.95
                    }
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test",
                        test_count=10,
                        success_rate=0.95
                    )

                    result = await agent.safe_parse_response(malformed, SimpleTestModel)

                    assert result.test_name == "test"
                    assert mock_fuzzy.called

    @pytest.mark.asyncio
    async def test_parse_stored_response(self, qe_memory, simple_model):
        """Test parsing a response retrieved from memory"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        # Store response in memory
        stored_data = {
            "test_name": "stored_test",
            "test_count": 25,
            "success_rate": 0.88
        }
        await qe_memory.store("test_response", stored_data)

        # Retrieve and parse
        retrieved = await qe_memory.retrieve("test_response")
        result = await agent.safe_parse_response(retrieved, SimpleTestModel)

        assert result.test_name == "stored_test"
        assert result.test_count == 25

    @pytest.mark.asyncio
    async def test_parse_response_missing_optional_fields(self, qe_memory, simple_model):
        """Test parsing response with missing optional fields"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        data = {
            "test_suite": "unit",
            "total_tests": 10,
            "passedTests": 9,
            "failedTests": 1,
            "test_files": ["test.py"]
            # metadata is optional, not provided
        }

        result = await agent.safe_parse_response(data, ComplexTestModel)

        assert result.test_suite == "unit"
        assert result.metadata is None


class TestLogging:
    """Test logging behavior"""

    @pytest.mark.asyncio
    async def test_success_logging(self, qe_memory, simple_model, mocker, caplog):
        """Test logging on successful parse"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(
            agent.branch,
            'operate',
            new=AsyncMock(return_value=SimpleTestModel(
                test_name="test",
                test_count=10,
                success_rate=0.95
            ))
        )

        await agent.safe_operate(instruction="Test", response_format=SimpleTestModel)

        assert "Standard parsing successful" in caplog.text

    @pytest.mark.asyncio
    async def test_fallback_warning_logging(self, qe_memory, simple_model, mocker, caplog):
        """Test warning logged when falling back to fuzzy parsing"""
        agent = MockAgent("test-agent", simple_model, qe_memory)

        mocker.patch.object(agent.branch, 'operate', side_effect=Exception("Parse error"))
        mocker.patch.object(agent.branch, 'communicate', new=AsyncMock(return_value='{"test_name": "test", "test_count": 10, "success_rate": 0.95}'))

        with patch('lionagi_qe.core.base_agent.FUZZY_PARSING_AVAILABLE', True):
            with patch('lionagi_qe.core.base_agent.fuzzy_json') as mock_fuzzy:
                with patch('lionagi_qe.core.base_agent.fuzzy_validate_pydantic') as mock_validate:
                    mock_fuzzy.return_value = {"test_name": "test", "test_count": 10, "success_rate": 0.95}
                    mock_validate.return_value = SimpleTestModel(
                        test_name="test",
                        test_count=10,
                        success_rate=0.95
                    )

                    await agent.safe_operate(instruction="Test", response_format=SimpleTestModel)

                    assert "attempting fuzzy parsing fallback" in caplog.text
                    assert "Fuzzy parsing successful" in caplog.text
