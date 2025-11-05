"""Requirements Validator Agent - Validates requirements testability and generates BDD scenarios"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class RequirementIssue(BaseModel):
    """Issue found in requirement validation"""

    issue_type: str = Field(..., description="Type of issue (ambiguity, missing_criteria, etc.)")
    severity: str = Field(..., description="Severity: CRITICAL, HIGH, MEDIUM, LOW")
    description: str = Field(..., description="Description of the issue")
    recommendation: str = Field(..., description="Recommended fix or improvement")


class BDDScenario(BaseModel):
    """Generated BDD scenario"""

    feature: str = Field(..., description="Feature being tested")
    scenario_name: str = Field(..., description="Scenario name")
    given: List[str] = Field(..., description="Given steps (preconditions)")
    when: List[str] = Field(..., description="When steps (actions)")
    then: List[str] = Field(..., description="Then steps (expected outcomes)")
    background: Optional[List[str]] = Field(default=None, description="Background steps")
    examples: Optional[Dict[str, List[Any]]] = Field(default=None, description="Scenario outline examples")


class AcceptanceCriteria(BaseModel):
    """Enhanced SMART acceptance criteria"""

    criteria_id: str = Field(..., description="Unique criteria identifier")
    description: str = Field(..., description="Criteria description")
    is_specific: bool = Field(..., description="Meets Specific criterion")
    is_measurable: bool = Field(..., description="Meets Measurable criterion")
    is_achievable: bool = Field(..., description="Meets Achievable criterion")
    is_relevant: bool = Field(..., description="Meets Relevant criterion")
    is_timebound: bool = Field(..., description="Meets Time-bound criterion")
    metrics: List[str] = Field(default_factory=list, description="Measurable metrics")
    test_scenarios: List[str] = Field(default_factory=list, description="Related test scenarios")


class RiskAssessment(BaseModel):
    """Requirement risk assessment"""

    risk_score: float = Field(..., description="Overall risk score (0-10)", ge=0, le=10)
    complexity_score: float = Field(..., description="Technical complexity (0-10)", ge=0, le=10)
    impact_level: str = Field(..., description="Impact: CRITICAL, HIGH, MEDIUM, LOW")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    mitigation_strategy: str = Field(..., description="Recommended mitigation approach")
    testing_priority: str = Field(..., description="Testing priority based on risk")


class TraceabilityLink(BaseModel):
    """Traceability mapping entry"""

    requirement_id: str = Field(..., description="Requirement identifier")
    epic_id: Optional[str] = Field(default=None, description="Related epic")
    user_story_id: Optional[str] = Field(default=None, description="Related user story")
    acceptance_criteria_ids: List[str] = Field(default_factory=list, description="Acceptance criteria IDs")
    bdd_scenario_ids: List[str] = Field(default_factory=list, description="BDD scenario IDs")
    test_case_ids: List[str] = Field(default_factory=list, description="Test case IDs")
    code_modules: List[str] = Field(default_factory=list, description="Related code modules")


class EdgeCase(BaseModel):
    """Identified edge case"""

    category: str = Field(..., description="Edge case category (boundary, null, concurrent, etc.)")
    description: str = Field(..., description="Description of the edge case")
    test_approach: str = Field(..., description="Recommended testing approach")
    priority: str = Field(..., description="Priority: HIGH, MEDIUM, LOW")


class RequirementValidationResult(BaseModel):
    """Complete requirement validation result"""

    requirement_id: str = Field(..., description="Unique requirement identifier")
    requirement_text: str = Field(..., description="Original requirement text")
    testability_score: float = Field(..., description="Testability score (0-10)", ge=0, le=10)
    invest_score: Dict[str, float] = Field(
        ...,
        description="INVEST criteria scores (Independent, Negotiable, Valuable, Estimable, Small, Testable)"
    )
    issues: List[RequirementIssue] = Field(..., description="Identified issues")
    enhanced_criteria: List[AcceptanceCriteria] = Field(..., description="Enhanced acceptance criteria")
    bdd_scenarios: List[BDDScenario] = Field(..., description="Generated BDD scenarios")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    edge_cases: List[EdgeCase] = Field(..., description="Identified edge cases")
    traceability: TraceabilityLink = Field(..., description="Traceability mapping")
    completeness_score: float = Field(..., description="Completeness score (0-100)", ge=0, le=100)
    validation_status: str = Field(..., description="Status: APPROVED, NEEDS_ENHANCEMENT, BLOCKED")
    recommendations: List[str] = Field(..., description="Overall recommendations")


class RequirementsValidatorAgent(BaseQEAgent):
    """Validates requirements for testability and generates BDD scenarios

    Capabilities:
    - INVEST criteria validation
    - BDD scenario generation (Given-When-Then)
    - Risk assessment and scoring
    - SMART acceptance criteria validation
    - Traceability mapping
    - Edge case identification
    - Requirement completeness checking (5 Ws framework)
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
        """Initialize RequirementsValidator Agent

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
            skills=skills or ['agentic-quality-engineering', 'context-driven-testing', 'risk-based-testing'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        return """You are an expert requirements validation agent specializing in:

**Core Capabilities:**

1. **Testability Analysis**:
   - Evaluate requirements against INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)
   - Detect ambiguity using NLP analysis
   - Identify missing acceptance criteria
   - Assess quantifiability and measurability
   - Score requirements for testability (0-10 scale)

2. **BDD Scenario Generation**:
   - Generate comprehensive Gherkin scenarios (Given-When-Then)
   - Cover happy paths, edge cases, and error conditions
   - Include scenario outlines with data tables
   - Map scenarios to acceptance criteria
   - Follow BDD best practices

3. **Risk Assessment**:
   - Score complexity, dependencies, and impact
   - Identify security, performance, and compliance risks
   - Create risk matrices (likelihood vs impact)
   - Recommend testing priorities based on risk
   - Flag high-risk requirements for review

4. **SMART Acceptance Criteria**:
   - Validate against SMART framework (Specific, Measurable, Achievable, Relevant, Time-bound)
   - Enhance vague criteria with measurable metrics
   - Define clear success conditions
   - Add performance expectations and SLAs
   - Ensure technical feasibility

5. **Traceability Mapping**:
   - Create bidirectional traceability (business requirement → code → deployment)
   - Map requirements to epics, user stories, test cases
   - Track requirement evolution over time
   - Ensure 100% traceability coverage

6. **Edge Case Identification**:
   - Use boundary value analysis
   - Identify null/undefined/missing data scenarios
   - Detect concurrent operation risks
   - Find internationalization edge cases
   - Uncover resource exhaustion scenarios

7. **Completeness Checking**:
   - Apply 5 Ws framework (Who, What, When, Where, Why, How)
   - Verify all user roles are identified
   - Ensure business value is articulated
   - Check deployment contexts are specified
   - Validate technical constraints are documented

**Skills Available:**
- shift-left-testing: Move testing activities earlier in development lifecycle
- test-design-techniques: Advanced test design patterns
- agentic-quality-engineering: AI-powered quality engineering
- risk-based-testing: Focus effort on highest-risk areas

**Output Standards:**
- Provide actionable, specific recommendations
- Use consistent scoring scales (0-10 for quality, 0-100 for completeness)
- Flag CRITICAL, HIGH, MEDIUM, LOW severity issues
- Generate production-ready BDD scenarios
- Include concrete examples and metrics
- Maintain professional, constructive tone

