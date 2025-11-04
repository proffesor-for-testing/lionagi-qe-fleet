"""Unit tests for APIContractValidatorAgent - API contract validation and breaking change detection"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from hypothesis import given, strategies as st
from lionagi_qe.agents.api_contract_validator import (
    APIContractValidatorAgent,
    ValidationError,
    SchemaValidationResult,
    BreakingChange,
    NonBreakingChange,
    BreakingChangeReport,
    VersionBump,
    AffectedEndpoint,
    ConsumerImpact,
    ConsumerImpactAnalysis,
    ContractDiff,
    APIContractValidatorResult,
)
from lionagi_qe.core.task import QETask


class TestAPIContractValidatorAgent:
    """Test suite for APIContractValidatorAgent"""

    @pytest.fixture
    async def agent(self, qe_memory, simple_model):
        """Create API contract validator agent"""
        return APIContractValidatorAgent(
            agent_id="api-contract-validator",
            model=simple_model,
            memory=qe_memory,
            skills=["agentic-quality-engineering", "api-testing-patterns"],
            enable_learning=False,
        )

    @pytest.fixture
    def baseline_openapi_schema(self):
        """Sample baseline OpenAPI schema"""
        return {
            "openapi": "3.0.0",
            "info": {"title": "User API", "version": "2.4.0"},
            "paths": {
                "/api/users/{id}": {
                    "get": {
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "User details",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["id", "username", "email"],
                                            "properties": {
                                                "id": {"type": "string"},
                                                "username": {"type": "string"},
                                                "email": {"type": "string"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }

    @pytest.fixture
    def candidate_openapi_schema_breaking(self):
        """Sample candidate schema with breaking changes"""
        return {
            "openapi": "3.0.0",
            "info": {"title": "User API", "version": "2.5.0"},
            "paths": {
                "/api/users/{id}": {
                    "get": {
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {
                            "200": {
                                "description": "User details",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["id", "email"],  # username removed
                                            "properties": {
                                                "id": {"type": "string"},
                                                "email": {"type": "string"},
                                                "profilePicture": {"type": "string"},  # new field
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }

    @pytest.fixture
    def sample_consumers(self):
        """Sample consumer data"""
        return [
            {
                "consumer": "mobile-app",
                "team": "Mobile Engineering",
                "contact": "mobile@example.com",
                "endpoints": {
                    "/api/users/{id}": {
                        "method": "GET",
                        "requests_per_day": 500000
                    }
                },
            },
            {
                "consumer": "web-app",
                "team": "Web Engineering",
                "contact": "web@example.com",
                "endpoints": {
                    "/api/users/{id}": {
                        "method": "GET",
                        "requests_per_day": 700000
                    }
                },
            },
        ]

    # ==================== Initialization Tests ====================

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.agent_id == "api-contract-validator"
        assert agent.skills == ["agentic-quality-engineering", "api-testing-patterns"]
        assert agent.enable_learning is False
        assert agent.branch is not None

    @pytest.mark.asyncio
    async def test_system_prompt(self, agent):
        """Test system prompt is properly defined"""
        prompt = agent.get_system_prompt()
        assert "API Contract Validator" in prompt
        assert "breaking API changes" in prompt
        assert "backward compatibility" in prompt
        assert "OpenAPI" in prompt or "GraphQL" in prompt
        assert "semantic versioning" in prompt

    # ==================== Schema Validation Tests ====================

    @pytest.mark.asyncio
    async def test_schema_validation_success(self, agent, baseline_openapi_schema, mocker):
        """Test successful schema validation"""
        task = QETask(
            task_type="validate_schema",
            context={
                "baseline_schema": baseline_openapi_schema,
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(
                valid=True,
                errors=[],
                warnings=[],
            ),
            recommendation="Schema is valid",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.schema_validation.valid is True
        assert len(result.schema_validation.errors) == 0
        assert result.recommendation is not None

    @pytest.mark.asyncio
    async def test_schema_validation_with_errors(self, agent, mocker):
        """Test schema validation with errors"""
        invalid_schema = {
            "openapi": "3.0.0",
            "paths": {
                "/api/users": {
                    "get": {
                        "responses": {}  # Missing required response
                    }
                }
            },
        }

        task = QETask(
            task_type="validate_schema",
            context={"baseline_schema": invalid_schema},
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        type="missing_response",
                        path="/api/users.get.responses",
                        message="At least one response must be defined",
                    )
                ],
                warnings=[],
            ),
            recommendation="Fix schema errors before deployment",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.schema_validation.valid is False
        assert len(result.schema_validation.errors) > 0

    # ==================== Breaking Change Detection Tests ====================

    @pytest.mark.asyncio
    async def test_breaking_change_detection(
        self, agent, baseline_openapi_schema, candidate_openapi_schema_breaking, mocker
    ):
        """Test detection of breaking changes"""
        task = QETask(
            task_type="detect_breaking_changes",
            context={
                "baseline_schema": baseline_openapi_schema,
                "candidate_schema": candidate_openapi_schema_breaking,
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
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
                            "affected_consumers": 2,
                            "estimated_requests": "1.2M/day",
                        },
                        recommendation="Deprecate in v2.5.0, remove in v3.0.0",
                    )
                ],
                non_breaking_changes=[
                    NonBreakingChange(
                        type="FIELD_ADDED",
                        endpoint="/api/users/{id}",
                        status=200,
                        field="profilePicture",
                        message="Response field 'profilePicture' was added",
                        impact="None - backward compatible",
                    )
                ],
                summary={
                    "total_breaking": 1,
                    "total_non_breaking": 1,
                    "recommendation": "BLOCK DEPLOYMENT",
                },
            ),
            recommendation="BLOCK DEPLOYMENT - Breaking changes detected",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.breaking_changes is not None
        assert len(result.breaking_changes.breaking_changes) > 0
        assert result.breaking_changes.breaking_changes[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_non_breaking_changes_only(self, agent, mocker):
        """Test detection of non-breaking changes only"""
        baseline = {
            "paths": {
                "/api/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {"id": {"type": "string"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        candidate = {
            "paths": {
                "/api/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "id": {"type": "string"},
                                                "name": {"type": "string"},  # New optional field
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        task = QETask(
            task_type="detect_changes",
            context={"baseline_schema": baseline, "candidate_schema": candidate},
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            breaking_changes=BreakingChangeReport(
                baseline="v1.0.0",
                candidate="v1.1.0",
                timestamp=datetime.now(),
                breaking_changes=[],
                non_breaking_changes=[
                    NonBreakingChange(
                        type="FIELD_ADDED",
                        endpoint="/api/users",
                        field="name",
                        message="New optional field added",
                        impact="None - backward compatible",
                    )
                ],
                summary={"total_breaking": 0, "total_non_breaking": 1},
            ),
            recommendation="ALLOW DEPLOYMENT - Only non-breaking changes",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.breaking_changes is not None
        assert len(result.breaking_changes.breaking_changes) == 0
        assert len(result.breaking_changes.non_breaking_changes) > 0

    # ==================== Semantic Versioning Tests ====================

    @pytest.mark.asyncio
    async def test_semver_validation_major_bump_required(self, agent, mocker):
        """Test semantic versioning validation requiring major bump"""
        task = QETask(
            task_type="validate_version",
            context={
                "current_version": "2.4.0",
                "proposed_version": "2.5.0",
                "has_breaking_changes": True,
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
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
                        "actual": "v2.5.0",
                    }
                ],
            ),
            recommendation="Version bump insufficient for breaking changes",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.version_compatibility is not None
        assert result.version_compatibility.valid is False
        assert result.version_compatibility.required_bump == "MAJOR"
        assert result.version_compatibility.actual_bump == "MINOR"

    @pytest.mark.asyncio
    async def test_semver_validation_minor_bump_valid(self, agent, mocker):
        """Test semantic versioning validation for valid minor bump"""
        task = QETask(
            task_type="validate_version",
            context={
                "current_version": "2.4.0",
                "proposed_version": "2.5.0",
                "has_breaking_changes": False,
                "has_new_features": True,
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            version_compatibility=VersionBump(
                valid=True,
                current_version="2.4.0",
                proposed_version="2.5.0",
                required_bump="MINOR",
                actual_bump="MINOR",
                recommendation="Version bump is appropriate",
                violations=[],
            ),
            recommendation="Version bump is valid for non-breaking changes",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.version_compatibility is not None
        assert result.version_compatibility.valid is True
        assert result.version_compatibility.required_bump == "MINOR"

    # ==================== Consumer Impact Analysis Tests ====================

    @pytest.mark.asyncio
    async def test_consumer_impact_analysis(self, agent, sample_consumers, mocker):
        """Test consumer impact analysis"""
        task = QETask(
            task_type="analyze_consumer_impact",
            context={
                "consumers": sample_consumers,
                "breaking_changes": [
                    {
                        "endpoint": "/api/users/{id}",
                        "method": "GET",
                        "type": "REQUIRED_FIELD_REMOVED",
                        "field": "username",
                    }
                ],
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            consumer_impact=ConsumerImpactAnalysis(
                baseline="v2.4.0",
                candidate="v2.5.0",
                breaking_changes=1,
                affected_consumers=2,
                top_impacted_consumers=[
                    ConsumerImpact(
                        consumer="web-app",
                        team="Web Engineering",
                        contact="web@example.com",
                        affected_endpoints=[
                            AffectedEndpoint(
                                endpoint="/api/users/{id}",
                                method="GET",
                                requests_per_day=700000,
                                changes=[],
                                migration_effort="HIGH",
                            )
                        ],
                        total_requests=700000,
                        estimated_migration_time="2-3 weeks",
                        priority="CRITICAL",
                    ),
                    ConsumerImpact(
                        consumer="mobile-app",
                        team="Mobile Engineering",
                        contact="mobile@example.com",
                        affected_endpoints=[
                            AffectedEndpoint(
                                endpoint="/api/users/{id}",
                                method="GET",
                                requests_per_day=500000,
                                changes=[],
                                migration_effort="HIGH",
                            )
                        ],
                        total_requests=500000,
                        estimated_migration_time="2-3 weeks",
                        priority="HIGH",
                    ),
                ],
                recommendation={
                    "action": "COORDINATE_MIGRATION",
                    "priority": "CRITICAL",
                    "estimated_time": "2-3 weeks",
                },
            ),
            recommendation="Coordinate with 2 affected consumers before deployment",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.consumer_impact is not None
        assert result.consumer_impact.affected_consumers == 2
        assert len(result.consumer_impact.top_impacted_consumers) == 2

    # ==================== Contract Diff Tests ====================

    @pytest.mark.asyncio
    async def test_contract_diff_generation(self, agent, baseline_openapi_schema, candidate_openapi_schema_breaking, mocker):
        """Test contract diff generation"""
        task = QETask(
            task_type="generate_diff",
            context={
                "baseline_schema": baseline_openapi_schema,
                "candidate_schema": candidate_openapi_schema_breaking,
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            contract_diff=ContractDiff(
                baseline="v2.4.0",
                candidate="v2.5.0",
                breaking_changes_count=1,
                non_breaking_changes_count=1,
                recommended_version="v3.0.0",
                estimated_migration_time="2-3 weeks",
                affected_consumers=2,
                diff_visualization="- username (REMOVED)\n+ profilePicture (ADDED)",
            ),
            recommendation="Review diff before proceeding",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.contract_diff is not None
        assert result.contract_diff.breaking_changes_count > 0
        assert result.contract_diff.diff_visualization is not None

    # ==================== Memory Integration Tests ====================

    @pytest.mark.asyncio
    async def test_stores_validation_results_in_memory(self, agent, qe_memory, mocker):
        """Test validation results are stored in memory"""
        task = QETask(
            task_type="validate_contract",
            context={"baseline_schema": {"test": "schema"}},
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            recommendation="Contract is valid",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        # Verify results stored
        stored = await qe_memory.retrieve(
            f"aqe/api-contract-validator/tasks/{task.task_id}/result"
        )
        assert stored is not None

    @pytest.mark.asyncio
    async def test_retrieves_historical_validations(self, agent, qe_memory):
        """Test retrieval of historical validation data"""
        # Store historical validation
        await qe_memory.store(
            "aqe/api/contracts/history",
            {
                "v2.3.0": {"breaking_changes": 0, "timestamp": "2024-01-01"},
                "v2.4.0": {"breaking_changes": 1, "timestamp": "2024-02-01"},
            },
        )

        history = await agent.retrieve_context("aqe/api/contracts/history")
        assert history is not None
        assert "v2.4.0" in history

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_handles_invalid_schema_format(self, agent, mocker):
        """Test handling of invalid schema format"""
        task = QETask(
            task_type="validate_schema",
            context={"baseline_schema": "invalid_string_not_dict"},
        )

        mocker.patch.object(
            agent,
            "operate",
            side_effect=Exception("Invalid schema format"),
        )

        with pytest.raises(Exception) as exc_info:
            await agent.execute(task)

        assert "Invalid schema format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handles_missing_baseline_schema(self, agent, mocker):
        """Test handling of missing baseline schema"""
        task = QETask(
            task_type="detect_breaking_changes",
            context={"candidate_schema": {"test": "schema"}},
            # Missing baseline_schema
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(
                valid=False,
                errors=[
                    ValidationError(
                        type="missing_baseline",
                        message="Baseline schema is required for comparison",
                    )
                ],
            ),
            recommendation="Provide baseline schema",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.schema_validation.valid is False

    # ==================== Property-Based Tests ====================

    @given(
        st.text(min_size=1, max_size=20),
        st.integers(min_value=0, max_value=3),
        st.integers(min_value=0, max_value=10),
    )
    def test_version_format_validation(self, major, minor, patch):
        """Property-based test for version format validation"""
        version = f"{major}.{minor}.{patch}"
        # Version should match semver pattern
        import re

        assert re.match(r"^\d+\.\d+\.\d+$", version)

    @given(st.lists(st.text(min_size=1), min_size=0, max_size=10))
    def test_consumer_list_handling(self, consumer_names):
        """Property-based test for consumer list handling"""
        # Should handle any list of consumer names
        consumers = [{"consumer": name, "team": "Team", "contact": "test@example.com"} for name in consumer_names]
        assert len(consumers) == len(consumer_names)

    # ==================== Integration Tests ====================

    @pytest.mark.asyncio
    async def test_full_validation_workflow(
        self,
        agent,
        baseline_openapi_schema,
        candidate_openapi_schema_breaking,
        sample_consumers,
        mocker,
    ):
        """Test complete validation workflow"""
        task = QETask(
            task_type="full_validation",
            context={
                "baseline_schema": baseline_openapi_schema,
                "candidate_schema": candidate_openapi_schema_breaking,
                "consumers": sample_consumers,
                "current_version": "2.4.0",
                "proposed_version": "2.5.0",
            },
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            breaking_changes=BreakingChangeReport(
                baseline="v2.4.0",
                candidate="v2.5.0",
                timestamp=datetime.now(),
                breaking_changes=[
                    BreakingChange(
                        type="REQUIRED_FIELD_REMOVED",
                        severity="CRITICAL",
                        endpoint="/api/users/{id}",
                        field="username",
                        message="Required field removed",
                        recommendation="Revert change or bump to v3.0.0",
                    )
                ],
                non_breaking_changes=[],
                summary={"total_breaking": 1},
            ),
            version_compatibility=VersionBump(
                valid=False,
                current_version="2.4.0",
                proposed_version="2.5.0",
                required_bump="MAJOR",
                actual_bump="MINOR",
                recommendation="Bump to v3.0.0",
            ),
            consumer_impact=ConsumerImpactAnalysis(
                baseline="v2.4.0",
                candidate="v2.5.0",
                breaking_changes=1,
                affected_consumers=2,
                top_impacted_consumers=[],
                recommendation={"action": "COORDINATE"},
            ),
            recommendation="BLOCK DEPLOYMENT - Breaking changes require major version bump",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        result = await agent.execute(task)

        assert result.schema_validation.valid is True
        assert result.breaking_changes is not None
        assert result.version_compatibility is not None
        assert result.consumer_impact is not None
        assert "BLOCK" in result.recommendation

    @pytest.mark.asyncio
    async def test_concurrent_validations(self, agent, mocker):
        """Test concurrent validation operations"""
        import asyncio

        tasks = [
            QETask(
                task_type="validate_schema",
                context={"baseline_schema": {"paths": {}}},
            )
            for _ in range(3)
        ]

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            recommendation="Valid",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        results = await asyncio.gather(*[agent.execute(task) for task in tasks])

        assert len(results) == 3
        assert all(r.schema_validation.valid for r in results)

    # ==================== Metrics Tests ====================

    @pytest.mark.asyncio
    async def test_agent_metrics_tracking(self, agent, mocker):
        """Test agent tracks metrics correctly"""
        task = QETask(
            task_type="validate_schema",
            context={"baseline_schema": {"test": "schema"}},
        )

        mock_result = APIContractValidatorResult(
            schema_validation=SchemaValidationResult(valid=True),
            recommendation="Valid",
        )

        mocker.patch.object(agent, "operate", new=AsyncMock(return_value=mock_result))

        initial_completed = agent.metrics["tasks_completed"]

        await agent.execute(task)

        metrics = await agent.get_metrics()
        assert metrics["tasks_completed"] == initial_completed + 1
