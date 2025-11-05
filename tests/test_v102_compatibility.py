"""
Regression tests to verify v1.0.2 backward compatibility.

These tests ensure that code written for v1.0.2 continues to work
in newer versions with appropriate deprecation warnings.
"""

import pytest
import warnings


class TestV102BackwardCompatibility:
    """Test backward compatibility with v1.0.2 API."""

    def test_qefleet_still_exists(self):
        """QEFleet should still be importable."""
        from lionagi_qe import QEFleet
        assert QEFleet is not None

    def test_qefleet_shows_deprecation_warning(self):
        """QEFleet should emit deprecation warning when used."""
        from lionagi_qe import QEFleet

        with pytest.warns(DeprecationWarning, match="QEFleet is deprecated"):
            fleet = QEFleet()

        assert fleet is not None

    def test_qememory_still_exists(self):
        """QEMemory should still be importable."""
        from lionagi_qe import QEMemory
        assert QEMemory is not None

    def test_qememory_shows_deprecation_warning(self):
        """QEMemory should emit deprecation warning when used."""
        from lionagi_qe import QEMemory

        with pytest.warns(DeprecationWarning, match="QEMemory is deprecated"):
            memory = QEMemory()

        assert memory is not None

    def test_qetask_still_works(self):
        """QETask should work without changes."""
        from lionagi_qe import QETask

        task = QETask(
            name="test",
            description="test task",
            agent_type="test-agent"
        )

        assert task.name == "test"
        assert task.description == "test task"
        assert task.agent_type == "test-agent"

    def test_model_router_still_works(self):
        """ModelRouter should work without changes."""
        from lionagi_qe import ModelRouter

        router = ModelRouter(enable_routing=False)
        assert router is not None

    def test_base_agent_still_works(self):
        """BaseQEAgent should work without changes."""
        from lionagi_qe import BaseQEAgent

        class TestAgent(BaseQEAgent):
            async def execute_task(self, task):
                return {"status": "completed"}

        agent = TestAgent(agent_id="test")
        assert agent is not None

    def test_orchestrator_available(self):
        """QEOrchestrator should be available as migration path."""
        from lionagi_qe import QEOrchestrator
        assert QEOrchestrator is not None


class TestNewFeaturesOptional:
    """Test that new features are optional and don't break existing code."""

    def test_base_agent_without_learning(self):
        """BaseQEAgent should work without Q-learning enabled."""
        from lionagi_qe.core.base_agent import BaseQEAgent

        class SimpleAgent(BaseQEAgent):
            async def execute_task(self, task):
                return {"status": "ok"}

        # Should work without Q-learning
        agent = SimpleAgent(agent_id="simple", enable_learning=False)
        assert agent is not None
        assert agent.enable_learning is False

    def test_base_agent_without_db_manager(self):
        """BaseQEAgent should work without DatabaseManager."""
        from lionagi_qe.core.base_agent import BaseQEAgent

        class SimpleAgent(BaseQEAgent):
            async def execute_task(self, task):
                return {"status": "ok"}

        # Should work with db_manager=None
        agent = SimpleAgent(agent_id="simple", db_manager=None)
        assert agent is not None
        assert agent.db_manager is None


class TestAPIStability:
    """Test that public API remains stable."""

    def test_all_exports_present(self):
        """All expected exports should be present."""
        import lionagi_qe

        expected_exports = [
            "QEFleet",
            "QEMemory",
            "QETask",
            "ModelRouter",
            "QEOrchestrator",
            "BaseQEAgent"
        ]

        for export in expected_exports:
            assert hasattr(lionagi_qe, export), f"Missing export: {export}"

    def test_version_attribute_exists(self):
        """Version attribute should exist."""
        import lionagi_qe
        assert hasattr(lionagi_qe, "__version__")
        assert isinstance(lionagi_qe.__version__, str)
