# Testing Guide

## Purpose

This document explains how the Job Market Intelligence test suite is structured, what each testing layer verifies, how to run the tests, and what the test suite does and does not guarantee.

The project uses Pytest with separate unit, integration, and end-to-end test layers.

Production smoke testing is a separate production-verification layer and is currently postponed because the Neon data-transfer quota issue prevents reliable production database verification.

---

## Testing Strategy

The testing strategy moves from isolated components toward complete application workflows:

```text
Unit Tests
    ↓
Integration Tests
    ↓
E2E Tests
    ↓
Production Smoke Tests
````

Each layer has a different purpose.

### Unit Tests

Unit tests verify individual pieces of application logic in isolation.

Typical targets include:

* Services
* Repositories
* ETL components
* Validation and enrichment logic
* Configuration behavior
* Dashboard components and helpers

Unit tests should be fast and should avoid unnecessary dependence on external infrastructure.

Run:

```bash
pytest tests/unit/ -v
```

---

### Integration Tests

Integration tests verify that application components work correctly together.

The repository contains integration coverage for areas including:

* API behavior
* Database access
* Repository/service interaction
* ETL/database integration
* Dashboard/API interaction
* Analytics pipelines

Run:

```bash
pytest tests/integration/ -v
```

Integration tests may require infrastructure such as PostgreSQL, depending on the test being executed.

---

### End-to-End Tests

End-to-end tests exercise complete workflows across multiple application components.

The current E2E suite includes workflows covering areas such as:

* Dashboard loading
* Dashboard refresh
* ETL workflow
* Health workflow
* Job filtering
* Job search

Run:

```bash
pytest tests/e2e/ -v
```

E2E tests provide stronger workflow-level confidence than isolated unit tests, but they do not prove that every possible production condition has been tested.

---

## Production Smoke Tests

Production smoke tests are intended to verify that the deployed system is functioning correctly in its real production environment.

They are conceptually the final verification layer:

```text
Application Tests
       ↓
Deployment
       ↓
Production Smoke
```

Typical production verification should cover the critical production path, including:

* API availability
* API health
* Database connectivity
* Dashboard availability
* Critical API responses
* Production configuration
* Basic end-to-end availability

Production smoke testing is currently **postponed** because the production Neon database has exceeded its data-transfer quota.

This is an infrastructure limitation affecting production verification, not a failure of the unit, integration, or E2E test layers.

Production smoke testing should be resumed once reliable Neon database connectivity is available.

---

## Test Directory Structure

```text
tests/
├── e2e/
│   ├── test_dashboard_loading.py
│   ├── test_dashboard_refresh.py
│   ├── test_etl_workflow.py
│   ├── test_health_workflow.py
│   ├── test_job_filtering.py
│   └── test_job_search.py
│
├── integration/
│   ├── test_analytics_pipeline.py
│   ├── test_api.py
│   ├── test_dashboard_api.py
│   ├── test_database.py
│   ├── test_etl_pipeline.py
│   └── test_repository_service.py
│
├── unit/
│   ├── backend/
│   └── dashboard/
│
└── fixtures/
```

The unit and integration directories contain additional test modules beyond the representative files shown above.

---

## Pytest Configuration

Pytest is configured in `pyproject.toml`.

The project defines these markers:

```text
unit
integration
e2e
```

Markers are strict, so misspelled or undefined markers are treated as configuration errors.

The configured test discovery pattern is:

```text
test_*.py
```

The test root is:

```text
tests/
```

The repository also configures the project and dashboard directories on the Python path.

---

## Running the Full Suite

Run all tests with:

```bash
pytest
```

A more verbose run is:

```bash
pytest -v
```

The full suite combines the unit, integration, and E2E layers.

---

## Running Tests by Marker

Run unit tests:

```bash
pytest -m unit
```

Run integration tests:

```bash
pytest -m integration
```

Run E2E tests:

```bash
pytest -m e2e
```

Markers are useful when working on a specific layer without running the entire suite.

---

## Running a Specific Test File

For example:

```bash
pytest tests/integration/test_api.py -v
```

Or:

```bash
pytest tests/e2e/test_job_search.py -v
```

A specific test can also be selected with its node ID:

```bash
pytest tests/integration/test_api.py::test_name -v
```

Replace `test_name` with the actual test function name.

---

## Coverage

Coverage should be measured from the actual test run rather than treated as a permanent project constant.

Run the full suite with coverage using:

```bash
pytest --cov=. --cov-report=term-missing
```

Coverage reports help identify code paths that are not exercised by the automated tests.

Coverage percentage can change as the application and test suite evolve. Do not interpret a high coverage percentage as proof that the system has no defects.

Coverage is one quality signal among several.

---

## What the Automated Tests Do Not Guarantee

Passing automated tests does not prove that:

* Every production configuration is correct
* External APIs will always be available
* Neon will remain within its service limits
* Render will always deploy successfully
* Streamlit Community Cloud will always be available
* Production credentials are correctly configured
* Network connectivity is available
* External service quotas will not be exceeded
* Production data is always semantically correct
* Every possible user workflow has been exercised

This is why production smoke testing remains a separate verification layer.

---

## CI Testing

GitHub Actions runs automated quality and test checks through the repository workflows.

The current CI setup includes:

### Code Quality

The quality workflow runs:

```text
Ruff
Black --check
MyPy

