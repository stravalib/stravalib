# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Stravalib is a Python library providing easy-to-use tools for accessing and downloading Strava data from the Strava V3 REST API. The library supports authentication, rate limiting, data access/download, and unit conversion through the Pint library.

## Development Commands

### Testing

Run all tests across all supported Python versions (3.10-3.14):
```bash
nox -s tests
```

Run tests for a specific Python version:
```bash
nox -s tests-3.11
```

Run a single test file:
```bash
pytest src/stravalib/tests/unit/test_client.py
```

Run a specific test:
```bash
pytest src/stravalib/tests/unit/test_client.py::test_name
```

### Type Checking

Run mypy type checking:
```bash
nox -s mypy
```

### Linting and Formatting

The project uses pre-commit hooks with ruff (linting), black (formatting), and codespell (spell checking).

Install pre-commit hooks:
```bash
pre-commit install --install-hooks
```

Run pre-commit on all files:
```bash
pre-commit run --all-files
```

Run a specific hook:
```bash
pre-commit run ruff --all-files
```

### Documentation

Build docs:
```bash
nox -s docs
```

Build docs with live reload (for local development):
```bash
nox -s docs-live
```

Clean doc build artifacts:
```bash
nox -s docs-clean
```

### Building

Build the package (creates wheel and sdist in dist/):
```bash
nox -s build
```

Clean build artifacts:
```bash
nox -s clean_build
```

## Code Architecture

### Core Components

**Client (`client.py`)**: Main interface for interacting with Strava V3 API. The `Client` class handles:
- Authentication and token management (including automatic token refresh)
- Rate limiting via `stravalib.util.limiter.RateLimiter`
- All API method calls (activities, athletes, clubs, segments, etc.)
- Batch iteration over paginated results via `BatchedResultsIterator`

**Protocol (`protocol.py`)**: Low-level HTTP communication with Strava API. `ApiV3` class handles:
- HTTP request execution (GET, POST, PUT, DELETE)
- Token refresh logic when tokens expire
- Error handling and response parsing
- OAuth2 authorization flow

**Model (`model.py`)**: Entity classes representing Strava data types (Activity, Athlete, Gear, etc.). These classes:
- Inherit base fields from auto-generated `strava_model.py` (from official Strava API spec)
- Add behavior: type enrichment, unit conversion, lazy loading of related entities
- Use Pydantic v2 for validation and serialization
- Support "bound" entities that can lazy-load related data via `bind_client()`

**Strava Model (`strava_model.py`)**: Auto-generated from Strava API specification. DO NOT manually edit this file - it's generated from the official Strava Swagger/OpenAPI spec.

**Unit Helper (`unit_helper.py`, `unit_registry.py`)**: Unit conversion utilities using Pint library for handling distances, speeds, elevations, etc.

**Exceptions (`exc.py`)**: Custom exception classes and warning utilities for Strava API errors and unofficial/deprecated features.

### Test Architecture

Tests are organized into:
- `src/stravalib/tests/unit/`: Unit tests that don't hit the real API
- `src/stravalib/tests/integration/`: Integration tests using the API stub

**Mock Fixture**: Tests use `StravaAPIMock` (in `integration/strava_api_stub.py`) to avoid hitting the real Strava API. This stub intercepts HTTP requests and returns mock responses. The `mock_strava_api` fixture in `conftest.py` provides this functionality.

When writing tests:
- Always use the mock fixtures to prevent real API calls
- Unit tests should be fast and isolated
- Integration tests verify end-to-end flows with mocked API responses

### Authentication Flow

1. Client is initialized with optional `access_token`, `refresh_token`, and `token_expires`
2. Before each API call, `ApiV3` checks if token is expired (comparing current time to `token_expires`)
3. If expired, automatically calls `refresh_access_token()` using `refresh_token`, `client_id`, and `client_secret` (from environment or constructor)
4. New tokens are stored and used for subsequent requests

### Rate Limiting

The `Client` uses `stravalib.util.limiter.RateLimiter` by default to respect Strava's rate limits. The rate limiter:
- Tracks requests in 15-minute and daily windows
- Sleeps when approaching limits
- Can be customized or disabled via constructor

## Important Conventions

### Code Style

- Line length: 79 characters (enforced by black and ruff)
- Type hints: Required for all function signatures (enforced by mypy with strict settings)
- Docstrings: Use NumPy-style docstrings for public APIs

### Python Version Support

- Minimum: Python 3.11
- Actively tested: 3.11, 3.12, 3.13, 3.14
- Type checking targets 3.11+ features

### Pydantic Usage

The codebase uses Pydantic v2. When working with models:
- All model classes inherit from `pydantic.BaseModel`
- Use `field_validator` and `model_validator` for custom validation
- Auto-generated models in `strava_model.py` are the source of truth for Strava API schema

### Dependencies

Core dependencies (see pyproject.toml):
- pint: Unit conversion
- arrow: Advanced datetime handling
- requests: HTTP client
- pydantic>=2.0: Data validation and serialization

Note: Timezone handling uses the standard library `zoneinfo` module (Python 3.9+)

## CI/CD

GitHub Actions workflows:
- `build-test.yml`: Runs pytest across all OS (Ubuntu, macOS, Windows) and Python versions
- `type-check.yml`: Runs mypy type checking
- `build-docs.yml`: Builds and deploys documentation to ReadTheDocs
- `publish-pypi.yml`: Publishes package to PyPI on releases

Pre-commit.ci is configured to automatically run hooks on PRs.
