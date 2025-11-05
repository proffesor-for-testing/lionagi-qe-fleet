"""
QE Test Data Architect Agent

Mission: Generates realistic, schema-aware test data with relationship preservation
and edge case coverage, eliminating manual test data creation.

Capabilities:
- Schema-aware generation from SQL, GraphQL, TypeScript, JSON Schema
- Relationship preservation maintaining referential integrity
- Edge case data covering boundary values and special cases
- Data anonymization for GDPR/HIPAA compliance
- Realistic data synthesis matching production patterns
- Constraint validation (NOT NULL, UNIQUE, CHECK, FK)
- Data versioning aligned with schema versions
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime


# ============================================================================
# Pydantic Result Models
# ============================================================================

class FieldSchema(BaseModel):
    """Schema definition for a field"""
    name: str
    type: str
    nullable: bool = False
    default_value: Optional[Any] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    format: Optional[str] = None
    generator: str


class EntitySchema(BaseModel):
    """Schema definition for an entity"""
    name: str
    fields: List[FieldSchema]
    primary_key: str
    unique_constraints: List[str] = Field(default_factory=list)
    check_constraints: List[Dict[str, str]] = Field(default_factory=list)


class Relationship(BaseModel):
    """Relationship between entities"""
    from_entity: str
    to_entity: str
    from_field: str
    to_field: str
    relationship_type: Literal["one-to-one", "one-to-many", "many-to-many"]


class SchemaAnalysis(BaseModel):
    """Complete schema analysis result"""
    entities: List[EntitySchema]
    relationships: List[Relationship]
    constraints: Dict[str, List[str]]
    indexes: Dict[str, List[str]]


class GeneratedRecord(BaseModel):
    """A single generated data record"""
    entity: str
    data: Dict[str, Any]


class GeneratedDataset(BaseModel):
    """Complete generated dataset"""
    schema_version: str
    generation_timestamp: datetime
    total_records: int
    records_by_entity: Dict[str, int]
    data: Dict[str, List[Dict[str, Any]]]


class EdgeCase(BaseModel):
    """Edge case test data"""
    field: str
    value: Any
    category: Literal[
        "empty", "minimum", "maximum", "special_chars",
        "unicode", "sql_injection", "xss", "boundary"
    ]
    description: str


class EdgeCaseDataset(BaseModel):
    """Dataset of edge cases"""
    entity: str
    edge_cases: List[EdgeCase]
    coverage: float  # Percentage of edge cases covered


class AnonymizationStrategy(BaseModel):
    """Strategy for anonymizing a field"""
    field: str
    strategy: Literal[
        "email", "name", "phone", "address", "partial_mask",
        "hash", "tokenize", "generalize"
    ]
    preserve_format: bool = True


class AnonymizationResult(BaseModel):
    """Result of data anonymization"""
    original_record_count: int
    anonymized_record_count: int
    strategies_applied: List[AnonymizationStrategy]
    statistical_properties_preserved: bool
    compliance_standard: Literal["GDPR", "HIPAA", "CCPA"]


class ConstraintViolation(BaseModel):
    """A constraint violation found during validation"""
    type: Literal["NOT_NULL", "UNIQUE", "CHECK", "FOREIGN_KEY"]
    entity: str
    field: Optional[str] = None
    record: Dict[str, Any]
    message: str


class ConstraintValidationResult(BaseModel):
    """Result of constraint validation"""
    valid: bool
    total_records: int
    violations: List[ConstraintViolation]
    violations_by_type: Dict[str, int]


class DataVersion(BaseModel):
    """Versioned test data"""
    id: str
    schema_version: str
    app_version: str
    timestamp: datetime
    checksum: str
    tags: List[str] = Field(default_factory=list)
    description: str
    record_count: int


class TestDataArchitectResult(BaseModel):
    """Complete test data architect result"""
    schema_analysis: SchemaAnalysis
    generated_dataset: GeneratedDataset
    edge_case_coverage: Optional[EdgeCaseDataset] = None
    anonymization: Optional[AnonymizationResult] = None
    constraint_validation: ConstraintValidationResult
    data_version: DataVersion
    statistics: Dict[str, Any]


# ============================================================================
# System Prompt
# ============================================================================

TEST_DATA_ARCHITECT_PROMPT = """You are the QE Test Data Architect, an expert at generating realistic, schema-aware test data that eliminates manual test data creation.

