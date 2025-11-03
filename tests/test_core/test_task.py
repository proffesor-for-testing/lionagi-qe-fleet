"""Unit tests for QETask - Task state management"""

import pytest
from datetime import datetime
from lionagi_qe.core.task import QETask


class TestQETask:
    """Test QETask model and state management"""

    def test_task_creation(self):
        """Test creating a QETask"""
        task = QETask(
            task_type="test_generation",
            context={"code": "def add(a, b): return a + b"},
            priority="high"
        )

        assert task.task_type == "test_generation"
        assert task.context == {"code": "def add(a, b): return a + b"}
        assert task.priority == "high"
        assert task.status == "pending"
        assert task.agent_id is None
        assert task.result is None
        assert task.error is None

    def test_task_defaults(self):
        """Test QETask default values"""
        task = QETask(task_type="test_execution")

        assert task.context == {}
        assert task.priority == "medium"
        assert task.status == "pending"
        assert task.created_at is not None
        assert task.completed_at is None

    def test_task_id_generation(self):
        """Test task_id is auto-generated"""
        task1 = QETask(task_type="test1")
        task2 = QETask(task_type="test2")

        assert task1.task_id is not None
        assert task2.task_id is not None
        assert task1.task_id != task2.task_id

    def test_mark_in_progress(self):
        """Test marking task as in progress"""
        task = QETask(task_type="test")

        task.mark_in_progress("agent-123")

        assert task.status == "in_progress"
        assert task.agent_id == "agent-123"

    def test_mark_completed(self):
        """Test marking task as completed"""
        task = QETask(task_type="test")
        result = {"tests_generated": 10, "coverage": 85.0}

        task.mark_completed(result)

        assert task.status == "completed"
        assert task.result == result
        assert task.completed_at is not None
        assert isinstance(task.completed_at, datetime)

    def test_mark_failed(self):
        """Test marking task as failed"""
        task = QETask(task_type="test")
        error_message = "Test generation failed: invalid syntax"

        task.mark_failed(error_message)

        assert task.status == "failed"
        assert task.error == error_message
        assert task.completed_at is not None

    def test_task_lifecycle(self):
        """Test complete task lifecycle"""
        task = QETask(
            task_type="test_generation",
            context={"code": "sample"},
            priority="high"
        )

        # Initial state
        assert task.status == "pending"

        # Start execution
        task.mark_in_progress("test-generator")
        assert task.status == "in_progress"
        assert task.agent_id == "test-generator"

        # Complete successfully
        task.mark_completed({"result": "success"})
        assert task.status == "completed"
        assert task.result == {"result": "success"}

    def test_task_priority_levels(self):
        """Test all priority levels"""
        for priority in ["low", "medium", "high", "critical"]:
            task = QETask(task_type="test", priority=priority)
            assert task.priority == priority

    def test_task_status_levels(self):
        """Test all status transitions"""
        task = QETask(task_type="test")

        # Pending -> In Progress
        task.status = "in_progress"
        assert task.status == "in_progress"

        # In Progress -> Completed
        task.status = "completed"
        assert task.status == "completed"

        # Test failed path
        task2 = QETask(task_type="test")
        task2.status = "failed"
        assert task2.status == "failed"

    def test_task_context_types(self):
        """Test various context data types"""
        contexts = [
            {"string": "value"},
            {"number": 42},
            {"list": [1, 2, 3]},
            {"nested": {"data": {"deep": "value"}}},
            {"mixed": ["string", 42, {"key": "value"}]}
        ]

        for context in contexts:
            task = QETask(task_type="test", context=context)
            assert task.context == context

    def test_task_result_structure(self):
        """Test task result can store complex data"""
        task = QETask(task_type="test")

        complex_result = {
            "tests_generated": 15,
            "coverage": 92.5,
            "frameworks": ["pytest", "jest"],
            "failures": [],
            "metrics": {
                "duration": 1.5,
                "complexity": "medium"
            }
        }

        task.mark_completed(complex_result)
        assert task.result == complex_result

    def test_task_error_message(self):
        """Test error message storage"""
        task = QETask(task_type="test")

        long_error = "ValueError: Invalid input\n" + "Stack trace: " * 100

        task.mark_failed(long_error)
        assert task.error == long_error

    def test_task_created_at_timestamp(self):
        """Test created_at is properly set"""
        before = datetime.now()
        task = QETask(task_type="test")
        after = datetime.now()

        assert before <= task.created_at <= after

    def test_task_completion_timestamp(self):
        """Test completed_at is set on completion"""
        task = QETask(task_type="test")

        assert task.completed_at is None

        before = datetime.now()
        task.mark_completed({"result": "done"})
        after = datetime.now()

        assert task.completed_at is not None
        assert before <= task.completed_at <= after

    def test_task_serialization(self):
        """Test task can be serialized to dict"""
        task = QETask(
            task_type="test_generation",
            context={"code": "test"},
            priority="high"
        )

        task_dict = task.model_dump()

        assert task_dict["task_type"] == "test_generation"
        assert task_dict["context"] == {"code": "test"}
        assert task_dict["priority"] == "high"
        assert task_dict["status"] == "pending"

    def test_task_with_agent_assignment(self):
        """Test task with pre-assigned agent"""
        task = QETask(
            task_type="test",
            agent_id="pre-assigned-agent"
        )

        assert task.agent_id == "pre-assigned-agent"

    def test_multiple_state_transitions(self):
        """Test task can't be completed twice"""
        task = QETask(task_type="test")

        task.mark_completed({"result": "first"})
        first_completion = task.completed_at

        # Try to complete again
        task.mark_completed({"result": "second"})

        # Should update result but completion time changes
        assert task.result == {"result": "second"}
        assert task.completed_at > first_completion

    def test_task_failure_after_in_progress(self):
        """Test task can fail after being in progress"""
        task = QETask(task_type="test")

        task.mark_in_progress("agent-1")
        assert task.status == "in_progress"

        task.mark_failed("Something went wrong")
        assert task.status == "failed"
        assert task.agent_id == "agent-1"  # Agent ID preserved

    def test_task_context_empty_dict(self):
        """Test task with empty context"""
        task = QETask(task_type="test", context={})

        assert task.context == {}
        assert isinstance(task.context, dict)

    def test_task_context_modification(self):
        """Test modifying task context"""
        task = QETask(
            task_type="test",
            context={"initial": "value"}
        )

        task.context["added"] = "new_value"

        assert task.context == {
            "initial": "value",
            "added": "new_value"
        }

    def test_task_repr_contains_key_info(self):
        """Test task string representation"""
        task = QETask(
            task_type="test_generation",
            priority="high"
        )

        task_str = str(task)
        assert "test_generation" in task_str or "QETask" in task_str
