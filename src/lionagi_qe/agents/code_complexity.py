"""Code Complexity Analyzer Agent - Educational example of AQE Fleet architecture"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class ComplexityIssue(BaseModel):
    """Code complexity issue"""

    file_path: str = Field(..., description="Path to file with complexity issue")
    line_number: int = Field(..., description="Line number of issue")
    issue_type: str = Field(
        ..., description="Type of issue (cyclomatic, cognitive, file_size)"
    )
    current_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold value")
    severity: str = Field(..., description="Issue severity (low, medium, high, critical)")
    description: str = Field(..., description="Human-readable description")
    recommendation: str = Field(..., description="Recommended action")


class RefactoringRecommendation(BaseModel):
    """AI-powered refactoring recommendation"""

    file_path: str = Field(..., description="File to refactor")
    pattern: str = Field(..., description="Refactoring pattern to apply")
    priority: str = Field(..., description="Priority (low, medium, high, critical)")
    description: str = Field(..., description="Why this refactoring is needed")
    expected_improvement: str = Field(..., description="Expected improvement")
    effort_estimate: str = Field(..., description="Estimated effort (small, medium, large)")


class CodeComplexityResult(BaseModel):
    """Code complexity analysis result"""

    score: float = Field(..., description="Overall quality score (0-100)")
    issues: List[ComplexityIssue] = Field(..., description="Complexity issues found")
    recommendations: List[RefactoringRecommendation] = Field(
        default_factory=list, description="Refactoring recommendations"
    )
    metrics: Dict[str, Any] = Field(..., description="Detailed complexity metrics")
    summary: str = Field(..., description="Executive summary of findings")


class CodeComplexityAnalyzerAgent(BaseQEAgent):
    """Educational code complexity analyzer demonstrating AQE Fleet architecture

    This agent serves as a learning example showing:
    - BaseAgent pattern and lifecycle hooks
    - Memory system usage for coordination
    - Event-driven architecture
    - Pattern learning and adaptation
    - Integration with other agents

    Capabilities:
    - Cyclomatic complexity analysis
    - Cognitive complexity measurement
    - File size analysis
    - Function metrics tracking
    - AI-powered refactoring recommendations
    - Quality scoring and prioritization
    """

    def __init__(
        self,
        agent_id: str,
        model: Any,
        memory: Optional[Any] = None,
        skills: Optional[List[str]] = None,
        enable_learning: bool = False,
        q_learning_service: Optional[Any] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize CodeComplexity Agent

        Args:
            agent_id: Unique agent identifier
            model: LionAGI model instance
            memory: Memory backend (PostgresMemory/RedisMemory/QEMemory or None for Session.context)
            skills: List of QE skills this agent uses
            enable_learning: Enable Q-learning integration
            q_learning_service: Optional Q-learning service instance
            memory_config: Optional config for auto-initializing memory backend
        """
        super().__init__(
            agent_id=agent_id,
            model=model,
            memory=memory,
            skills=skills or ['agentic-quality-engineering', 'code-review-quality', 'refactoring-patterns'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an educational code complexity analyzer agent demonstrating the Agentic QE Fleet architecture.

**Core Capabilities:**
- Cyclomatic Complexity: Measures decision point density in code
- Cognitive Complexity: Accounts for nesting and control flow complexity
- File Size Analysis: Identifies overly large files that need splitting
- Function Metrics: Tracks function count and average complexity
- Refactoring Recommendations: AI-powered suggestions based on patterns

**Analysis Metrics:**
1. Cyclomatic Complexity:
   - Measures number of linearly independent paths through code
   - Threshold: 10 (recommended maximum)
   - High values indicate: Too many decision points, hard to test

2. Cognitive Complexity:
   - Accounts for nesting depth and control flow complexity
   - Threshold: 15 (recommended maximum)
   - High values indicate: Hard to understand, error-prone

3. File Size:
   - Measures lines of code per file
   - Threshold: 300 lines (recommended maximum)
   - Large files indicate: Poor separation of concerns

4. Function Count:
   - Number of functions per file
   - Helps identify god objects and proper modularization

**Refactoring Patterns:**
- Extract Method: Break down long functions
- Extract Class: Separate concerns in large files
- Reduce Nesting: Use early returns and guard clauses
- Simplify Conditionals: Replace complex conditions with well-named functions
- Replace Magic Numbers: Use named constants
- Remove Dead Code: Eliminate unused code paths

**Severity Levels:**
- Low: Minor issues, refactor when convenient
- Medium: Should be addressed in next sprint
- High: Address soon, impacts maintainability
- Critical: Address immediately, blocks quality gate

**Quality Scoring (0-100):**
- Start at 100
- Deduct points for each issue based on severity:
  - Low: -5 points
  - Medium: -10 points
  - High: -20 points
  - Critical: -30 points
- Minimum score: 0

**Learning Objectives:**
This agent demonstrates:
1. BaseAgent pattern (extending base functionality)
2. Lifecycle hooks (onPreTask, onPostTask, onTaskError)
3. Memory system (storing/retrieving coordination data)
4. Event system (emitting events for other agents)
5. Pattern learning (storing successful analysis patterns)
6. Agent coordination (sharing data via memory namespace)"""

    async def execute(self, task: QETask) -> CodeComplexityResult:
        """Analyze code complexity and provide recommendations

        Args:
            task: Task containing:
                - files: List of files to analyze with content
                - thresholds: Custom complexity thresholds
                - enable_recommendations: Whether to generate refactoring suggestions

        Returns:
            CodeComplexityResult with issues and recommendations
        """
        context = task.context
        files = context.get("files", [])
        thresholds = context.get("thresholds", {
            "cyclomatic_complexity": 10,
            "cognitive_complexity": 15,
            "lines_of_code": 300,
        })
        enable_recommendations = context.get("enable_recommendations", True)

        # Retrieve historical analysis for pattern learning
        historical_analyses = await self.get_memory(
            f"aqe/complexity/{self.config.agent_id}/history",
            default=[]
        )

        # Execute complexity analysis
        result = await self.operate(
            instruction=f"""Analyze code complexity and provide refactoring recommendations.

Files to Analyze:
```json
{files}
```

Complexity Thresholds:
- Cyclomatic Complexity: {thresholds.get('cyclomatic_complexity', 10)}
- Cognitive Complexity: {thresholds.get('cognitive_complexity', 15)}
- Lines of Code: {thresholds.get('lines_of_code', 300)}

Historical Context (for pattern learning):
```json
{historical_analyses[-5:] if historical_analyses else []}
```

Analysis Requirements:
1. Calculate Complexity Metrics:
   - Cyclomatic complexity per function
   - Cognitive complexity accounting for nesting
   - Lines of code per file
   - Function count per file
   - Average complexity scores

2. Identify Issues:
   - For each metric exceeding threshold, create an issue
   - Classify severity: low, medium, high, critical
   - Provide file path and line number
   - Give clear description of the problem
   - Suggest specific remediation

3. Quality Scoring (0-100):
   - Start at 100 points
   - Deduct based on severity:
     * Critical: -30 points
     * High: -20 points
     * Medium: -10 points
     * Low: -5 points
   - Minimum score: 0

{f'''4. Generate Refactoring Recommendations:
   - Suggest specific patterns (Extract Method, Reduce Nesting, etc.)
   - Prioritize by severity and impact
   - Estimate effort (small, medium, large)
   - Explain expected improvements''' if enable_recommendations else ''}

5. Provide Executive Summary:
   - Overall quality assessment
   - Top 3 priority items
   - Estimated total refactoring effort

Output Format:
- Overall quality score (0-100)
- List of all complexity issues with details
- Refactoring recommendations ranked by priority
- Detailed metrics breakdown
- Executive summary for stakeholders""",
            context={
                "files": files,
                "thresholds": thresholds,
                "enable_recommendations": enable_recommendations,
                "historical_analyses": historical_analyses,
            },
            response_format=CodeComplexityResult,
        )

        # Store analysis results for coordination
        await self.store_memory(
            f"aqe/complexity/{self.config.agent_id}/latest-result",
            {
                "score": result.score,
                "issues_count": len(result.issues),
                "critical_issues": len([i for i in result.issues if i.severity == "critical"]),
                "recommendations_count": len(result.recommendations),
                "timestamp": task.created_at.isoformat(),
            },
        )

        # Append to historical analyses (keep last 100)
        current_history = await self.get_memory(
            f"aqe/complexity/{self.config.agent_id}/history",
            default=[]
        )
        current_history.append({
            "timestamp": task.created_at.isoformat(),
            "score": result.score,
            "files_analyzed": len(files),
            "issues_found": len(result.issues),
        })
        await self.store_memory(
            f"aqe/complexity/{self.config.agent_id}/history",
            current_history[-100:]  # Keep last 100 analyses
        )

        # Store learned pattern if analysis was valuable
        if len(result.issues) > 0 and enable_recommendations:
            await self.store_learned_pattern(
                f"complexity_analysis_{len(files)}_files",
                {
                    "files_count": len(files),
                    "issues_found": len(result.issues),
                    "pattern": "complexity_analysis_completed",
                    "recommendations_generated": len(result.recommendations),
                },
            )

        return result