## Your Mission

**Eliminate manual test data creation** by generating realistic, schema-aware test data that preserves relationships, satisfies constraints, and covers edge cases. Using schema analysis, production data patterns, and intelligent faker libraries, create comprehensive test datasets in seconds instead of hours.

## Core Capabilities

### 1. Schema-Aware Generation
- Parse schemas from multiple sources: SQL DDL, GraphQL, TypeScript, JSON Schema
- Detect semantic types from field names (email, phone, URL, etc.)
- Select appropriate generators for each field type
- Respect field constraints (length, format, range)
- Generate data matching expected structures perfectly

### 2. Relationship Preservation
- Build relationship graphs from foreign keys
- Perform topological sort for generation order
- Ensure referential integrity (all FKs valid)
- Maintain cardinality constraints (1-to-1, 1-to-many, many-to-many)
- Handle complex multi-table relationships

### 3. Edge Case Coverage
- Generate boundary values (min, max, midpoint)
- Include special characters and unicode
- Test security scenarios (SQL injection, XSS)
- Cover empty/null cases where allowed
- Generate invalid data for negative testing

### 4. Data Anonymization
- Anonymize PII for GDPR/HIPAA compliance
- Preserve statistical properties (mean, distribution)
- Maintain relationships between anonymized records
- Support multiple strategies: masking, hashing, tokenization
- Ensure deterministic anonymization (same input → same output)

### 5. Realistic Data Synthesis
- Analyze production data patterns
- Match statistical distributions (normal, log-normal, etc.)
- Preserve correlations between fields
- Generate time-series data with seasonality
- Create realistic business scenarios

### 6. Constraint Validation
- Validate NOT NULL constraints
- Check UNIQUE constraints (no duplicates)
- Verify CHECK constraints (custom rules)
- Validate FOREIGN KEY constraints (referential integrity)
- Provide detailed violation reports

### 7. Data Versioning
- Version datasets aligned with schema versions
- Tag datasets by purpose (seed, test, load-test)
- Calculate checksums for data integrity
- Support rollback to previous versions
- Track generation metadata

## Data Generation Patterns

### Semantic Field Detection
Detect semantic meaning from field names:
- `email` → faker.internet.email()
- `phone` → faker.phone.number()
- `name` → faker.person.fullName()
- `address` → faker.location.streetAddress()
- `price` → faker.commerce.price()
- `date_of_birth` → faker.date.birthdate()
- `uuid` → faker.string.uuid()
- `url` → faker.internet.url()

### Edge Case Categories
Generate edge cases for:
1. **Strings**: empty, single char, max length, special chars, unicode, emojis
2. **Numbers**: 0, min, max, negative, decimal precision, infinity, NaN
3. **Dates**: epoch, leap year, far future, invalid dates
4. **Emails**: valid formats, invalid formats, edge cases
5. **Phones**: various formats, international, too short/long
6. **URLs**: valid schemes, malformed, special protocols

### Anonymization Strategies
Apply appropriate strategy per field type:
- **Email**: Anonymize local part, preserve domain
- **Name**: Replace with fake name
- **Phone**: Generate fake phone number
- **SSN**: Generate fake SSN with correct format
- **Address**: Replace with fake address
- **Partial Mask**: Show first/last char, mask middle
- **Hash**: Deterministic SHA-256 hash
- **Tokenize**: Consistent token replacement
- **Generalize**: Round/bucket values (age → age range)

## Output Requirements

Generate datasets that are:
1. **Schema-compliant**: Match all field types and constraints
2. **Referentially intact**: All foreign keys valid
3. **Edge-case rich**: Include boundary and special cases
4. **Privacy-compliant**: No PII exposure
5. **Realistic**: Match production patterns and distributions
6. **Versioned**: Traceable and reproducible

## Performance Targets

Achieve:
- **10,000+ records/second** generation speed
- **100% constraint compliance** (all validations pass)
- **95%+ edge case coverage**
- **100% referential integrity** (no orphaned records)

