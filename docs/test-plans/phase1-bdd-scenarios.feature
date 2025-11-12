# Phase 1 CI/CD Integration - BDD Scenarios
# Project: LionAGI QE Fleet
# Phase: Phase 1 - Foundation (Weeks 1-8)
# Generated: 2025-11-12
# Status: Ready for Implementation

#==============================================================================
# MILESTONE 1.1: CLI ENHANCEMENTS (Weeks 1-2)
#==============================================================================

@milestone-1.1 @cli-enhancements @priority-high
Feature: CLI Enhancements for CI/CD Integration
  As a DevOps engineer
  I want CLI commands to work seamlessly in CI/CD pipelines
  So that I can automate quality engineering workflows without manual intervention

  Background:
    Given the AQE CLI is installed and available in PATH
    And the test project has source code in "src/" directory
    And the CLI version is v1.3.0 or higher

  #----------------------------------------------------------------------------
  # JSON Output Flag
  #----------------------------------------------------------------------------

  @json-output @smoke-test
  Scenario: CLI outputs valid JSON when --json flag is specified
    When I run "aqe generate src/ --json"
    Then the exit code should be 0
    And the output should be valid JSON
    And the JSON should contain the key "status"
    And the JSON should contain the key "coverage"
    And the JSON should contain the key "tests_generated"
    And the JSON should be parseable by jq

  @json-output @error-handling
  Scenario: CLI outputs JSON error format when command fails with --json
    Given the directory "nonexistent/" does not exist
    When I run "aqe generate nonexistent/ --json"
    Then the exit code should be 1
    And the output should be valid JSON
    And the JSON should contain the key "status" with value "error"
    And the JSON should contain the key "error_message"
    And the JSON should contain the key "error_code"

  @json-output @special-characters
  Scenario Outline: CLI properly escapes special characters in JSON output
    Given a test file with <special_content>
    When I run "aqe generate src/ --json"
    Then the JSON output should properly escape <special_content>
    And the JSON should remain valid

    Examples:
      | special_content         |
      | quotes "test"           |
      | newlines \n             |
      | unicode émojis 🚀       |
      | backslashes \\          |
      | null bytes              |

  #----------------------------------------------------------------------------
  # Quiet Mode Flag
  #----------------------------------------------------------------------------

  @quiet-mode @smoke-test
  Scenario: CLI produces minimal output with --quiet flag
    When I run "aqe generate src/ --quiet"
    Then the exit code should be 0
    And the stdout should contain at most 10 lines
    And the stdout should contain a status line
    And the stdout should not contain debug messages
    And the stdout should not contain progress indicators

  @quiet-mode @error-handling
  Scenario: CLI shows error message even in quiet mode
    Given the directory "nonexistent/" does not exist
    When I run "aqe generate nonexistent/ --quiet"
    Then the exit code should be 1
    And the stderr should contain exactly 1 line
    And the stderr should contain the error message
    And the stderr should not contain stack traces

  @quiet-mode @warnings
  Scenario: CLI shows warnings in quiet mode but not verbose info
    Given the source code has deprecated API usage
    When I run "aqe generate src/ --quiet"
    Then the exit code should be 2
    And the stdout should contain warning count
    And the stdout should not contain individual warning details
    And the stdout should suggest using verbose mode for details

  #----------------------------------------------------------------------------
  # Non-Interactive Flag
  #----------------------------------------------------------------------------

  @non-interactive @smoke-test
  Scenario: CLI never prompts for input with --non-interactive flag
    Given the CLI would normally prompt for confirmation
    When I run "aqe generate src/ --non-interactive --force"
    Then the exit code should be 0
    And the command should complete without waiting for input
    And no interactive prompts should be displayed

  @non-interactive @defaults
  Scenario: CLI uses sensible defaults in non-interactive mode
    Given the configuration file is missing
    When I run "aqe generate src/ --non-interactive"
    Then the CLI should use default framework "jest"
    And the CLI should use default coverage threshold 80%
    And the CLI should not ask for framework selection

  @non-interactive @errors
  Scenario: CLI fails fast in non-interactive mode when required input is missing
    Given the API key is not configured
    And the API key is required for the operation
    When I run "aqe security-scan src/ --non-interactive"
    Then the exit code should be 1
    And the error message should indicate missing API key
    And the error message should suggest how to configure it
    And the command should not hang waiting for input

  #----------------------------------------------------------------------------
  # CI Mode Flag
  #----------------------------------------------------------------------------

  @ci-mode @smoke-test
  Scenario: CLI enables all CI optimizations with --ci-mode flag
    When I run "aqe generate src/ --ci-mode"
    Then the JSON output should be enabled
    And the quiet mode should be enabled
    And the non-interactive mode should be enabled
    And the color output should be disabled
    And the progress bars should be disabled
    And the output should be line-buffered (not block-buffered)

  @ci-mode @github-actions
  Scenario: CLI detects GitHub Actions environment and auto-enables CI mode
    Given the environment variable "GITHUB_ACTIONS" is set to "true"
    When I run "aqe generate src/"
    Then the CLI should automatically enable CI mode
    And the output should be compatible with GitHub Actions
    And the annotations should be in GitHub format

  @ci-mode @gitlab-ci
  Scenario: CLI detects GitLab CI environment and auto-enables CI mode
    Given the environment variable "GITLAB_CI" is set to "true"
    When I run "aqe generate src/"
    Then the CLI should automatically enable CI mode
    And the output should be compatible with GitLab CI
    And the coverage report should be in GitLab format

  #----------------------------------------------------------------------------
  # Exit Codes
  #----------------------------------------------------------------------------

  @exit-codes @smoke-test
  Scenario: CLI returns exit code 0 when all tests pass
    Given the test suite has passing tests
    When I run "aqe execute tests/"
    Then the exit code should be 0
    And the output should indicate success

  @exit-codes @smoke-test
  Scenario: CLI returns exit code 1 when tests fail
    Given the test suite has failing tests
    When I run "aqe execute tests/"
    Then the exit code should be 1
    And the output should indicate failure
    And the output should list failed tests

  @exit-codes @smoke-test
  Scenario: CLI returns exit code 2 when warnings are present but no failures
    Given the source code has linting warnings
    And the tests all pass
    When I run "aqe quality-gate --threshold 80"
    Then the exit code should be 2
    And the output should indicate warnings

  @exit-codes @edge-cases
  Scenario: CLI returns exit code 2 when no tests are found
    Given the tests directory is empty
    When I run "aqe execute tests/"
    Then the exit code should be 2
    And the output should indicate "no tests found"
    And the output should suggest where to add tests

  @exit-codes @unhandled-exception
  Scenario: CLI returns exit code 1 for unhandled exceptions
    Given an unhandled exception occurs during execution
    When I run "aqe generate src/"
    Then the exit code should be 1
    And the stderr should contain error details
    And the error should be logged for debugging

  #----------------------------------------------------------------------------
  # Flag Combinations
  #----------------------------------------------------------------------------

  @flag-combinations
  Scenario: CLI combines --json and --quiet flags correctly
    When I run "aqe generate src/ --json --quiet"
    Then the stdout should contain only JSON output
    And the stderr should be empty (unless errors occur)
    And the JSON should be on a single line (no pretty-printing)

  @flag-combinations
  Scenario: CLI handles redundant flag combinations gracefully
    When I run "aqe generate src/ --ci-mode --json --quiet"
    Then the command should succeed without errors
    And the behavior should be equivalent to --ci-mode alone

  @flag-combinations @precedence
  Scenario: CLI respects flag precedence when conflicts occur
    When I run "aqe generate src/ --verbose --quiet"
    Then the last flag (--quiet) should take precedence
    And the output should be in quiet mode

  #----------------------------------------------------------------------------
  # Performance Requirements
  #----------------------------------------------------------------------------

  @performance @sla
  Scenario: CLI flag processing adds minimal overhead (<100ms)
    Given performance benchmarking is enabled
    When I run "aqe generate src/" 100 times
    And I run "aqe generate src/ --json --quiet --non-interactive" 100 times
    Then the average overhead should be less than 100ms
    And the p95 overhead should be less than 150ms
    And the p99 overhead should be less than 200ms

  @performance @concurrent
  Scenario: CLI handles concurrent invocations without degradation
    When I run 100 concurrent "aqe generate src/ --ci-mode" processes
    Then all processes should complete successfully
    And the average execution time should not increase by more than 20%
    And no processes should hang or deadlock

  #----------------------------------------------------------------------------
  # Documentation and Help
  #----------------------------------------------------------------------------

  @documentation @help-text
  Scenario: CLI help includes CI usage examples
    When I run "aqe generate --help"
    Then the help text should include a "CI Usage" section
    And the section should have examples for GitHub Actions
    And the section should have examples for GitLab CI
    And the section should have examples for Jenkins

  @documentation @man-page
  Scenario: CLI documentation is updated with new flags
    When I run "man aqe-generate" or "aqe generate --help"
    Then the documentation should describe --json flag
    And the documentation should describe --quiet flag
    And the documentation should describe --non-interactive flag
    And the documentation should describe --ci-mode flag
    And the documentation should describe exit codes

