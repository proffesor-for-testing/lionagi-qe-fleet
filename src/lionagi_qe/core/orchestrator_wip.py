"""WIP-Limited QE Orchestrator with Coordination Primitives

This module implements Small Teams pattern and Swarming (One-Piece Continuous Flow)
from Scrum patterns to prevent thrashing and reduce repetitive output.

Key Features:
- Work-In-Progress (WIP) limits via asyncio.Semaphore
- Agent lane segregation (test/security/performance/quality)
- Context budget tracking (token limits)
- Metrics for coordination effectiveness

References:
- Small Teams: https://sites.google.com/a/scrumplop.org/published-patterns/product-organization-pattern-language/development-team/small-teams
- Swarming: https://sites.google.com/a/scrumplop.org/published-patterns/product-organization-pattern-language/development-team/swarming--one-piece-continuous-flow
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum

# Import from existing orchestrator
from .orchestrator import QEOrchestrator as BaseOrchestrator
from .task import QETask


class LaneType(Enum):
    """Agent lane types for segregation"""
    TEST = "test"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SHARED = "shared"


@dataclass
class AgentLane:
    """Agent lane with WIP limits and isolated memory namespace
    
    Implements Small Teams pattern: 3-5 agents per lane to prevent thrashing.
    Each lane has its own semaphore enforcing WIP limits.
    
    Attributes:
        name: Lane identifier
        lane_type: Type of lane (test, security, etc.)
        wip_limit: Maximum concurrent agents in this lane
        memory_namespace: Isolated memory namespace (e.g., "aqe/test/*")
        active_count: Current number of active agents
        total_executed: Total agents executed (lifetime)
        wait_time_ms: Cumulative wait time due to WIP limit
    """
    name: str
    lane_type: LaneType
    wip_limit: int = 3
    memory_namespace: str = field(init=False)
    semaphore: asyncio.Semaphore = field(init=False)
    
    # Metrics
    active_count: int = 0
    total_executed: int = 0
    wait_time_ms: float = 0.0
    limit_hits: int = 0  # Times lane WIP limit was hit
    
    def __post_init__(self):
        self.memory_namespace = f"aqe/{self.lane_type.value}/*"
        self.semaphore = asyncio.Semaphore(self.wip_limit)
    
    async def acquire(self) -> float:
        """Acquire semaphore, return wait time in ms"""
        start = asyncio.get_event_loop().time()
        await self.semaphore.acquire()
        wait_ms = (asyncio.get_event_loop().time() - start) * 1000
        self.active_count += 1
        self.wait_time_ms += wait_ms
        if wait_ms > 1:  # Waited > 1ms = hit the limit
            self.limit_hits += 1
        return wait_ms
    
    def release(self):
        """Release semaphore"""
        self.semaphore.release()
        self.active_count -= 1
        self.total_executed += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get lane metrics"""
        return {
            "name": self.name,
            "type": self.lane_type.value,
            "wip_limit": self.wip_limit,
            "active_count": self.active_count,
            "total_executed": self.total_executed,
            "wait_time_ms": self.wait_time_ms,
            "avg_wait_ms": self.wait_time_ms / max(1, self.total_executed),
            "utilization": self.active_count / self.wip_limit if self.wip_limit > 0 else 0,
            "limit_hits": self.limit_hits
        }


