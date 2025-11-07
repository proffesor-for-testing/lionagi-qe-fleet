"""Integration tests for AgentDB integration module."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from lionagi_qe.integrations.agentdb import AgentDBIntegration, store_qe_episode


class TestAgentDBIntegration:
    """Test suite for AgentDBIntegration class."""

    @pytest.fixture
    def integration(self):
        """Create AgentDBIntegration instance for testing."""
        return AgentDBIntegration()

    @pytest.fixture
    def sample_test_result(self):
        """Sample test result data."""
        return {
            "test_name": "test_login_flow",
            "status": "passed",
            "duration": 1.23,
            "assertions": 5,
            "steps": [
                {"action": "navigate", "target": "/login"},
                {"action": "input", "target": "username", "value": "testuser"},
                {"action": "click", "target": "submit"}
            ]
        }

    @pytest.mark.asyncio
    async def test_store_test_run_success(self, integration, sample_test_result):
        """Test storing a test run episode."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            # Mock process with successful return
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"episode_id": "ep_123", "status": "success"}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await integration.store_test_run(
                test_name=sample_test_result["test_name"],
                steps=sample_test_result["steps"],
                outcome=sample_test_result["status"],
                metadata={"duration": sample_test_result["duration"]}
            )

            assert result["status"] == "success"
            assert "episode_id" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_test_run_with_reward(self, integration, sample_test_result):
        """Test storing test run with explicit reward value."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"episode_id": "ep_124", "reward": 0.95}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await integration.store_test_run(
                test_name="test_high_reward",
                steps=sample_test_result["steps"],
                outcome="passed",
                reward=0.95
            )

            assert result["reward"] == 0.95

    @pytest.mark.asyncio
    async def test_retrieve_similar_tests(self, integration):
        """Test retrieving similar tests from history."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"results": [{"episode_id": "ep_100", "similarity": 0.92}]}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            results = await integration.retrieve_similar_tests(
                query="login flow",
                k=5,
                min_reward=0.8
            )

            assert "results" in results
            assert len(results["results"]) > 0
            assert results["results"][0]["similarity"] == 0.92

    @pytest.mark.asyncio
    async def test_consolidate_skills(self, integration):
        """Test skill consolidation from test patterns."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"skills_consolidated": 3, "patterns_found": 7}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await integration.consolidate_skills(
                min_examples=3,
                min_reward=0.7,
                lookback_days=7
            )

            assert result["skills_consolidated"] == 3
            assert result["patterns_found"] == 7

    @pytest.mark.asyncio
    async def test_search_skills(self, integration):
        """Test searching for learned skills."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"skills": [{"name": "login_validation", "frequency": 15}]}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            skills = await integration.search_skills(
                query="login validation",
                k=5
            )

            assert "skills" in skills
            assert skills["skills"][0]["name"] == "login_validation"

    @pytest.mark.asyncio
    async def test_get_critique_summary(self, integration):
        """Test retrieving critique summary."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"summary": "Most failures in auth module", "count": 12}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            summary = await integration.get_critique_summary(
                query="authentication failures"
            )

            assert "summary" in summary
            assert summary["count"] == 12

    @pytest.mark.asyncio
    async def test_command_failure_handling(self, integration):
        """Test handling of AgentDB command failures."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            # Mock process with error return
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'',
                b'Error: Database not found'
            ))
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            result = await integration.store_test_run(
                test_name="test_failure",
                steps=[],
                outcome="failed"
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_store_qe_episode_convenience_function(self, sample_test_result):
        """Test convenience function for storing QE episodes."""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(
                b'{"episode_id": "ep_125"}',
                b''
            ))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await store_qe_episode(
                test_name=sample_test_result["test_name"],
                steps=sample_test_result["steps"],
                outcome=sample_test_result["status"]
            )

            assert "episode_id" in result


class TestAgentDBCLIIntegration:
    """Test CLI command construction and execution."""

    @pytest.mark.asyncio
    async def test_episode_store_command_format(self):
        """Test that episode store commands are formatted correctly."""
        integration = AgentDBIntegration()
        
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b'{}', b''))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            await integration.store_test_run(
                test_name="test_sample",
                steps=[{"action": "test"}],
                outcome="passed"
            )

            # Verify command structure
            call_args = mock_exec.call_args
            assert call_args[0][0] == "npx"
            assert call_args[0][1] == "agentdb"
            assert "episode" in call_args[0]
            assert "store" in call_args[0]

    @pytest.mark.asyncio
    async def test_reflexion_retrieve_command_format(self):
        """Test reflexion retrieve command format."""
        integration = AgentDBIntegration()
        
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b'{}', b''))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            await integration.retrieve_similar_tests(
                query="sample query",
                k=5
            )

            call_args = mock_exec.call_args
            assert "reflexion" in call_args[0]
            assert "retrieve" in call_args[0]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