## Example Use Cases

### 1. Database Seed Data
Generate 1,000 users with orders and order items:
- Users: 1,000 records
- Orders: 3,000 records (avg 3 per user)
- Order Items: 9,000 records (avg 3 per order)
- All foreign keys valid, realistic amounts and quantities

### 2. API Contract Testing
Generate test data matching OpenAPI schema:
- Request bodies with all required fields
- Edge cases for validation testing
- Invalid data for error handling tests

### 3. Production Data Anonymization
Anonymize 100,000 production records:
- Remove all PII (email, name, phone, address)
- Preserve statistical properties (order amounts, quantities)
- Maintain referential integrity
- GDPR/HIPAA compliant

Focus on eliminating manual data creation and ensuring data quality through automation."""


# ============================================================================
# Agent Implementation
# ============================================================================

from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


class TestDataArchitectAgent(BaseQEAgent):
    """Test Data Architect Agent

    Generates realistic, schema-aware test data with relationship preservation
    and edge case coverage, eliminating manual test data creation.

    Capabilities:
    - Schema-aware generation from SQL, GraphQL, TypeScript, JSON Schema
    - Relationship preservation maintaining referential integrity
    - Edge case data covering boundary values and special cases
    - Data anonymization for GDPR/HIPAA compliance
    - Realistic data synthesis matching production patterns
    - Constraint validation (NOT NULL, UNIQUE, CHECK, FK)
    - Data versioning aligned with schema versions
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
        """Initialize TestDataArchitect Agent

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
            skills=skills or ['agentic-quality-engineering', 'test-data-management', 'test-design-techniques'],
            enable_learning=enable_learning,
            q_learning_service=q_learning_service,
            memory_config=memory_config
        )

    def get_system_prompt(self) -> str:
        """Define agent expertise"""
        return TEST_DATA_ARCHITECT_PROMPT

    async def execute(self, task: QETask) -> TestDataArchitectResult:
        """Execute test data generation from schema

        Args:
            task: Task containing:
                - schema_source: Schema definition (SQL DDL, GraphQL, JSON Schema)
                - record_count: Number of records to generate per entity (default: 100)
                - include_edge_cases: Whether to include edge case data (default: True)
                - anonymize: Whether to anonymize generated data (default: False)
                - schema_version: Schema version for data versioning (optional)
                - compliance_standard: GDPR/HIPAA/CCPA (optional)

        Returns:
            TestDataArchitectResult with generated datasets
        """
        # Extract context
        context = task.context
        schema_source = context.get("schema_source", "")
        record_count = context.get("record_count", 100)
        include_edge_cases = context.get("include_edge_cases", True)
        anonymize = context.get("anonymize", False)
        schema_version = context.get("schema_version", "1.0.0")
        compliance_standard = context.get("compliance_standard", "GDPR")

        # Retrieve schema history from memory
        schema_history = await self.get_memory(
            "aqe/test-data/schema-history",
            default=[]
        )

        # Retrieve previously generated data patterns
        data_patterns = await self.get_memory(
            "aqe/test-data/patterns",
            default={}
        )

        # Use LionAGI to perform test data generation
        result = await self.operate(
            instruction=f"""Generate realistic, schema-aware test data with comprehensive validation.

            Schema Source:
            ```
            {schema_source}
            ```

            Configuration:
            - Record Count: {record_count} per entity
            - Include Edge Cases: {include_edge_cases}
            - Anonymize: {anonymize}
            - Schema Version: {schema_version}
            - Compliance Standard: {compliance_standard}

            Requirements:
            1. Parse schema and extract entities, fields, relationships
            2. Generate realistic data matching field semantics (email, phone, name, etc.)
            3. Preserve referential integrity (all foreign keys valid)
            4. Include edge cases (empty, min, max, special chars, unicode)
            5. Validate all constraints (NOT NULL, UNIQUE, CHECK, FK)
            6. Apply anonymization strategies if requested
            7. Version the dataset with checksum
            8. Report generation statistics (records/sec, compliance rate)

            Data Patterns (for realistic synthesis):
            {str(data_patterns)[:500] if data_patterns else "No patterns available"}

            Schema History (for relationship inference):
            {schema_history[:3] if schema_history else "No history available"}

            Performance Targets:
            - 10,000+ records/second generation speed
            - 100% constraint compliance
            - 95%+ edge case coverage
            - 100% referential integrity
            """,
            response_format=TestDataArchitectResult,
        )

        # Store generated dataset in memory
        await self.store_memory(
            f"aqe/test-data/datasets/{schema_version}",
            result.model_dump(),
        )

        # Update schema history
        schema_history.append({
            "schema_version": schema_version,
            "timestamp": datetime.now().isoformat(),
            "entity_count": len(result.schema_analysis.entities),
            "total_records": result.generated_dataset.total_records,
        })
        await self.store_memory(
            "aqe/test-data/schema-history",
            schema_history[-20:],  # Keep last 20 schema versions
        )

        # Store data patterns for future synthesis
        for entity in result.schema_analysis.entities:
            if entity.name not in data_patterns:
                data_patterns[entity.name] = {
                    "fields": [f.name for f in entity.fields],
                    "generators": [f.generator for f in entity.fields],
                    "generation_count": 1,
                }
            else:
                data_patterns[entity.name]["generation_count"] += 1

        await self.store_memory(
            "aqe/test-data/patterns",
            data_patterns,
        )

        return result


# ============================================================================
# Placeholder Function (For Backward Compatibility)
# ============================================================================

def execute(
    schema_source: str,
    record_count: int = 100,
    include_edge_cases: bool = True,
    anonymize: bool = False
) -> TestDataArchitectResult:
    """
    Execute test data generation from schema.

    Args:
        schema_source: Schema definition (SQL DDL, GraphQL, JSON Schema)
        record_count: Number of records to generate per entity
        include_edge_cases: Whether to include edge case data
        anonymize: Whether to anonymize generated data

    Returns:
        TestDataArchitectResult with generated datasets

    Note:
        This is a placeholder implementation. In production, this would:
        1. Parse schema from various formats
        2. Build relationship graph
        3. Generate data respecting constraints
        4. Include edge cases
        5. Anonymize if requested
        6. Validate all constraints
        7. Version the dataset
    """
    # Placeholder implementation
    # In production, integrate with:
    # - Schema parsers (sql-parse, graphql-js, ajv)
    # - Faker libraries (@faker-js/faker)
    # - Database clients for seeding
    # - Anonymization libraries

    # Example result structure
    return TestDataArchitectResult(
        schema_analysis=SchemaAnalysis(
            entities=[
                EntitySchema(
                    name="users",
                    fields=[
                        FieldSchema(
                            name="id",
                            type="uuid",
                            nullable=False,
                            generator="uuid"
                        ),
                        FieldSchema(
                            name="email",
                            type="string",
                            nullable=False,
                            format="email",
                            generator="email"
                        ),
                        FieldSchema(
                            name="name",
                            type="string",
                            nullable=False,
                            generator="name"
                        )
                    ],
                    primary_key="id",
                    unique_constraints=["email"]
                )
            ],
            relationships=[],
            constraints={"users": ["email UNIQUE", "id NOT NULL"]},
            indexes={"users": ["email"]}
        ),
        generated_dataset=GeneratedDataset(
            schema_version="1.0.0",
            generation_timestamp=datetime.now(),
            total_records=record_count,
            records_by_entity={"users": record_count},
            data={
                "users": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "alice@example.com",
                        "name": "Alice Johnson"
                    }
                ] * record_count
            }
        ),
        constraint_validation=ConstraintValidationResult(
            valid=True,
            total_records=record_count,
            violations=[],
            violations_by_type={}
        ),
        data_version=DataVersion(
            id="test-data-v1.0.0",
            schema_version="1.0.0",
            app_version="2.5.0",
            timestamp=datetime.now(),
            checksum="abc123def456",
            tags=["seed", "development"],
            description="Initial seed data for development",
            record_count=record_count
        ),
        statistics={
            "generation_time_ms": 1234,
            "records_per_second": 10000,
            "constraint_compliance_rate": 1.0,
            "edge_case_coverage": 0.95 if include_edge_cases else 0.0
        }
    )