@dataclass
class ContextBudget:
    """Context budget tracking to prevent redundant LLM calls
    
    Tracks cumulative token usage across agents to enforce budget limits.
    Helps identify when context is growing unbounded.
    
    Attributes:
        max_tokens: Maximum allowed tokens per workflow
        used_tokens: Current token usage
        calls_count: Number of LLM calls
        budget_exceeded_count: Times budget was exceeded
    """
    max_tokens: int = 100_000  # Default 100k tokens per workflow
    used_tokens: int = 0
    calls_count: int = 0
    budget_exceeded_count: int = 0
    
    async def reserve(self, tokens: int) -> bool:
        """Reserve tokens from budget
        
        Args:
            tokens: Number of tokens to reserve
            
        Returns:
            True if reservation successful
            
        Raises:
            ContextBudgetExceededError: If budget exceeded
        """
        if self.used_tokens + tokens > self.max_tokens:
            self.budget_exceeded_count += 1
            raise ContextBudgetExceededError(
                f"Context budget exceeded: {self.used_tokens + tokens} > {self.max_tokens}. "
                f"Consider: (1) reducing context size, (2) using delta updates, "
                f"(3) increasing budget limit."
            )
        self.used_tokens += tokens
        self.calls_count += 1
        return True
    
    def release(self, tokens: int):
        """Release tokens back to budget"""
        self.used_tokens = max(0, self.used_tokens - tokens)
    
    def reset(self):
        """Reset budget for new workflow"""
        self.used_tokens = 0
        self.calls_count = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get budget metrics"""
        return {
            "max_tokens": self.max_tokens,
            "used_tokens": self.used_tokens,
            "remaining_tokens": self.max_tokens - self.used_tokens,
            "utilization": (self.used_tokens / self.max_tokens) * 100,  # Return as percentage
            "calls_count": self.calls_count,
            "avg_tokens_per_call": self.used_tokens / max(1, self.calls_count),
            "budget_exceeded_count": self.budget_exceeded_count
        }


class ContextBudgetExceededError(Exception):
    """Raised when context budget is exceeded"""
    pass


class WIPLimitedOrchestrator(BaseOrchestrator):
    """QE Orchestrator with WIP limits and coordination primitives
    
    Extends base orchestrator with:
    - Global WIP limit (default: 5 concurrent agents)
    - Agent lane segregation (test/security/performance/quality lanes)
    - Context budget tracking (token limits)
    - Enhanced metrics for coordination effectiveness
    
    Usage:
        orchestrator = WIPLimitedOrchestrator(
            wip_limit=5,  # Global limit
            lane_wip_limits={
                LaneType.TEST: 3,
                LaneType.SECURITY: 2,
                LaneType.PERFORMANCE: 2,
                LaneType.QUALITY: 3
            },
            context_budget_tokens=100_000
        )
        
        # Register agents to lanes
        orchestrator.assign_agent_to_lane("test-generator", LaneType.TEST)
        orchestrator.assign_agent_to_lane("security-scanner", LaneType.SECURITY)
        
        # Execute with WIP limits enforced
        results = await orchestrator.execute_parallel(
            agent_ids=["test-generator", "security-scanner"],
            tasks=[task1, task2]
        )
    """
    
    def __init__(
        self,
        wip_limit: int = 5,
        lane_wip_limits: Optional[Dict[LaneType, int]] = None,
        context_budget_tokens: int = 100_000,
        **base_kwargs
    ):
        """Initialize WIP-limited orchestrator
        
        Args:
            wip_limit: Global WIP limit (max concurrent agents across all lanes)
            lane_wip_limits: Per-lane WIP limits (defaults to Small Teams pattern: 3-5 per lane)
            context_budget_tokens: Maximum tokens per workflow
            **base_kwargs: Arguments passed to BaseOrchestrator
        """
        super().__init__(**base_kwargs)
        
        # Global WIP limit
        self.wip_limit = wip_limit
        self.global_semaphore = asyncio.Semaphore(wip_limit)
        
        # Initialize lanes with Small Teams pattern (3-5 agents per lane)
        default_lane_limits = {
            LaneType.TEST: 3,
            LaneType.SECURITY: 2,
            LaneType.PERFORMANCE: 2,
            LaneType.QUALITY: 3,
            LaneType.SHARED: 2
        }
        lane_limits = lane_wip_limits or default_lane_limits
        
        self.lanes: Dict[LaneType, AgentLane] = {
            lane_type: AgentLane(
                name=lane_type.value,
                lane_type=lane_type,
                wip_limit=lane_limits.get(lane_type, 3)
            )
            for lane_type in LaneType
        }
        
        # Agent -> Lane mapping
        self.agent_lanes: Dict[str, LaneType] = {}
        
        # Context budget
        self.context_budget = ContextBudget(max_tokens=context_budget_tokens)
        
        # Coordination metrics
        self.coordination_metrics = {
            "total_wait_time_ms": 0.0,
            "wip_limit_hits": 0,
            "lane_limit_hits": 0,
            "budget_exceeded": 0,
            "parallel_executions": 0,
            "max_concurrent_observed": 0
        }
        
        self.logger.info(
            f"WIPLimitedOrchestrator initialized with global WIP limit: {wip_limit}, "
            f"lanes: {[f'{lt.value}({l.wip_limit})' for lt, l in self.lanes.items()]}, "
            f"context budget: {context_budget_tokens} tokens"
        )
    
    def assign_agent_to_lane(self, agent_id: str, lane_type: LaneType):
        """Assign agent to a specific lane
        
        Args:
            agent_id: Agent identifier
            lane_type: Lane to assign agent to
        """
        self.agent_lanes[agent_id] = lane_type
        self.logger.info(f"Assigned agent '{agent_id}' to lane '{lane_type.value}'")
    
    def get_agent_lane(self, agent_id: str) -> LaneType:
        """Get agent's lane (defaults to SHARED if not assigned)"""
        return self.agent_lanes.get(agent_id, LaneType.SHARED)
    
    async def execute_agent(self, agent_id: str, task: QETask) -> Dict[str, Any]:
        """Execute single agent with WIP limits enforced
        
        Overrides base method to add WIP limit enforcement for direct calls.
        When called directly (not via execute_parallel), still enforces limits.
        
        Args:
            agent_id: Agent identifier
            task: Task to execute
            
        Returns:
            Execution result dict
        """
        lane_type = self.get_agent_lane(agent_id)
        lane = self.lanes[lane_type]
        
        # Acquire both global and lane semaphores
        start_time = asyncio.get_event_loop().time()
        
        # Global WIP limit
        await self.global_semaphore.acquire()
        global_wait = (asyncio.get_event_loop().time() - start_time) * 1000
        
        try:
            # Lane WIP limit
            lane_wait = await lane.acquire()
            
            total_wait = global_wait + lane_wait
            
            self.logger.debug(
                f"Agent '{agent_id}' acquired WIP slots (lane: {lane_type.value}, "
                f"wait: {total_wait:.1f}ms)"
            )
            
            # Call base implementation
            return await super().execute_agent(agent_id, task)
            
        finally:
            # Release semaphores
            lane.release()
            self.global_semaphore.release()
    
    async def execute_parallel(
        self,
        agent_ids: List[str],
        tasks: List[Any]  # Can be QETask objects or dicts
    ) -> List[Dict[str, Any]]:
        """Execute multiple agents in parallel with WIP limits
        
        Overrides base method to add:
        - Global WIP limit enforcement via semaphore
        - Per-lane WIP limit enforcement
        - Wait time tracking
        - Context budget validation
        
        Args:
            agent_ids: List of agent IDs to execute
            tasks: List of QETask objects or task context dicts (one per agent)
        
        Returns:
            List of execution results
        """
        self.logger.info(
            f"Executing {len(agent_ids)} agents in parallel with WIP limit: {self.wip_limit}"
        )
        self.coordination_metrics["parallel_executions"] += 1
        
        async def run_agent_with_limits(agent_id: str, task_context: Any):
            """Run agent with both global and lane WIP limits (task_context can be QETask or dict)"""
            lane_type = self.get_agent_lane(agent_id)
            lane = self.lanes[lane_type]
            
            # Acquire both global and lane semaphores
            start_time = asyncio.get_event_loop().time()
            
            # Global WIP limit
            await self.global_semaphore.acquire()
            global_wait = (asyncio.get_event_loop().time() - start_time) * 1000
            if global_wait > 10:  # Waited > 10ms
                self.coordination_metrics["wip_limit_hits"] += 1
            
            try:
                # Lane WIP limit
                lane_wait = await lane.acquire()
                if lane_wait > 10:  # Waited > 10ms
                    self.coordination_metrics["lane_limit_hits"] += 1
                
                total_wait = global_wait + lane_wait
                self.coordination_metrics["total_wait_time_ms"] += total_wait
                
                # Track max concurrency
                current_active = sum(l.active_count for l in self.lanes.values())
                self.coordination_metrics["max_concurrent_observed"] = max(
                    self.coordination_metrics["max_concurrent_observed"],
                    current_active
                )
                
                self.logger.debug(
                    f"Agent '{agent_id}' acquired WIP slots (lane: {lane_type.value}, "
                    f"wait: {total_wait:.1f}ms, active: {current_active}/{self.wip_limit})"
                )
                
                # Execute task (delegate to base orchestrator, NOT our override)
                # We already acquired semaphores above, so call base directly
                agent = self.get_agent(agent_id)
                if not agent:
                    raise ValueError(f"Agent not found: {agent_id}")
                
                # Handle both QETask objects and dicts
                if isinstance(task_context, QETask):
                    task = task_context
                else:
                    task = QETask(
                        task_type=task_context.get("task_type", "execute"),
                        context=task_context
                    )
                
                return await super(WIPLimitedOrchestrator, self).execute_agent(agent_id, task)
                
            finally:
                # Release semaphores
                lane.release()
                self.global_semaphore.release()
        
        # Execute all agents with limits
        tasks_with_agents = list(zip(agent_ids, tasks))
        coroutines = [
            run_agent_with_limits(agent_id, task_ctx)
            for agent_id, task_ctx in tasks_with_agents
        ]
        # Use return_exceptions=True to ensure all coroutines complete and release semaphores
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Check for exceptions and re-raise first one found
        for result in results:
            if isinstance(result, Exception):
                raise result
        
        self.metrics["total_agents_used"] += len(agent_ids)
        
        return results
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """Get coordination and WIP limit status
        
        Returns:
            Dict with coordination metrics, lane status, and context budget
        """
        lane_metrics = {
            lane_type.value: lane.get_metrics()
            for lane_type, lane in self.lanes.items()
        }
        
        # Flatten for backward compatibility with tests
        result = {
            "wip_config": {
                "global_limit": self.wip_limit,
                "lane_limits": {lt.value: l.wip_limit for lt, l in self.lanes.items()}
            },
            "coordination_metrics": self.coordination_metrics,
            "lane_metrics": lane_metrics,
            "context_budget": self.context_budget.get_metrics(),
            "recommendations": self._generate_recommendations()
        }
        
        # Add flattened metrics for backward compatibility
        result.update(self.coordination_metrics)  # wip_limit_hits, etc. at top level
        result["lanes"] = lane_metrics  # Alias for lane_metrics
        
        return result
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on coordination metrics"""
        recommendations = []
        
        # Calculate global average wait time first (needed for lane recommendations)
        avg_wait = self.coordination_metrics["total_wait_time_ms"] / max(
            1, self.coordination_metrics["parallel_executions"]
        )
        high_contention = avg_wait > 100  # >100ms average wait indicates contention
        
        # Check WIP limit effectiveness
        if self.coordination_metrics["wip_limit_hits"] > 10:
            recommendations.append(
                f"⚠️ Global WIP limit hit {self.coordination_metrics['wip_limit_hits']} times. "
                "consider increasing global limit or reviewing workflow parallelism."
            )
        
        # Check lane utilization
        for lane_type, lane in self.lanes.items():
            metrics = lane.get_metrics()
            if metrics["utilization"] > 0.8:
                recommendations.append(
                    f"⚠️ Lane '{lane_type.value}' at {metrics['utilization']:.0%} utilization. "
                    f"consider increasing WIP limit from {lane.wip_limit} to {lane.wip_limit + 2}."
                )
            elif (metrics["total_executed"] > 0 and metrics["utilization"] < 0.2 and 
                  metrics["limit_hits"] == 0 and metrics["avg_wait_ms"] < 10 and not high_contention):
                # Only recommend reducing if there's no contention (no limit hits, low wait time, no global contention)
                recommendations.append(
                    f"💡 Lane '{lane_type.value}' underutilized ({metrics['utilization']:.0%}). "
                    f"consider reducing WIP limit from {lane.wip_limit} to {max(1, lane.wip_limit - 1)}."
                )
        
        # Check context budget
        budget_metrics = self.context_budget.get_metrics()
        if budget_metrics["utilization"] > 90:  # utilization is now percentage (0-100+)
            recommendations.append(
                "⚠️ Context budget near limit (>90%). "
                "Implement delta updates or increase budget."
            )
        
        # Check average wait time (already calculated above)
        if high_contention:
            recommendations.append(
                f"⚠️ High average wait time ({avg_wait:.0f}ms). "
                "increase WIP limits to reduce contention."
            )
        
        if not recommendations:
            recommendations.append("✅ Coordination parameters are well-tuned.")
        
        return recommendations


# Utility function for easy migration
def create_wip_limited_orchestrator(
    wip_limit: int = 5,
    test_lane_limit: int = 3,
    security_lane_limit: int = 2,
    performance_lane_limit: int = 2,
    quality_lane_limit: int = 3,
    shared_lane_limit: int = 2,
    context_budget: int = 100_000,
    **orchestrator_kwargs
) -> WIPLimitedOrchestrator:
    """Create WIP-limited orchestrator with sensible defaults
    
    Quick factory function following Small Teams pattern recommendations.
    
    Args:
        wip_limit: Global max concurrent agents (recommended: 5-10)
        test_lane_limit: Test lane WIP limit (recommended: 3)
        security_lane_limit: Security lane WIP limit (recommended: 2)
        performance_lane_limit: Performance lane WIP limit (recommended: 2)
        quality_lane_limit: Quality lane WIP limit (recommended: 3)
        shared_lane_limit: Shared lane WIP limit (recommended: 2)
        context_budget: Max tokens per workflow (recommended: 100k)
        **orchestrator_kwargs: Additional args for BaseOrchestrator
    
    Returns:
        WIPLimitedOrchestrator instance
    
    Example:
        >>> orchestrator = create_wip_limited_orchestrator(wip_limit=5)
        >>> await orchestrator.initialize()
        >>> orchestrator.assign_agent_to_lane("test-generator", LaneType.TEST)
    """
    return WIPLimitedOrchestrator(
        wip_limit=wip_limit,
        lane_wip_limits={
            LaneType.TEST: test_lane_limit,
            LaneType.SECURITY: security_lane_limit,
            LaneType.PERFORMANCE: performance_lane_limit,
            LaneType.QUALITY: quality_lane_limit,
            LaneType.SHARED: shared_lane_limit
        },
        context_budget_tokens=context_budget,
        **orchestrator_kwargs
    )
