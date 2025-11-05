"""
QE API Contract Validator Agent

Mission: Validates API contracts, detects breaking changes, and ensures backward
compatibility across services, preventing 95% of API breaking changes.

Capabilities:
- Schema validation against OpenAPI, GraphQL, JSON Schema
- Breaking change detection between API versions
- Version compatibility and semantic versioning validation
- Contract diffing with visual representation
- Consumer impact analysis
- Contract-first testing with Pact integration
- Semantic versioning compliance enforcement
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime


# ============================================================================
# Pydantic Result Models
# ============================================================================

class ValidationError(BaseModel):
    """A validation error"""
    type: str
    path: Optional[str] = None
    message: str
    params: Optional[Dict[str, Any]] = None


class SchemaValidationResult(BaseModel):
    """Result of schema validation"""
    valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)


class BreakingChange(BaseModel):
    """A detected breaking change"""
    type: Literal[
        "ENDPOINT_REMOVED", "METHOD_REMOVED", "REQUIRED_PARAM_REMOVED",
        "PARAM_BECAME_REQUIRED", "PARAM_TYPE_CHANGED", "NEW_REQUIRED_PARAM",
        "REQUEST_BODY_REQUIRED", "REQUEST_BODY_REMOVED",
        "RESPONSE_STATUS_REMOVED", "REQUIRED_FIELD_REMOVED",
        "FIELD_REMOVED", "FIELD_TYPE_CHANGED"
    ]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status: Optional[int] = None
    field: Optional[str] = None
    param: Optional[str] = None
    old_type: Optional[str] = None
    new_type: Optional[str] = None
    message: str
    impact: Optional[Dict[str, Any]] = None
    recommendation: str


class NonBreakingChange(BaseModel):
    """A non-breaking change"""
    type: Literal[
        "FIELD_ADDED", "OPTIONAL_PARAM_ADDED", "OPTIONAL_PARAM_REMOVED",
        "ENDPOINT_ADDED", "METHOD_ADDED", "RESPONSE_STATUS_ADDED"
    ]
    endpoint: Optional[str] = None
    status: Optional[int] = None
    field: Optional[str] = None
    param: Optional[str] = None
    message: str
    impact: str


class BreakingChangeReport(BaseModel):
    """Complete breaking change report"""
    baseline: str
    candidate: str
    timestamp: datetime
    breaking_changes: List[BreakingChange]
    non_breaking_changes: List[NonBreakingChange]
    summary: Dict[str, Any]


class VersionBump(BaseModel):
    """Version bump validation"""
    valid: bool
    current_version: str
    proposed_version: str
    required_bump: Literal["MAJOR", "MINOR", "PATCH"]
    actual_bump: Literal["MAJOR", "MINOR", "PATCH"]
    recommendation: str
    violations: List[Dict[str, str]] = Field(default_factory=list)


class AffectedEndpoint(BaseModel):
    """An endpoint affected by changes"""
    endpoint: str
    method: str
    requests_per_day: int
    changes: List[BreakingChange]
    migration_effort: Literal["LOW", "MEDIUM", "HIGH"]


class ConsumerImpact(BaseModel):
    """Impact on a single consumer"""
    consumer: str
    team: str
    contact: str
    affected_endpoints: List[AffectedEndpoint]
    total_requests: int
    estimated_migration_time: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class ConsumerImpactAnalysis(BaseModel):
    """Complete consumer impact analysis"""
    baseline: str
    candidate: str
    breaking_changes: int
    affected_consumers: int
    top_impacted_consumers: List[ConsumerImpact]
    recommendation: Dict[str, Any]


class ContractDiff(BaseModel):
    """Contract diff between versions"""
    baseline: str
    candidate: str
    breaking_changes_count: int
    non_breaking_changes_count: int
    recommended_version: str
    estimated_migration_time: str
    affected_consumers: int
    diff_visualization: str


class APIContractValidatorResult(BaseModel):
    """Complete API contract validator result"""
    schema_validation: SchemaValidationResult
    breaking_changes: Optional[BreakingChangeReport] = None
    version_compatibility: Optional[VersionBump] = None
    consumer_impact: Optional[ConsumerImpactAnalysis] = None
    contract_diff: Optional[ContractDiff] = None
    recommendation: str


# ============================================================================
# System Prompt
# ============================================================================

API_CONTRACT_VALIDATOR_PROMPT = """You are the QE API Contract Validator, an expert at preventing breaking API changes and ensuring backward compatibility.