MyPy is currently run against the app package.

Unit Tests

The quality workflow runs the unit test suite with coverage:

pytest tests/unit -v
Integration Tests

The quality workflow runs the integration test suite with coverage:

pytest tests/integration -v
E2E Tests

The E2E workflow runs the end-to-end test suite with coverage:

pytest tests/e2e -v

Coverage reports from the automated test jobs are uploaded by the workflows.

The authoritative CI configuration is:

.github/workflows/quality.yml
.github/workflows/e2e.yml

When a test passes locally but fails in CI, compare:

Python version
Dependency installation
Environment variables
Database availability
Operating-system behavior
Working directory
Test isolation
External service dependencies

## Test Failures

When a test fails, first identify which testing layer failed.

### Unit Failure

Check:

1. The failing assertion
2. The input fixture
3. The function under test
4. Recent code changes
5. Mock or fixture behavior

### Integration Failure

Check:

1. Database availability
2. Environment variables
3. API configuration
4. Migration state
5. Service dependencies
6. Test fixtures

### E2E Failure

Check:

1. Whether required services are running
2. API health
3. Database availability
4. Dashboard availability
5. Test configuration
6. Test data and fixtures
7. Recent application changes

### Production Verification Failure

Check production infrastructure before changing application code.

For example, a database-provider quota problem can cause API startup and health failures even when the application code itself has not changed.

See [`deployment.md`](deployment.md) and [`troubleshooting.md`](troubleshooting.md) for production diagnosis and recovery procedures.

---

## Local Test Workflow

A practical development workflow is:

```text
1. Make a focused code change
          ↓
2. Run relevant unit tests
          ↓
3. Run relevant integration tests
          ↓
4. Run relevant E2E tests when applicable
          ↓
5. Run the full suite
          ↓
6. Review failures and coverage
          ↓
7. Run quality checks
          ↓
8. Review the Git diff
```

For changes affecting deployment, database migrations, or production configuration, follow the additional procedures in the deployment and operations documentation.

---

## Quality Checks

The project uses development tooling including:

* Pytest for automated tests
* Black for formatting
* Ruff for linting
* MyPy for type checking

Typical checks include:

```bash
pytest
black --check .
ruff check .
mypy .
```

Run the checks relevant to the files being changed before committing.

---

## Testing Principles

The test suite follows several practical principles:

1. **Test behavior rather than implementation details.**
2. **Keep unit tests isolated and fast.**
3. **Use integration tests where component interaction matters.**
4. **Use E2E tests for important complete workflows.**
5. **Keep production verification separate from application tests.**
6. **Do not treat coverage as proof of correctness.**
7. **Investigate infrastructure failures before changing application code.**
8. **Keep tests aligned with the current application behavior.**

---

## Related Documentation

* [`development.md`](development.md) — local development and test execution
* [`deployment.md`](deployment.md) — deployment and production verification
* [`operations.md`](operations.md) — production operations and monitoring
* [`troubleshooting.md`](troubleshooting.md) — failure diagnosis and recovery
* [`architecture.md`](architecture.md) — system architecture
* [`api_contract.md`](api_contract.md) — API behavior and contract