**Best Practices:**
- Validate early (backlog grooming, not sprint planning)
- Collaborate with product management
- Use validation reports to enhance requirement quality
- Maintain traceability as code evolves
- Learn from production issues to improve patterns"""

    async def execute(self, task: QETask) -> RequirementValidationResult:
        """Validate requirement for testability and generate BDD scenarios

        Args:
            task: Task containing:
                - requirement_text: Requirement to validate
                - requirement_id: Unique requirement identifier
                - context: Additional context (epic, user story, etc.)
                - historical_defects: Past issues related to similar requirements

        Returns:
            RequirementValidationResult with validation analysis and BDD scenarios
        """
        context = task.context
        requirement_text = context.get("requirement_text", "")
        requirement_id = context.get("requirement_id", f"REQ-{task.task_id}")
        additional_context = context.get("context", {})
        historical_defects = context.get("historical_defects", [])

        # Retrieve learned patterns from memory
        learned_patterns = await self.get_learned_patterns()

        # Retrieve historical validation data
        historical_validations = await self.search_memory(
            r"aqe/requirements/validated/.*"
        )

        # Generate validation result
        result = await self.operate(
            instruction=f"""Validate the following requirement for testability and generate comprehensive BDD scenarios.

Requirement ID: {requirement_id}
Requirement Text:
{requirement_text}

Additional Context:
{additional_context}

Historical Defects (if available):
{historical_defects}

{f"Learned Patterns: {learned_patterns}" if learned_patterns else ""}

{f"Historical Validations: {len(historical_validations)} similar requirements validated" if historical_validations else ""}

**Validation Tasks:**

1. **INVEST Analysis**: Score each criterion (0-10):
   - Independent: Can this requirement be developed independently?
   - Negotiable: Is there room for discussion on implementation?
   - Valuable: Does it provide clear business value?
   - Estimable: Can the team estimate effort required?
   - Small: Is it small enough to complete in a sprint?
   - Testable: Can success be verified objectively?

2. **Testability Score**: Overall score (0-10) based on:
   - Clarity and specificity
   - Measurable success criteria
   - Completeness of acceptance criteria
   - Identifiable test scenarios

3. **Issue Identification**: Find all issues:
   - Ambiguous language ("should be fast", "user-friendly")
   - Missing acceptance criteria
   - Unmeasurable success metrics
   - Technical infeasibility
   - Missing edge cases

4. **BDD Scenario Generation**: Create comprehensive scenarios:
   - Feature description (As a... I want... So that...)
   - Background steps (if needed)
   - Positive scenarios (happy path)
   - Negative scenarios (error conditions)
   - Boundary scenarios (edge cases)
   - Scenario outlines with data tables (when applicable)

5. **Risk Assessment**:
   - Complexity score (0-10): Technical difficulty
   - Impact level: CRITICAL, HIGH, MEDIUM, LOW
   - Risk factors: Dependencies, integrations, security, performance
   - Mitigation strategy: How to reduce risk
   - Testing priority: Based on risk matrix

6. **SMART Acceptance Criteria**: Enhance criteria to be:
   - Specific: Clear, concrete definitions
   - Measurable: Quantifiable metrics (response time, error rate, etc.)
   - Achievable: Technically feasible
   - Relevant: Aligned with business goals
   - Time-bound: Performance expectations, SLAs

7. **Edge Cases**: Identify using:
   - Boundary value analysis (min/max, empty/full)
   - Null/undefined/missing data
   - Concurrent operations
   - Network failures
   - Internationalization (UTF-8, timezones, locales)

8. **Traceability**: Map requirement to:
   - Epic and user story (if available)
   - Acceptance criteria IDs
   - BDD scenario IDs
   - Expected test case count
   - Code modules to be implemented

9. **Completeness Check** (5 Ws):
   - Who: User roles and actors
   - What: Features and functionalities
   - When: Timing, triggers, scheduling
   - Where: Deployment environments
   - Why: Business value and user needs
   - How: Technical approach

10. **Validation Status**:
    - APPROVED: Ready for implementation
    - NEEDS_ENHANCEMENT: Requires clarification/improvement
    - BLOCKED: Critical issues prevent implementation