## Your Mission

**Prevent breaking API changes** by validating contracts against consumer expectations, detecting backward compatibility issues, and ensuring semantic versioning compliance. Using contract-first testing, schema validation, and consumer-driven contracts, catch 95% of integration issues before deployment.

## Core Capabilities

### 1. Schema Validation
- Validate requests/responses against OpenAPI, GraphQL, JSON Schema
- Check parameter types, required fields, formats
- Validate status codes and headers
- Detect undocumented endpoints
- Ensure schema compliance across all API operations

### 2. Breaking Change Detection
- Compare baseline vs candidate schemas
- Detect removed endpoints or methods
- Identify removed required parameters
- Catch parameter type changes
- Find removed required response fields
- Flag new required parameters
- Detect response schema changes

### 3. Version Compatibility
- Validate semantic versioning compliance
- Ensure proper version bumps for changes:
  - **MAJOR**: Breaking changes
  - **MINOR**: New features (backward compatible)
  - **PATCH**: Bug fixes only
- Recommend appropriate version numbers
- Enforce versioning policies

### 4. Contract Diffing
- Generate detailed diffs between versions
- Visualize changes with clear formatting
- Categorize changes by severity
- Highlight breaking vs non-breaking changes
- Provide migration recommendations

### 5. Consumer Impact Analysis
- Identify which consumers use affected endpoints
- Calculate request volumes per consumer
- Estimate migration effort and timeline
- Prioritize consumers by impact
- Generate notification lists
- Track migration progress

### 6. Contract Testing
- Generate Pact contract tests from schemas
- Validate provider against consumer contracts
- Implement consumer-driven contract testing
- Ensure contract compliance
- Automate contract verification

### 7. Semantic Versioning Validation
- Enforce semver rules:
  - Breaking changes → Major bump required
  - New features → Minor bump required
  - Bug fixes only → Patch bump allowed
- Validate version bump matches change severity
- Block deployments with incorrect versions

## Breaking Change Categories

### CRITICAL Severity
- **ENDPOINT_REMOVED**: Endpoint no longer exists
- **REQUIRED_FIELD_REMOVED**: Required response field removed
- **REQUEST_BODY_REMOVED**: Request body requirement removed
- **RESPONSE_STATUS_REMOVED**: Success status code removed

### HIGH Severity
- **PARAM_TYPE_CHANGED**: Parameter type incompatibly changed
- **PARAM_BECAME_REQUIRED**: Optional parameter now required
- **NEW_REQUIRED_PARAM**: New required parameter added
- **FIELD_TYPE_CHANGED**: Response field type changed

### MEDIUM Severity
- **METHOD_REMOVED**: HTTP method removed from endpoint
- **REQUIRED_PARAM_REMOVED**: Required parameter removed (if optional alternatives exist)

### LOW Severity
- **FIELD_REMOVED**: Non-required response field removed

## Non-Breaking Changes

These are **backward compatible**:
- **FIELD_ADDED**: New response field added
- **OPTIONAL_PARAM_ADDED**: New optional parameter added
- **ENDPOINT_ADDED**: New endpoint added
- **METHOD_ADDED**: New HTTP method on existing endpoint
- **RESPONSE_STATUS_ADDED**: New response status code

## Validation Strategy

### 1. Request Validation
Check:
- All required path parameters present
- All required query parameters present
- Request body matches schema
- Content-Type header correct
- Parameter types match specification

### 2. Response Validation
Check:
- Status code documented in schema
- Response body matches schema
- All required fields present
- Field types match specification
- Headers match specification

### 3. Change Detection
Compare:
- Endpoints (paths)
- HTTP methods
- Parameters (path, query, header, body)
- Request schemas
- Response schemas
- Status codes

### 4. Impact Assessment
Analyze:
- Consumer usage patterns
- Request volumes
- Critical vs non-critical consumers
- Migration complexity
- Timeline estimates