#==============================================================================
# MILESTONE 1.2: WEBHOOK API (Weeks 3-5)
#==============================================================================

@milestone-1.2 @webhook-api @priority-high
Feature: Webhook API for CI/CD Integration
  As a CI/CD system
  I want to trigger QE Fleet operations via REST API
  So that I can integrate with any CI/CD platform

  Background:
    Given the Webhook API server is running on localhost:8080
    And the API version is v1
    And the OpenAPI specification is available at /api/v1/openapi.json

  #----------------------------------------------------------------------------
  # API Authentication
  #----------------------------------------------------------------------------

  @authentication @api-keys @smoke-test
  Scenario: API accepts valid API key authentication
    Given I have a valid API key "aqe_test_1234567890abcdef1234567890abcdef"
    When I POST to "/api/v1/test/generate" with:
      """
      {
        "target": "src/",
        "framework": "jest"
      }
      """
    And I set header "Authorization: Bearer aqe_test_1234567890abcdef1234567890abcdef"
    Then the response status should be 202 Accepted
    And the response should contain a job ID
    And the response time should be less than 200ms (p95)

  @authentication @api-keys @negative
  Scenario: API rejects invalid API key
    Given I have an invalid API key "invalid_key"
    When I POST to "/api/v1/test/generate" with valid payload
    And I set header "Authorization: Bearer invalid_key"
    Then the response status should be 401 Unauthorized
    And the response should contain error details
    And the error message should be "Invalid API key"
    And the response should include WWW-Authenticate header

  @authentication @jwt @smoke-test
  Scenario: API accepts valid JWT token
    Given I have exchanged my API key for a JWT token
    And the JWT token is not expired
    When I POST to "/api/v1/test/generate" with:
      """
      {
        "target": "src/",
        "framework": "jest"
      }
      """
    And I set header "Authorization: Bearer {jwt_token}"
    Then the response status should be 202 Accepted

  @authentication @jwt @expiry
  Scenario: API rejects expired JWT token
    Given I have a JWT token that expired 1 hour ago
    When I POST to "/api/v1/test/generate" with valid payload
    And I set header "Authorization: Bearer {expired_jwt}"
    Then the response status should be 401 Unauthorized
    And the error message should indicate token expiration
    And the error should suggest refreshing the token

  @authentication @missing
  Scenario: API rejects requests without authentication
    When I POST to "/api/v1/test/generate" without Authorization header
    Then the response status should be 401 Unauthorized
    And the response should include WWW-Authenticate header
    And the error should suggest authentication methods

  #----------------------------------------------------------------------------
  # Rate Limiting
  #----------------------------------------------------------------------------

  @rate-limiting @smoke-test
  Scenario: API enforces rate limit of 100 requests per minute
    Given I have a valid API key
    When I make 100 requests to "/api/v1/test/generate" within 1 minute
    Then all 100 requests should succeed (status 202)
    When I make a 101st request within the same minute
    Then the response status should be 429 Too Many Requests
    And the response should include "Retry-After" header
    And the response should include "X-RateLimit-Limit: 100" header
    And the response should include "X-RateLimit-Remaining: 0" header

  @rate-limiting @sliding-window
  Scenario: API uses sliding window rate limiting
    Given I have a valid API key
    When I make 100 requests at time T
    And I wait 30 seconds
    And I make 50 requests at time T+30s
    Then the first 50 requests at T+30s should succeed
    When I wait another 30 seconds (T+60s)
    And I make 100 requests at time T+60s
    Then all 100 requests should succeed (rate limit reset)

  @rate-limiting @headers
  Scenario: API returns rate limit headers on all responses
    Given I have a valid API key
    When I make 5 requests to "/api/v1/test/generate"
    Then each response should include "X-RateLimit-Limit: 100"
    And each response should include "X-RateLimit-Remaining" (decreasing)
    And each response should include "X-RateLimit-Reset" (Unix timestamp)

  #----------------------------------------------------------------------------
  # API Endpoints
  #----------------------------------------------------------------------------

  @endpoints @test-generation @smoke-test
  Scenario: API generates tests via POST /api/v1/test/generate
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with:
      """
      {
        "target": "src/user-service.py",
        "framework": "pytest",
        "coverage_threshold": 90
      }
      """
    Then the response status should be 202 Accepted
    And the response should contain:
      """
      {
        "job_id": "{uuid}",
        "status": "queued",
        "created_at": "{iso8601_timestamp}"
      }
      """
    And the job should appear in the queue

  @endpoints @test-execution
  Scenario: API executes tests via POST /api/v1/test/execute
    Given I have a valid API key
    When I POST to "/api/v1/test/execute" with:
      """
      {
        "test_directory": "tests/",
        "parallel": true,
        "coverage": true
      }
      """
    Then the response status should be 202 Accepted
    And the response should contain a job ID
    And the job should be processed by Celery worker

  @endpoints @coverage-analysis
  Scenario: API analyzes coverage via POST /api/v1/coverage/analyze
    Given I have a valid API key
    When I POST to "/api/v1/coverage/analyze" with:
      """
      {
        "target": "src/",
        "coverage_file": ".coverage"
      }
      """
    Then the response status should be 202 Accepted
    And the response should contain a job ID

  @endpoints @quality-gate
  Scenario: API checks quality gate via POST /api/v1/quality/gate
    Given I have a valid API key
    When I POST to "/api/v1/quality/gate" with:
      """
      {
        "threshold": 80,
        "coverage_required": 85,
        "security_critical_max": 0
      }
      """
    Then the response status should be 200 OK
    And the response should contain:
      """
      {
        "passed": true,
        "coverage": 87.5,
        "quality_score": 92,
        "security_issues": 0
      }
      """

  @endpoints @job-status
  Scenario: API retrieves job status via GET /api/v1/job/{id}/status
    Given I have a job with ID "job-123"
    And I have a valid API key
    When I GET "/api/v1/job/job-123/status"
    Then the response status should be 200 OK
    And the response should contain:
      """
      {
        "job_id": "job-123",
        "status": "running",
        "progress": 65,
        "started_at": "{iso8601}",
        "estimated_completion": "{iso8601}"
      }
      """

  #----------------------------------------------------------------------------
  # WebSocket Streaming
  #----------------------------------------------------------------------------

  @websocket @streaming @smoke-test
  Scenario: API streams job progress via WebSocket
    Given I have a valid API key
    And I have started a job with ID "job-456"
    When I connect to WebSocket endpoint "ws://localhost:8080/api/v1/job/job-456/stream"
    And I send authentication message with API key
    Then I should receive a connection acknowledgment
    And I should receive progress updates in real-time:
      """
      {"type": "progress", "percent": 10, "message": "Analyzing code..."}
      {"type": "progress", "percent": 50, "message": "Generating tests..."}
      {"type": "progress", "percent": 100, "message": "Completed"}
      {"type": "result", "data": {...}}
      """
    And the WebSocket connection should close gracefully

  @websocket @timeout
  Scenario: API closes inactive WebSocket connections after 5 minutes
    Given I have a WebSocket connection to "/api/v1/job/job-789/stream"
    When I do not send any messages for 5 minutes
    Then the server should close the connection
    And the close reason should be "inactivity timeout"

  @websocket @backpressure
  Scenario: API handles slow WebSocket clients with backpressure
    Given I have a WebSocket connection
    And I do not read messages (simulate slow client)
    When the server sends 1000 messages
    Then the server should buffer up to 10MB
    And the server should disconnect the client if buffer exceeds 10MB
    And the server should not block other clients

  #----------------------------------------------------------------------------
  # Async Job Queue
  #----------------------------------------------------------------------------

  @job-queue @celery @smoke-test
  Scenario: API queues jobs with Celery and Redis
    Given Redis is running and accessible
    And Celery workers are running
    When I POST to "/api/v1/test/generate" with valid payload
    Then the job should be added to the Celery queue
    And the job should be picked up by a worker within 5 seconds
    And the job status should change from "queued" to "running"

  @job-queue @priority
  Scenario: API supports job priority levels
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with:
      """
      {
        "target": "src/",
        "priority": "critical"
      }
      """
    Then the job should be added to the high-priority queue
    And the job should be processed before normal priority jobs

  @job-queue @timeout
  Scenario: API cancels jobs that exceed 1-hour timeout
    Given I have a job running for 1 hour
    When the job timeout is reached
    Then the job should be cancelled
    And the job status should be "timeout"
    And the error message should indicate timeout

  @job-queue @retry
  Scenario: API retries failed jobs up to 3 times
    Given I have a job that fails intermittently
    When the job fails for the first time
    Then the job should be retried after exponential backoff
    And the retry count should be incremented
    When the job fails 3 times
    Then the job should be marked as "failed"
    And no further retries should be attempted

  #----------------------------------------------------------------------------
  # Input Validation
  #----------------------------------------------------------------------------

  @validation @empty-body
  Scenario: API rejects empty request body
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with empty body
    Then the response status should be 400 Bad Request
    And the error message should be "Request body is required"

  @validation @invalid-json
  Scenario: API rejects invalid JSON
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with:
      """
      {invalid json}
      """
    Then the response status should be 400 Bad Request
    And the error message should indicate JSON parse error
    And the error should show the location of the syntax error

  @validation @missing-required-field
  Scenario: API rejects request with missing required fields
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with:
      """
      {
        "framework": "jest"
      }
      """
    Then the response status should be 400 Bad Request
    And the error should list missing required field "target"
    And the error should use JSON Schema validation format

  @validation @payload-too-large
  Scenario: API rejects requests with body larger than 10MB
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with 11MB payload
    Then the response status should be 413 Payload Too Large
    And the error message should indicate maximum size

  @validation @injection-prevention
  Scenario Outline: API prevents injection attacks
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with:
      """
      {
        "target": "<malicious_input>"
      }
      """
    Then the response status should be 400 Bad Request
    And the malicious input should be sanitized
    And no command injection should occur

    Examples:
      | malicious_input                  |
      | "; rm -rf /"                     |
      | $(cat /etc/passwd)               |
      | `whoami`                         |
      | ' OR '1'='1                      |
      | <script>alert(1)</script>        |
      | ../../../etc/passwd              |

  #----------------------------------------------------------------------------
  # Error Handling
  #----------------------------------------------------------------------------

  @error-handling @format
  Scenario: API returns errors in RFC 7807 Problem Details format
    Given I have a valid API key
    When I POST to "/api/v1/test/generate" with invalid payload
    Then the response status should be 400 Bad Request
    And the response Content-Type should be "application/problem+json"
    And the response should contain:
      """
      {
        "type": "https://api.lionagi-qe.io/errors/validation-error",
        "title": "Validation Error",
        "status": 400,
        "detail": "The 'target' field is required",
        "instance": "/api/v1/test/generate"
      }
      """

  @error-handling @500-errors
  Scenario: API handles internal server errors gracefully
    Given the API encounters an internal error
    When I POST to "/api/v1/test/generate" with valid payload
    Then the response status should be 500 Internal Server Error
    And the error should not expose stack traces or sensitive data
    And the error should include a correlation ID for debugging
    And the error should be logged for investigation

  #----------------------------------------------------------------------------
  # Performance Requirements
  #----------------------------------------------------------------------------

  @performance @latency @sla
  Scenario: API responds within 200ms at p95
    Given I have a valid API key
    When I make 1000 requests to various endpoints
    Then the p50 response time should be less than 100ms
    And the p95 response time should be less than 200ms
    And the p99 response time should be less than 500ms

  @performance @throughput @sla
  Scenario: API handles 1000 concurrent requests
    Given I have a valid API key
    When I make 1000 concurrent requests to "/api/v1/test/generate"
    Then all requests should complete successfully
    And the average response time should be less than 300ms
    And no requests should timeout

  @performance @uptime @sla
  Scenario: API maintains 99.9% uptime
    Given the API has been running for 1 month
    When I check the uptime logs
    Then the uptime should be greater than 99.9%
    And the total downtime should be less than 43 minutes

