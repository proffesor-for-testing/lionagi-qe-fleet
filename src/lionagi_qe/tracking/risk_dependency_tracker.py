"""
Risk and Dependency Tracker with Swarm Coordination

Implements continuous risk/dependency tracking using:
- ROAM (Resolved, Owned, Accepted, Mitigated) risk management
- Dependency graph with blocking relationships
- Research-swarm integration for distributed monitoring
- Async background workers with sync gates
- Traffic light status (🟢🟡🔴) for visual prioritization

Based on Scrum patterns:
- Swarming: One-Piece Continuous Flow (focus on unblocking)
- Small Teams (agent lane segregation for risk domains)
- Interrupts Unjam Blocking (explicit dependency resolution)
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta


class RiskStatus(Enum):
    """ROAM risk status"""
    RESOLVED = "resolved"  # Risk eliminated
    OWNED = "owned"  # Owner assigned, mitigation in progress
    ACCEPTED = "accepted"  # Risk accepted, no action
    MITIGATED = "mitigated"  # Controls in place


class DependencyStatus(Enum):
    """Dependency blocking status"""
    BLOCKED = "blocked"  # Cannot proceed
    WAITING = "waiting"  # Waiting on external event
    READY = "ready"  # All dependencies satisfied
    IN_PROGRESS = "in_progress"  # Work started
    COMPLETE = "complete"  # Finished


class TrafficLight(Enum):
    """Priority level using traffic light metaphor"""
    GREEN = "🟢"  # Active, proceed
    YELLOW = "🟡"  # Caution, monitor
    RED = "🔴"  # Blocked, critical


@dataclass
class Risk:
    """ROAM risk with tracking metadata"""
    risk_id: str
    description: str
    status: RiskStatus
    owner: Optional[str] = None
    probability: float = 0.5  # 0.0-1.0
    impact: float = 0.5  # 0.0-1.0
    mitigation_plan: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)
    
    @property
    def risk_score(self) -> float:
        """Risk score = probability * impact"""
        return self.probability * self.impact
    
    @property
    def traffic_light(self) -> TrafficLight:
        """Traffic light based on risk score"""
        if self.status == RiskStatus.RESOLVED:
            return TrafficLight.GREEN
        score = self.risk_score
        if score > 0.7:
            return TrafficLight.RED
        elif score > 0.4:
            return TrafficLight.YELLOW
        return TrafficLight.GREEN


@dataclass
class Dependency:
    """Task dependency with blocking relationships"""
    task_id: str
    description: str
    status: DependencyStatus
    depends_on: Set[str] = field(default_factory=set)  # Task IDs
    blocked_by: Set[str] = field(default_factory=set)  # Risk IDs
    assignee: Optional[str] = None
    lane: Optional[str] = None  # Agent lane for swarming
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)
    
    @property
    def traffic_light(self) -> TrafficLight:
        """Traffic light based on dependency status"""
        if self.status == DependencyStatus.COMPLETE:
            return TrafficLight.GREEN
        elif self.status == DependencyStatus.BLOCKED:
            return TrafficLight.RED
        elif self.status == DependencyStatus.WAITING:
            return TrafficLight.YELLOW
        return TrafficLight.GREEN


@dataclass
class SwarmAlert:
    """Alert for swarm coordination"""
    alert_id: str
    alert_type: str  # "risk_elevated", "dependency_blocked", "bottleneck_detected"
    severity: TrafficLight
    message: str
    related_items: List[str]  # Risk/Dependency IDs
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


class RiskDependencyTracker:
    """
    Continuous risk and dependency tracker with swarm coordination
    
    Features:
    - ROAM risk tracking
    - Dependency graph management
    - Bottleneck detection
    - Swarm alerts for coordination
    - Async background monitoring
    - Traffic light visualization
    """
    
    def __init__(
        self,
        monitoring_interval: float = 60.0,  # Check every 60s
        risk_threshold: float = 0.7,  # Alert if risk score > 0.7
        enable_swarm_alerts: bool = True
    ):
        self.risks: Dict[str, Risk] = {}
        self.dependencies: Dict[str, Dependency] = {}
        self.alerts: List[SwarmAlert] = []
        
        self.monitoring_interval = monitoring_interval
        self.risk_threshold = risk_threshold
        self.enable_swarm_alerts = enable_swarm_alerts
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Metrics
        self.metrics = {
            "risks_created": 0,
            "risks_resolved": 0,
            "dependencies_completed": 0,
            "bottlenecks_detected": 0,
            "alerts_generated": 0,
            "monitoring_cycles": 0
        }
    
    # ============ Risk Management (ROAM) ============
    
    def add_risk(
        self,
        risk_id: str,
        description: str,
        probability: float,
        impact: float,
        owner: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ) -> Risk:
        """Add new risk to tracker"""
        risk = Risk(
            risk_id=risk_id,
            description=description,
            status=RiskStatus.OWNED if owner else RiskStatus.ACCEPTED,
            owner=owner,
            probability=probability,
            impact=impact,
            tags=tags or set()
        )
        self.risks[risk_id] = risk
        self.metrics["risks_created"] += 1
        
        # Generate alert if high risk
        if risk.risk_score > self.risk_threshold and self.enable_swarm_alerts:
            self._generate_alert(
                alert_type="risk_elevated",
                severity=TrafficLight.RED,
                message=f"High-priority risk detected: {description}",
                related_items=[risk_id]
            )
        
        return risk
    
    def update_risk_status(
        self,
        risk_id: str,
        status: RiskStatus,
        mitigation_plan: Optional[str] = None
    ) -> Risk:
        """Update risk status (ROAM transition)"""
        if risk_id not in self.risks:
            raise ValueError(f"Risk {risk_id} not found")
        
        risk = self.risks[risk_id]
        risk.status = status
        
        if mitigation_plan:
            risk.mitigation_plan = mitigation_plan
        
        if status == RiskStatus.RESOLVED:
            risk.resolved_at = datetime.now()
            self.metrics["risks_resolved"] += 1
            
            # Check if any dependencies can be unblocked
            self._check_unblock_dependencies(risk_id)
        
        return risk
    
    def get_high_priority_risks(self) -> List[Risk]:
        """Get risks with score > threshold, sorted by score"""
        high_risks = [
            r for r in self.risks.values()
            if r.risk_score > self.risk_threshold and r.status not in [RiskStatus.RESOLVED, RiskStatus.MITIGATED]
        ]
        return sorted(high_risks, key=lambda r: r.risk_score, reverse=True)
    
    # ============ Dependency Management ============
    
    def add_dependency(
        self,
        task_id: str,
        description: str,
        depends_on: Optional[Set[str]] = None,
        blocked_by: Optional[Set[str]] = None,
        lane: Optional[str] = None,
        assignee: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ) -> Dependency:
        """Add task dependency to tracker"""
        dep = Dependency(
            task_id=task_id,
            description=description,
            status=DependencyStatus.BLOCKED if (blocked_by or depends_on) else DependencyStatus.READY,
            depends_on=depends_on or set(),
            blocked_by=blocked_by or set(),
            lane=lane,
            assignee=assignee,
            tags=tags or set()
        )
        self.dependencies[task_id] = dep
        
        # Alert if blocked
        if dep.status == DependencyStatus.BLOCKED and self.enable_swarm_alerts:
            blockers = list(blocked_by or []) + list(depends_on or [])
            self._generate_alert(
                alert_type="dependency_blocked",
                severity=TrafficLight.RED,
                message=f"Task blocked: {description}",
                related_items=[task_id] + blockers
            )
        
        return dep
    
    def update_dependency_status(
        self,
        task_id: str,
        status: DependencyStatus
    ) -> Dependency:
        """Update dependency status"""
        if task_id not in self.dependencies:
            raise ValueError(f"Dependency {task_id} not found")
        
        dep = self.dependencies[task_id]
        old_status = dep.status
        dep.status = status
        
        if status == DependencyStatus.IN_PROGRESS and not dep.started_at:
            dep.started_at = datetime.now()
        
        if status == DependencyStatus.COMPLETE:
            dep.completed_at = datetime.now()
            self.metrics["dependencies_completed"] += 1
            
            # Check if downstream dependencies can proceed
            self._check_downstream_dependencies(task_id)
        
        return dep
    
    def get_blocked_tasks(self) -> List[Dependency]:
        """Get all blocked tasks"""
        return [
            d for d in self.dependencies.values()
            if d.status == DependencyStatus.BLOCKED
        ]
    
    def get_ready_tasks_by_lane(self, lane: str) -> List[Dependency]:
        """Get ready tasks for specific agent lane (for swarming)"""
        return [
            d for d in self.dependencies.values()
            if d.status == DependencyStatus.READY and d.lane == lane
        ]
    
    # ============ Dependency Graph Analysis ============
    
    def get_dependency_chain(self, task_id: str) -> List[str]:
        """Get full dependency chain for task"""
        if task_id not in self.dependencies:
            return []
        
        chain = []
        visited = set()
        
        def dfs(tid: str):
            if tid in visited:
                return
            visited.add(tid)
            
            if tid in self.dependencies:
                chain.append(tid)
                for dep_id in self.dependencies[tid].depends_on:
                    dfs(dep_id)
        
        dfs(task_id)
        return chain
    
    def detect_bottlenecks(self) -> List[Tuple[str, int]]:
        """
        Detect bottleneck tasks (many tasks depend on them)
        Returns: List of (task_id, dependency_count) sorted by count
        """
        dependency_counts: Dict[str, int] = {}
        
        for dep in self.dependencies.values():
            for dep_id in dep.depends_on:
                dependency_counts[dep_id] = dependency_counts.get(dep_id, 0) + 1
        
        bottlenecks = sorted(
            dependency_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Alert on significant bottlenecks
        if bottlenecks and bottlenecks[0][1] >= 3 and self.enable_swarm_alerts:
            task_id, count = bottlenecks[0]
            self._generate_alert(
                alert_type="bottleneck_detected",
                severity=TrafficLight.YELLOW,
                message=f"Bottleneck detected: {count} tasks depend on {task_id}",
                related_items=[task_id]
            )
            self.metrics["bottlenecks_detected"] += 1
        
        return bottlenecks
    
    def get_critical_path(self) -> List[str]:
        """
        Get critical path (longest dependency chain)
        For project planning and WIP limit optimization
        """
        if not self.dependencies:
            return []
        
        max_chain = []
        for task_id in self.dependencies.keys():
            chain = self.get_dependency_chain(task_id)
            if len(chain) > len(max_chain):
                max_chain = chain
        
        return max_chain
    
    # ============ Swarm Coordination ============
    
    def _generate_alert(
        self,
        alert_type: str,
        severity: TrafficLight,
        message: str,
        related_items: List[str]
    ) -> SwarmAlert:
        """Generate swarm coordination alert"""
        alert = SwarmAlert(
            alert_id=f"alert-{len(self.alerts)}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            related_items=related_items
        )
        self.alerts.append(alert)
        self.metrics["alerts_generated"] += 1
        return alert
    
    def get_unacknowledged_alerts(self) -> List[SwarmAlert]:
        """Get alerts requiring attention"""
        return [a for a in self.alerts if not a.acknowledged]
    
    def acknowledge_alert(self, alert_id: str):
        """Mark alert as acknowledged"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                break
    
    def get_swarm_recommendations(self) -> List[str]:
        """Get actionable recommendations for swarm coordination"""
        recommendations = []
        
        # High-priority risks
        high_risks = self.get_high_priority_risks()
        if high_risks:
            recommendations.append(
                f"🔴 {len(high_risks)} high-priority risks require immediate attention"
            )
        
        # Blocked tasks
        blocked = self.get_blocked_tasks()
        if blocked:
            recommendations.append(
                f"🔴 {len(blocked)} tasks blocked - focus on unblocking"
            )
        
        # Bottlenecks
        bottlenecks = self.detect_bottlenecks()
        if bottlenecks and bottlenecks[0][1] >= 3:
            task_id, count = bottlenecks[0]
            recommendations.append(
                f"🟡 Bottleneck at {task_id} ({count} dependencies) - consider parallelizing"
            )
        
        # Ready tasks by lane (for swarming)
        lanes = set(d.lane for d in self.dependencies.values() if d.lane)
        for lane in lanes:
            ready = self.get_ready_tasks_by_lane(lane)
            if ready:
                recommendations.append(
                    f"🟢 {len(ready)} tasks ready in {lane} lane - swarm can proceed"
                )
        
        if not recommendations:
            recommendations.append("✅ No blocking issues - coordination is effective")
        
        return recommendations
    
    # ============ Continuous Monitoring ============
    
    async def start_monitoring(self):
        """Start async background monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Continuous monitoring loop (async background worker)"""
        while self._running:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                print(f"Monitoring cycle error: {e}")
    
    async def _monitoring_cycle(self):
        """Single monitoring cycle"""
        self.metrics["monitoring_cycles"] += 1
        
        # Check for elevated risks
        high_risks = self.get_high_priority_risks()
        for risk in high_risks[:3]:  # Top 3
            if not any(a.related_items == [risk.risk_id] for a in self.alerts[-5:]):
                self._generate_alert(
                    alert_type="risk_elevated",
                    severity=risk.traffic_light,
                    message=f"Risk {risk.risk_id} score: {risk.risk_score:.2f}",
                    related_items=[risk.risk_id]
                )
        
        # Check for long-blocked tasks
        blocked = self.get_blocked_tasks()
        for dep in blocked:
            blocked_duration = (datetime.now() - dep.created_at).total_seconds()
            if blocked_duration > 3600:  # Blocked > 1 hour
                self._generate_alert(
                    alert_type="dependency_blocked",
                    severity=TrafficLight.RED,
                    message=f"Task {dep.task_id} blocked for {blocked_duration/3600:.1f}h",
                    related_items=[dep.task_id]
                )
        
        # Detect bottlenecks
        self.detect_bottlenecks()
    
    # ============ Helper Methods ============
    
    def _check_unblock_dependencies(self, resolved_risk_id: str):
        """Check if resolving risk unblocks any dependencies"""
        for dep in self.dependencies.values():
            if resolved_risk_id in dep.blocked_by:
                dep.blocked_by.remove(resolved_risk_id)
                
                # If no more blockers, mark as ready
                if not dep.blocked_by and not dep.depends_on:
                    dep.status = DependencyStatus.READY
                    
                    if self.enable_swarm_alerts:
                        self._generate_alert(
                            alert_type="dependency_unblocked",
                            severity=TrafficLight.GREEN,
                            message=f"Task {dep.task_id} unblocked - ready to proceed",
                            related_items=[dep.task_id]
                        )
    
    def _check_downstream_dependencies(self, completed_task_id: str):
        """Check if completing task unblocks downstream dependencies"""
        for dep in self.dependencies.values():
            if completed_task_id in dep.depends_on:
                dep.depends_on.remove(completed_task_id)
                
                # If no more dependencies, mark as ready
                if not dep.depends_on and not dep.blocked_by:
                    dep.status = DependencyStatus.READY
    
    # ============ Status Reporting ============
    
    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        total_risks = len(self.risks)
        resolved_risks = sum(1 for r in self.risks.values() if r.status == RiskStatus.RESOLVED)
        high_risks = len(self.get_high_priority_risks())
        
        total_deps = len(self.dependencies)
        blocked_deps = len(self.get_blocked_tasks())
        completed_deps = sum(1 for d in self.dependencies.values() if d.status == DependencyStatus.COMPLETE)
        
        bottlenecks = self.detect_bottlenecks()
        critical_path = self.get_critical_path()
        
        return {
            "risks": {
                "total": total_risks,
                "resolved": resolved_risks,
                "high_priority": high_risks,
                "resolution_rate": resolved_risks / total_risks if total_risks > 0 else 0
            },
            "dependencies": {
                "total": total_deps,
                "blocked": blocked_deps,
                "completed": completed_deps,
                "completion_rate": completed_deps / total_deps if total_deps > 0 else 0
            },
            "bottlenecks": {
                "count": len(bottlenecks),
                "top_3": bottlenecks[:3] if bottlenecks else []
            },
            "critical_path": {
                "length": len(critical_path),
                "tasks": critical_path[:5] if len(critical_path) > 5 else critical_path
            },
            "alerts": {
                "total": len(self.alerts),
                "unacknowledged": len(self.get_unacknowledged_alerts())
            },
            "recommendations": self.get_swarm_recommendations(),
            "metrics": self.metrics
        }


# ============ Factory Functions ============

def create_tracker_for_project(
    project_name: str,
    enable_monitoring: bool = True
) -> RiskDependencyTracker:
    """Create tracker configured for project use"""
    return RiskDependencyTracker(
        monitoring_interval=60.0,
        risk_threshold=0.7,
        enable_swarm_alerts=enable_monitoring
    )


def create_tracker_for_sprint(
    sprint_duration_days: int = 14
) -> RiskDependencyTracker:
    """Create tracker configured for sprint use"""
    # More frequent monitoring for sprints
    return RiskDependencyTracker(
        monitoring_interval=30.0,  # Check every 30s
        risk_threshold=0.6,  # Lower threshold for sprints
        enable_swarm_alerts=True
    )