## Output Requirements

Provide comprehensive reports including:
1. **Schema Validation**: All validation errors and warnings
2. **Breaking Changes**: Complete list with severity and impact
3. **Version Recommendation**: Appropriate semantic version
4. **Consumer Impact**: Affected consumers and migration effort
5. **Contract Diff**: Visual representation of changes
6. **Recommendations**: Actions to prevent breaking consumers

## Decision Logic

### Allow Deployment If:
- No breaking changes detected
- Only non-breaking changes
- Proper version bump (minor/patch)
- All schema validations pass

### Block Deployment If:
- Breaking changes detected
- Insufficient version bump (patch when major needed)
- Schema validation failures
- High-impact consumers affected without coordination

### Require Coordination If:
- Breaking changes with >10 affected consumers
- Changes to critical business APIs
- External partner integrations affected
- Migration timeline >2 weeks

## Example Scenarios

### Scenario 1: Safe Change
- Added new optional field `profilePicture` to `/users/{id}` response
- **Result**: Non-breaking, allow with MINOR version bump

### Scenario 2: Breaking Change
- Removed required field `username` from `/users/{id}` response
- **Result**: CRITICAL breaking change, require MAJOR version bump + consumer coordination

### Scenario 3: Type Change
- Changed `quantity` parameter from `integer` to `string`
- **Result**: HIGH severity breaking change, recommend revert or MAJOR bump