#==============================================================================
# MILESTONE 1.3: ARTIFACT STORAGE (Weeks 5-6)
#==============================================================================

@milestone-1.3 @artifact-storage @priority-medium
Feature: Artifact Storage for Test Results and Reports
  As a QE system
  I want to persist test artifacts across runs
  So that I can track trends and provide historical analysis

  Background:
    Given the artifact storage system is initialized
    And the storage backend is configured

  #----------------------------------------------------------------------------
  # Storage Abstraction Layer
  #----------------------------------------------------------------------------

  @abstraction @smoke-test
  Scenario: Storage abstraction layer supports multiple backends
    Given the storage abstraction layer is initialized
    When I check supported backends
    Then the backends should include: ["local", "s3", "github-actions"]
    And each backend should implement store(), retrieve(), list(), delete()

  @abstraction @backend-switching
  Scenario: Storage backend can be switched at runtime
    Given I am using "local" storage backend
    And I have stored 10 artifacts
    When I switch to "s3" storage backend
    And I migrate artifacts from local to S3
    Then all 10 artifacts should be accessible in S3
    And the local artifacts should be deleted (optional)

  #----------------------------------------------------------------------------
  # Local Filesystem Storage
  #----------------------------------------------------------------------------

  @local-storage @smoke-test
  Scenario: Local storage saves artifacts to XDG directory
    Given I am using "local" storage backend
    When I store an artifact "test-results.json" with data:
      """
      {"tests": 42, "passed": 40, "failed": 2}
      """
    Then the artifact should be saved to "~/.local/share/aqe/artifacts/"
    And the file permissions should be 0600 (owner read/write only)
    And the parent directories should be created if not exist

  @local-storage @retrieval
  Scenario: Local storage retrieves artifacts correctly
    Given I have stored artifact "coverage-report.html"
    When I retrieve artifact "coverage-report.html"
    Then the content should match the original data exactly
    And the retrieval time should be less than 100ms

  @local-storage @disk-full
  Scenario: Local storage handles disk full gracefully
    Given the disk is full (or quota exceeded)
    When I attempt to store artifact "large-report.json"
    Then the operation should fail with error "Disk full"
    And the error message should suggest cleaning up old artifacts
    And no partial files should be left behind

  #----------------------------------------------------------------------------
  # S3-Compatible Storage
  #----------------------------------------------------------------------------

  @s3-storage @smoke-test
  Scenario: S3 storage saves artifacts to S3 bucket
    Given I am using "s3" storage backend
    And I have configured AWS credentials
    And I have an S3 bucket "aqe-artifacts"
    When I store an artifact "test-results.json"
    Then the artifact should be uploaded to S3 bucket
    And the S3 object key should be "artifacts/{job_id}/test-results.json"
    And the upload time should be less than 5 seconds (for 10MB)

  @s3-storage @multipart
  Scenario: S3 storage uses multipart upload for large files
    Given I am using "s3" storage backend
    When I store a 100MB artifact "large-report.html"
    Then the S3 client should use multipart upload
    And the upload should complete successfully
    And the upload time should be less than 30 seconds

  @s3-storage @retry
  Scenario: S3 storage retries failed uploads
    Given I am using "s3" storage backend
    And the network connection is unstable
    When I attempt to store artifact "test-results.json"
    And the first upload attempt fails
    Then the storage should retry with exponential backoff
    And the retry should succeed within 3 attempts

  @s3-storage @credentials
  Scenario: S3 storage fails gracefully with invalid credentials
    Given I am using "s3" storage backend
    And I have invalid AWS credentials
    When I attempt to store artifact "test-results.json"
    Then the operation should fail with error "Authentication failed"
    And the error should suggest checking credentials
    And no data should be partially uploaded

  #----------------------------------------------------------------------------
  # GitHub Actions Artifact Storage
  #----------------------------------------------------------------------------

  @github-artifacts @smoke-test
  Scenario: GitHub Actions storage uses @actions/artifact API
    Given I am using "github-actions" storage backend
    And I am running in a GitHub Actions workflow
    When I store artifact "test-results.json"
    Then the artifact should be uploaded via @actions/artifact
    And the artifact should appear in the GitHub Actions run UI
    And the artifact should be downloadable for 90 days (default retention)

  @github-artifacts @outside-actions
  Scenario: GitHub Actions storage fails gracefully outside GitHub Actions
    Given I am using "github-actions" storage backend
    And I am NOT running in a GitHub Actions workflow
    When I attempt to store artifact "test-results.json"
    Then the operation should fail with error "Not running in GitHub Actions"
    And the error should suggest using a different backend

  #----------------------------------------------------------------------------
  # Compression
  #----------------------------------------------------------------------------

  @compression @gzip @smoke-test
  Scenario: Compression reduces storage size by 60-80% with gzip
    Given I am using "local" storage backend
    And compression is enabled with "gzip"
    When I store a 10MB text artifact "large-log.txt"
    Then the stored file should be compressed
    And the compressed size should be 20-40% of original (2-4MB)
    And the compression time should be less than 1 second

  @compression @zstd
  Scenario: Compression uses zstd for faster compression
    Given I am using "local" storage backend
    And compression is enabled with "zstd"
    When I store a 10MB text artifact "large-log.txt"
    Then the compressed size should be 15-30% of original (1.5-3MB)
    And the compression time should be less than 0.5 seconds (faster than gzip)

  @compression @already-compressed
  Scenario: Compression skips files that are already compressed
    Given I am using "local" storage backend
    And compression is enabled with "gzip"
    When I store a PNG image artifact "screenshot.png"
    Then the storage should detect the file is already compressed
    And the file should be stored without additional compression
    And the stored size should equal the original size

  @compression @decompression
  Scenario: Decompression is transparent on retrieval
    Given I have stored a compressed artifact "report.json.gz"
    When I retrieve artifact "report.json.gz"
    Then the content should be automatically decompressed
    And the returned data should match the original uncompressed data
    And the decompression time should be less than 500ms

  #----------------------------------------------------------------------------
  # Retention Policies
  #----------------------------------------------------------------------------

  @retention @default-policy @smoke-test
  Scenario: Retention policy deletes artifacts after 30 days (default)
    Given I am using "local" storage backend
    And the default retention policy is 30 days
    When I store an artifact "old-report.json"
    And 30 days pass
    And the retention cleanup job runs
    Then the artifact "old-report.json" should be deleted
    And the metadata index should be updated

  @retention @custom-ttl
  Scenario: Retention policy supports custom TTL per artifact type
    Given I have configured retention policies:
      """
      {
        "test-results": 7,
        "coverage-reports": 30,
        "security-scans": 90,
        "performance-metrics": 180
      }
      """
    When I store artifacts of different types
    And the retention cleanup job runs
    Then each artifact should be deleted according to its TTL
    And no artifacts should be deleted before their TTL expires

  @retention @ttl-zero
  Scenario: Retention policy with TTL=0 deletes immediately
    Given I have configured retention TTL=0 for "temp-artifacts"
    When I store an artifact "temp-data.json" with type "temp-artifacts"
    Then the artifact should be deleted immediately after use
    And the storage should confirm deletion

  @retention @ttl-forever
  Scenario: Retention policy with TTL=-1 keeps artifacts forever
    Given I have configured retention TTL=-1 for "compliance-reports"
    When I store an artifact "audit-log.json" with type "compliance-reports"
    And 365 days pass
    And the retention cleanup job runs
    Then the artifact should still exist
    And the artifact should not be deleted

  #----------------------------------------------------------------------------
  # Metadata Index
  #----------------------------------------------------------------------------

  @metadata @index @smoke-test
  Scenario: Metadata index stores artifact metadata
    Given I am using "local" storage backend
    When I store an artifact "test-results.json" with metadata:
      """
      {
        "type": "test-results",
        "framework": "jest",
        "timestamp": "2025-11-12T10:00:00Z",
        "tags": ["unit-tests", "ci"]
      }
      """
    Then the metadata should be stored in the index (SQLite or DynamoDB)
    And the metadata should be queryable

  @metadata @query
  Scenario: Metadata index supports querying by multiple criteria
    Given I have stored 100 artifacts with various metadata
    When I query for artifacts where:
      """
      {
        "type": "coverage-reports",
        "date_range": "2025-11-01 to 2025-11-12",
        "tags": ["integration-tests"]
      }
      """
    Then the query should return matching artifacts
    And the query time should be less than 200ms
    And the results should be sorted by timestamp (descending)

  #----------------------------------------------------------------------------
  # Query API
  #----------------------------------------------------------------------------

  @query-api @smoke-test
  Scenario: Query API retrieves historical artifacts
    Given I have stored 50 artifacts over 30 days
    When I GET "/api/v1/artifacts?type=coverage-reports&limit=10"
    Then the response should contain the 10 most recent coverage reports
    And the response should include pagination metadata
    And the response time should be less than 200ms

  @query-api @filtering
  Scenario: Query API supports filtering by date range
    Given I have stored artifacts from 2025-10-01 to 2025-11-12
    When I GET "/api/v1/artifacts?start_date=2025-11-01&end_date=2025-11-07"
    Then the response should contain only artifacts from Nov 1-7
    And the results should be sorted by date

  @query-api @pagination
  Scenario: Query API supports pagination for large result sets
    Given I have stored 1000 artifacts
    When I GET "/api/v1/artifacts?limit=50&offset=0"
    Then the response should contain 50 artifacts (page 1)
    And the response should include:
      """
      {
        "total": 1000,
        "limit": 50,
        "offset": 0,
        "next": "/api/v1/artifacts?limit=50&offset=50"
      }
      """

  #----------------------------------------------------------------------------
  # Performance Requirements
  #----------------------------------------------------------------------------

  @performance @store-retrieve @sla
  Scenario: Storage meets latency SLAs for different file sizes
    Given I am using "local" storage backend
    When I store and retrieve files of various sizes
    Then the latency should meet these SLAs:
      | File Size | Store Time | Retrieve Time |
      | 1 MB      | <100ms     | <50ms         |
      | 10 MB     | <1s        | <500ms        |
      | 100 MB    | <5s        | <2s           |

  @performance @concurrent
  Scenario: Storage handles 10+ concurrent uploads without degradation
    Given I am using "local" storage backend
    When I upload 10 artifacts concurrently (1MB each)
    Then all uploads should complete successfully
    And the slowest upload should complete within 2 seconds
    And no uploads should fail due to locking issues

  #----------------------------------------------------------------------------
  # Data Integrity
  #----------------------------------------------------------------------------

  @integrity @checksum
  Scenario: Storage verifies data integrity with checksums
    Given I am using "s3" storage backend
    When I store an artifact "test-results.json"
    Then the storage should calculate SHA-256 checksum
    And the checksum should be stored in metadata
    When I retrieve the artifact
    Then the storage should verify the checksum
    And the retrieval should fail if checksum mismatch

  @integrity @corruption
  Scenario: Storage detects corrupted artifacts
    Given I have stored an artifact "report.json"
    And the stored data becomes corrupted (bit flip)
    When I retrieve the artifact
    Then the checksum verification should fail
    And the error message should indicate data corruption
    And the error should suggest restoring from backup

