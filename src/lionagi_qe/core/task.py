"""QE Task definitions"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
from datetime import datetime


class QETask(BaseModel):
    """Task definition for QE agents"""

    task_id: str = Field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    task_type: str = Field(..., description="Type of QE task to execute")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Task context and parameters"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Task priority level"
    )
    agent_id: Optional[str] = Field(
        default=None, description="Assigned agent ID"
    )
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending"
    )
    result: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)

    def mark_in_progress(self, agent_id: str):
        """Mark task as in progress"""
        self.status = "in_progress"
        self.agent_id = agent_id

    def mark_completed(self, result: Dict[str, Any]):
        """Mark task as completed"""
        self.status = "completed"
        self.result = result
        self.completed_at = datetime.now()

    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now()