Focus on preventing integration failures and ensuring smooth API evolution."""


# ============================================================================
# Agent Implementation
# ============================================================================

from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class APIContractValidatorAgent(BaseQEAgent):
    """API Contract Validator Agent

    Validates API contracts, detects breaking changes, and ensures backward
    compatibility across services, preventing 95% of API breaking changes.

    Capabilities:
    - Schema validation against OpenAPI, GraphQL, JSON Schema
    - Breaking change detection between API versions
    - Version compatibility and semantic versioning validation
    - Contract diffing with visual representation
    - Consumer impact analysis
    - Contract-first testing with Pact integration
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
        """Initialize ApiContractValidator Agent

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
            skills=skills or ['agentic-quality-engineering', 'contract-testing', 'api-testing-patterns'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        """Define agent expertise"""
        return API_CONTRACT_VALIDATOR_PROMPT

    async def execute(self, task: QETask) -> APIContractValidatorResult:
        """Execute API contract validation

        Args:
            task: Task containing:
                - baseline_schema: Baseline API schema (OpenAPI, GraphQL)
                - candidate_schema: New API schema to validate (optional)
                - consumers: List of API consumers with usage patterns (optional)
                - current_version: Current API version (optional)
                - proposed_version: Proposed new version (optional)

        Returns:
            APIContractValidatorResult with validation results
        """
        # Extract context
        context = task.context
        baseline_schema = context.get("baseline_schema", "")
        candidate_schema = context.get("candidate_schema")
        consumers = context.get("consumers", [])
        current_version = context.get("current_version")
        proposed_version = context.get("proposed_version")

        # Retrieve validation history from memory
        validation_history = await self.get_memory(
            "aqe/api/validation-history",
            default=[]
        )

        # Use LionAGI to perform contract validation
        result = await self.operate(
            instruction=f"""Validate API contract and detect breaking changes.

            Baseline Schema:
            ```
            {baseline_schema}
            ```

            {f'''Candidate Schema:
            ```
            {candidate_schema}
            ```
            ''' if candidate_schema else ''}

            {f'Current Version: {current_version}' if current_version else ''}
            {f'Proposed Version: {proposed_version}' if proposed_version else ''}
            {f'Consumer Count: {len(consumers)}' if consumers else ''}

            Requirements:
            1. Validate schema structure and compliance (OpenAPI/GraphQL)
            2. Detect breaking changes between baseline and candidate
            3. Categorize changes by severity (CRITICAL, HIGH, MEDIUM, LOW)
            4. Analyze consumer impact for each breaking change
            5. Validate semantic versioning compliance
            6. Generate contract diff visualization
            7. Provide deployment recommendation (ALLOW/BLOCK/COORDINATE)

            Use validation history for pattern recognition:
            {validation_history[:5] if validation_history else "No history available"}
            """,
            response_format=APIContractValidatorResult,
        )

        # Store validation result in memory
        await self.store_memory(
            "aqe/api/contracts/latest",
            result.model_dump(),
        )

        # Update validation history
        baseline_excerpt = str(baseline_schema)[:100] if baseline_schema else ""
        validation_history.append({
            "timestamp": datetime.now().isoformat(),
            "baseline": baseline_excerpt,  # Store excerpt
            "breaking_changes": len(result.breaking_changes.breaking_changes) if result.breaking_changes else 0,
            "recommendation": result.recommendation,
        })
        await self.store_memory(
            "aqe/api/validation-history",
            validation_history[-50:],  # Keep last 50 validations
        )

        # Call post execution hook to update metrics
        await self.post_execution_hook(task, result.model_dump())

        return result


# ============================================================================
# Placeholder Function (For Backward Compatibility)
# ============================================================================

def execute(
    baseline_schema: str,
    candidate_schema: Optional[str] = None,
    consumers: Optional[List[Dict[str, Any]]] = None,
    current_version: Optional[str] = None,
    proposed_version: Optional[str] = None
) -> APIContractValidatorResult:
    """
    Execute API contract validation.

    Args:
        baseline_schema: Baseline API schema (OpenAPI, GraphQL)
        candidate_schema: New API schema to validate (optional)
        consumers: List of API consumers with usage patterns
        current_version: Current API version
        proposed_version: Proposed new version

    Returns:
        APIContractValidatorResult with validation results

    Note:
        This is a placeholder implementation. In production, this would:
        1. Parse OpenAPI/GraphQL schemas
        2. Validate requests/responses against schema
        3. Compare baseline vs candidate for breaking changes
        4. Analyze consumer impact
        5. Validate semantic versioning
        6. Generate contract tests
        7. Provide recommendations
    """
    # Placeholder implementation
    # In production, integrate with:
    # - OpenAPI parsers (swagger-parser, openapi-diff)
    # - GraphQL schema tools
    # - Pact for contract testing
    # - Consumer registry

    # Example result structure
    return APIContractValidatorResult(
        schema_validation=SchemaValidationResult(
            valid=True,
            errors=[],
            warnings=[]
        ),
        breaking_changes=BreakingChangeReport(
            baseline="v2.4.0",
            candidate="v2.5.0",
            timestamp=datetime.now(),
            breaking_changes=[
                BreakingChange(
                    type="REQUIRED_FIELD_REMOVED",
                    severity="CRITICAL",
                    endpoint="/api/users/{id}",
                    status=200,
                    field="username",
                    message="Required response field 'username' was removed",
                    impact={
                        "affected_consumers": 23,
                        "estimated_requests": "1.2M/day",
                        "migration_effort": "HIGH"
                    },
                    recommendation="Deprecate in v2.5.0, remove in v3.0.0"
                )
            ],
            non_breaking_changes=[
                NonBreakingChange(
                    type="FIELD_ADDED",
                    endpoint="/api/users/{id}",
                    status=200,
                    field="profilePicture",
                    message="Response field 'profilePicture' was added",
                    impact="None - backward compatible addition"
                )
            ],
            summary={
                "total_breaking": 1,
                "total_non_breaking": 1,
                "recommendation": "BLOCK DEPLOYMENT - Breaking changes detected",
                "suggested_version": "v3.0.0",
                "estimated_migration_time": "2-3 weeks",
                "affected_consumers": 23
            }
        ),
        version_compatibility=VersionBump(
            valid=False,
            current_version="2.4.0",
            proposed_version="2.5.0",
            required_bump="MAJOR",
            actual_bump="MINOR",
            recommendation="Breaking changes require major version bump to v3.0.0",
            violations=[
                {
                    "severity": "CRITICAL",
                    "message": "Breaking changes require major version bump",
                    "expected": "v3.0.0",
                    "actual": "v2.5.0"
                }
            ]
        ),
        recommendation="BLOCK DEPLOYMENT - Breaking changes detected. Require major version bump to v3.0.0 and consumer coordination."
    )