Provide comprehensive, actionable feedback with specific examples and recommendations.""",
            context={
                "requirement_text": requirement_text,
                "requirement_id": requirement_id,
                "additional_context": additional_context,
                "historical_defects": historical_defects,
                "learned_patterns": learned_patterns,
            },
            response_format=RequirementValidationResult
        )

        # Store validation result in memory
        await self.store_result(
            f"validated/{requirement_id}",
            result.model_dump(),
            ttl=2592000  # 30 days
        )

        # Store BDD scenarios
        await self.store_result(
            f"bdd-scenarios/{requirement_id}",
            [scenario.model_dump() for scenario in result.bdd_scenarios],
            ttl=2592000
        )

        # Store risk assessment
        await self.memory.store(
            f"aqe/risk-scores/{requirement_id}",
            result.risk_assessment.model_dump(),
            partition="risk_scores",
            ttl=2592000
        )

        # Learn from high-quality validations
        if result.testability_score >= 8.0 and result.completeness_score >= 90.0:
            await self.store_learned_pattern(
                f"high_quality_{requirement_id}",
                {
                    "requirement_type": additional_context.get("type", "unknown"),
                    "testability_score": result.testability_score,
                    "completeness_score": result.completeness_score,
                    "bdd_scenario_count": len(result.bdd_scenarios),
                    "pattern": "high_quality_validation",
                }
            )

        return result

    async def batch_validate(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[RequirementValidationResult]:
        """Validate multiple requirements in batch

        Args:
            requirements: List of requirements with text and IDs

        Returns:
            List of validation results
        """
        results = []
        for req in requirements:
            task = QETask(
                task_id=req.get("requirement_id", f"REQ-{len(results)}"),
                task_type="requirement_validation",
                context={
                    "requirement_text": req.get("text", ""),
                    "requirement_id": req.get("requirement_id"),
                    "context": req.get("context", {}),
                    "historical_defects": req.get("historical_defects", []),
                }
            )
            result = await self.execute(task)
            results.append(result)

        return results

    async def generate_traceability_matrix(
        self,
        requirement_ids: List[str]
    ) -> Dict[str, TraceabilityLink]:
        """Generate traceability matrix for multiple requirements

        Args:
            requirement_ids: List of requirement IDs

        Returns:
            Dict mapping requirement IDs to traceability links
        """
        matrix = {}
        for req_id in requirement_ids:
            validation = await self.retrieve_context(
                f"aqe/requirements-validator/validated/{req_id}"
            )
            if validation:
                matrix[req_id] = TraceabilityLink(**validation["traceability"])

        return matrix

    async def get_validation_status(self) -> Dict[str, Any]:
        """Get overall validation status and metrics

        Returns:
            Dict with validation statistics
        """
        validations = await self.search_memory(
            r"aqe/requirements-validator/validated/.*"
        )

        approved = sum(
            1 for v in validations.values()
            if v.get("validation_status") == "APPROVED"
        )
        needs_enhancement = sum(
            1 for v in validations.values()
            if v.get("validation_status") == "NEEDS_ENHANCEMENT"
        )
        blocked = sum(
            1 for v in validations.values()
            if v.get("validation_status") == "BLOCKED"
        )

        avg_testability = (
            sum(v.get("testability_score", 0) for v in validations.values())
            / len(validations)
            if validations
            else 0
        )

        avg_completeness = (
            sum(v.get("completeness_score", 0) for v in validations.values())
            / len(validations)
            if validations
            else 0
        )

        return {
            "total_validations": len(validations),
            "approved": approved,
            "needs_enhancement": needs_enhancement,
            "blocked": blocked,
            "avg_testability_score": round(avg_testability, 2),
            "avg_completeness_score": round(avg_completeness, 2),
            "total_bdd_scenarios": sum(
                len(v.get("bdd_scenarios", []))
                for v in validations.values()
            ),
        }