#==============================================================================
# MILESTONE 1.4: BADGE GENERATION (Week 7)
#==============================================================================

@milestone-1.4 @badge-generation @priority-medium
Feature: Badge Generation for README Integration
  As a project maintainer
  I want to display quality badges in my README
  So that I can showcase code quality metrics visually

  Background:
    Given the badge service is running at http://localhost:8080
    And the badge service has cached recent test results

  #----------------------------------------------------------------------------
  # Badge Types
  #----------------------------------------------------------------------------

  @badge-types @coverage @smoke-test
  Scenario: Badge service generates coverage badge
    Given the current code coverage is 87.5%
    When I GET "/badge/coverage/org/repo"
    Then the response status should be 200 OK
    And the Content-Type should be "image/svg+xml"
    And the badge should display "coverage 87.5%"
    And the badge color should be green (coverage >85%)

  @badge-types @quality
  Scenario: Badge service generates quality score badge
    Given the current quality score is 92
    When I GET "/badge/quality/org/repo"
    Then the badge should display "quality 92"
    And the badge color should be green (quality >85)

  @badge-types @security
  Scenario: Badge service generates security badge
    Given there are 0 critical security issues
    And there are 2 high severity issues
    When I GET "/badge/security/org/repo"
    Then the badge should display "security 2 high"
    And the badge color should be yellow (has high issues)

  @badge-types @tests
  Scenario: Badge service generates test count badge
    Given the test suite has 142 tests
    And all tests are passing
    When I GET "/badge/tests/org/repo"
    Then the badge should display "tests 142 passing"
    And the badge color should be green (all passing)

  @badge-types @status
  Scenario: Badge service generates overall status badge
    Given the latest build passed
    When I GET "/badge/status/org/repo"
    Then the badge should display "build passing"
    And the badge color should be green

  #----------------------------------------------------------------------------
  # Badge Colors
  #----------------------------------------------------------------------------

  @badge-colors @coverage-thresholds
  Scenario Outline: Coverage badge color changes based on percentage
    Given the current code coverage is <coverage>%
    When I GET "/badge/coverage/org/repo"
    Then the badge color should be <color>

    Examples:
      | coverage | color  |
      | 95       | green  |
      | 87       | green  |
      | 85       | green  |
      | 80       | yellow |
      | 75       | yellow |
      | 70       | yellow |
      | 65       | red    |
      | 50       | red    |

  @badge-colors @quality-thresholds
  Scenario Outline: Quality badge color changes based on score
    Given the current quality score is <score>
    When I GET "/badge/quality/org/repo"
    Then the badge color should be <color>

    Examples:
      | score | color  |
      | 95    | green  |
      | 85    | green  |
      | 80    | yellow |
      | 70    | yellow |
      | 65    | red    |

  @badge-colors @security-thresholds
  Scenario Outline: Security badge color based on issue severity
    Given there are <critical> critical and <high> high severity issues
    When I GET "/badge/security/org/repo"
    Then the badge color should be <color>

    Examples:
      | critical | high | color  |
      | 1        | 0    | red    |
      | 0        | 5    | yellow |
      | 0        | 0    | green  |

  #----------------------------------------------------------------------------
  # Badge Styles
  #----------------------------------------------------------------------------

  @badge-styles @flat
  Scenario: Badge service supports flat style (default)
    When I GET "/badge/coverage/org/repo?style=flat"
    Then the badge should use flat style (shields.io format)
    And the badge should have no shadows or gradients

  @badge-styles @flat-square
  Scenario: Badge service supports flat-square style
    When I GET "/badge/coverage/org/repo?style=flat-square"
    Then the badge should use flat-square style
    And the badge should have sharp corners

  @badge-styles @plastic
  Scenario: Badge service supports plastic style
    When I GET "/badge/coverage/org/repo?style=plastic"
    Then the badge should use plastic style
    And the badge should have gradients

  @badge-styles @for-the-badge
  Scenario: Badge service supports for-the-badge style
    When I GET "/badge/coverage/org/repo?style=for-the-badge"
    Then the badge should use for-the-badge style
    And the text should be uppercase
    And the badge should be larger

  #----------------------------------------------------------------------------
  # Caching
  #----------------------------------------------------------------------------

  @caching @smoke-test
  Scenario: Badge service caches badges for 5 minutes (default TTL)
    Given the badge cache is empty
    When I GET "/badge/coverage/org/repo"
    Then the badge should be generated
    And the badge should be cached with TTL=300 seconds
    When I GET "/badge/coverage/org/repo" again within 5 minutes
    Then the cached badge should be returned
    And the generation time should be <10ms (cached)

  @caching @ttl
  Scenario: Badge service respects custom cache TTL
    When I GET "/badge/coverage/org/repo?cache_ttl=60"
    Then the badge should be cached with TTL=60 seconds
    When I GET the same badge after 61 seconds
    Then the badge should be regenerated

  @caching @invalidation
  Scenario: Badge cache is invalidated on new test run
    Given the coverage badge is cached
    When a new test run completes
    And the coverage changes from 85% to 90%
    Then the cached badge should be invalidated
    When I GET "/badge/coverage/org/repo"
    Then the badge should reflect the new coverage (90%)

  @caching @hit-rate @sla
  Scenario: Badge cache achieves >80% hit rate
    Given the badge service has been running for 24 hours
    When I check the cache hit rate
    Then the hit rate should be greater than 80%

  #----------------------------------------------------------------------------
  # Cross-Platform Rendering
  #----------------------------------------------------------------------------

  @rendering @github
  Scenario: Badge renders correctly in GitHub README
    When I embed the badge in GitHub README:
      ```markdown
      ![Coverage](http://localhost:8080/badge/coverage/org/repo)
      ```
    Then the badge should render correctly in GitHub
    And the badge should be clickable (link to report)

  @rendering @gitlab
  Scenario: Badge renders correctly in GitLab README
    When I embed the badge in GitLab README:
      ```markdown
      ![Coverage](http://localhost:8080/badge/coverage/org/repo)
      ```
    Then the badge should render correctly in GitLab

  @rendering @bitbucket
  Scenario: Badge renders correctly in Bitbucket README
    When I embed the badge in Bitbucket README
    Then the badge should render correctly in Bitbucket

  #----------------------------------------------------------------------------
  # Edge Cases
  #----------------------------------------------------------------------------

  @edge-cases @no-data
  Scenario: Badge shows "N/A" when no data is available (new project)
    Given no test runs have been recorded for "org/new-repo"
    When I GET "/badge/coverage/org/new-repo"
    Then the badge should display "coverage N/A"
    And the badge color should be gray (lightgray)

  @edge-cases @invalid-values
  Scenario: Badge handles NaN and invalid values gracefully
    Given the coverage calculation returns NaN
    When I GET "/badge/coverage/org/repo"
    Then the badge should display "coverage unknown"
    And the badge color should be gray

  @edge-cases @long-text
  Scenario: Badge truncates very long text
    Given the badge text is "very long repository name that exceeds 50 characters"
    When I GET "/badge/coverage/org/very-long-repository-name"
    Then the badge text should be truncated to 50 characters
    And the text should end with ellipsis "..."

  @edge-cases @special-characters
  Scenario: Badge properly escapes special characters in text
    Given the repository name contains special characters "<repo&name>"
    When I GET "/badge/coverage/org/<repo&name>"
    Then the special characters should be properly escaped in SVG
    And the badge should render correctly

  #----------------------------------------------------------------------------
  # Accessibility
  #----------------------------------------------------------------------------

  @accessibility @screen-readers
  Scenario: Badge includes alt text for screen readers
    When I GET "/badge/coverage/org/repo"
    Then the SVG should include <title> element
    And the title should be "Code coverage: 87.5%"
    And the SVG should include <desc> element for detailed description

  @accessibility @color-blind
  Scenario: Badge is distinguishable for color-blind users
    When I GET "/badge/coverage/org/repo?accessible=true"
    Then the badge should use patterns in addition to colors
    Or the badge should use high-contrast colors
    And the badge should be distinguishable in grayscale

  #----------------------------------------------------------------------------
  # Security
  #----------------------------------------------------------------------------

  @security @private-repos
  Scenario: Badge service does not leak data from private repositories
    Given "org/private-repo" is a private repository
    And I am not authenticated
    When I GET "/badge/coverage/org/private-repo"
    Then the response status should be 403 Forbidden
    Or the badge should display "private"

  @security @rate-limiting
  Scenario: Badge service rate limits requests to prevent abuse
    When I make 1000 requests to "/badge/coverage/org/repo" from the same IP
    Then the first 500 requests should succeed
    And subsequent requests should be rate limited (429 Too Many Requests)

  #----------------------------------------------------------------------------
  # Performance Requirements
  #----------------------------------------------------------------------------

  @performance @generation-time @sla
  Scenario: Badge generation meets latency SLAs
    Given the badge cache is empty
    When I request a badge
    Then the generation time should be <100ms (uncached)
    When I request the same badge again
    Then the response time should be <10ms (cached)

  @performance @concurrent-requests @sla
  Scenario: Badge service handles 100+ concurrent requests
    When I make 100 concurrent badge requests
    Then all requests should complete successfully
    And the average response time should be <50ms
    And no requests should timeout

#==============================================================================
# CROSS-CUTTING SCENARIOS
#==============================================================================

@cross-cutting @integration
Feature: End-to-End CI/CD Integration Workflow
  As a complete CI/CD pipeline
  I want to use all Phase 1 features together
  So that I can automate quality engineering from commit to deployment

  @e2e @github-actions
  Scenario: Complete GitHub Actions workflow using all Phase 1 features
    Given a GitHub repository with source code
    And a GitHub Actions workflow configured with AQE Fleet
    When a developer pushes code to a feature branch
    Then the GitHub Actions workflow should:
      | Step | Action | Expected Result |
      | 1 | Trigger webhook API | Job queued with ID |
      | 2 | Generate tests via CLI (--ci-mode) | Tests created in tests/ |
      | 3 | Execute tests via API | All tests pass |
      | 4 | Store artifacts (results, coverage) | Artifacts saved to GitHub Actions |
      | 5 | Generate badges | Badges updated in README |
      | 6 | Run quality gate | Gate passes (coverage >80%) |
    And the total workflow time should be less than 5 minutes
    And all artifacts should be downloadable from GitHub UI

  @e2e @gitlab-ci
  Scenario: Complete GitLab CI workflow using webhook API
    Given a GitLab repository with source code
    And a .gitlab-ci.yml configured to use AQE Fleet webhook API
    When a merge request is created
    Then the GitLab CI pipeline should:
      | Step | API Endpoint | Expected Result |
      | 1 | POST /api/v1/test/generate | Job ID returned |
      | 2 | GET /api/v1/job/{id}/status | Status: completed |
      | 3 | POST /api/v1/coverage/analyze | Coverage: 87% |
      | 4 | POST /api/v1/quality/gate | Gate: passed |
    And the coverage badge should be updated
    And the merge request should have a comment with results

  @e2e @jenkins
  Scenario: Complete Jenkins pipeline using webhook API
    Given a Jenkins job with Jenkinsfile
    And the Jenkinsfile configured to call AQE Fleet API
    When the Jenkins job is triggered
    Then the pipeline should POST to webhook API
    And the artifacts should be stored via artifact storage API
    And the badges should be generated
    And the quality gate should determine build success/failure

  @e2e @error-recovery
  Scenario: System recovers gracefully from partial failures
    Given a CI/CD workflow is running
    When the Redis connection is lost during job execution
    Then the webhook API should queue jobs in memory (up to 1000)
    And the system should continue processing after Redis reconnects
    And no jobs should be lost
    And the badges should reflect eventual consistency

---

## Test Data & Fixtures

### Test Projects

**Small Project**: 50 files, 5k LOC, 20 tests
**Medium Project**: 200 files, 50k LOC, 500 tests
**Large Project**: 1000 files, 500k LOC, 5000 tests

### API Keys for Testing

- Valid key: `aqe_test_1234567890abcdef1234567890abcdef`
- Expired JWT: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (expired 1 hour ago)
- Invalid key: `invalid_key_12345`

### Sample Artifacts

- `test-results.json`: 10KB JSON file with test results
- `coverage-report.html`: 500KB HTML coverage report
- `security-findings.json`: 50KB security scan results
- `large-performance-log.txt`: 100MB log file (for compression tests)

### Metadata Examples

```json
{
  "type": "coverage-report",
  "framework": "jest",
  "timestamp": "2025-11-12T10:00:00Z",
  "coverage": 87.5,
  "tags": ["unit-tests", "ci", "feature-branch"]
}
```

---

**Generated by**: qe-requirements-validator agent
**Date**: 2025-11-12
**Total Scenarios**: 120+
**Coverage**: All Phase 1 milestones (CLI, API, Storage, Badges)
**Status**: ✅ Ready for Test Implementation
