# Code Dojo Test Suite

This directory contains comprehensive tests for the Code Dojo application, including unit tests and end-to-end Playwright tests for the PR submission feature.

## Table of Contents

- [Test Structure](#test-structure)
- [Quick Start](#quick-start)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Test Structure

```
tests/
├── README.md                        # This file
├── __init__.py                      # Test package init
├── test_github_pr.py                # Unit tests for PR service
├── test_agent_harness.py            # Unit tests for agent harness
└── playwright/                      # Playwright E2E tests
    ├── conftest.py                  # Playwright fixtures
    └── test_pr_submission.py        # PR submission E2E tests
```

## Quick Start

### 1. Install Test Dependencies

```bash
# Install all test dependencies
pip install -r requirements-test.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Run Tests

```bash
# Run all unit tests
./run_tests.sh unit

# Run Playwright E2E tests
./run_tests.sh playwright

# Run all tests
./run_tests.sh all
```

## Test Types

### Unit Tests

Unit tests verify individual functions and components in isolation.

**Location**: `tests/test_*.py`

**What's tested**:
- `test_github_pr.py`: PR URL parsing, validation, metadata fetching, file fetching
- Functions from `services/github_pr.py`

**Run with**:
```bash
pytest tests/test_github_pr.py -v
```

### Playwright E2E Tests

End-to-end tests that simulate real user interactions in a browser.

**Location**: `tests/playwright/test_pr_submission.py`

**What's tested**:
- Complete PR submission workflow
- Real-time PR preview functionality
- PR validation (format, base repo)
- Review tab PR information display
- File-by-file diff viewer
- Regression scenarios

**Run with**:
```bash
# Headed mode (watch tests run)
pytest tests/playwright/ --headed --slowmo 500

# Headless mode (CI)
pytest tests/playwright/
```

## Running Tests

### Using the Test Runner Script

The `run_tests.sh` script provides convenient commands:

```bash
# Run unit tests
./run_tests.sh unit

# Run unit tests with coverage report
./run_tests.sh unit-cov

# Run Playwright tests (headed - watch browser)
./run_tests.sh playwright

# Run Playwright tests (headless - CI mode)
./run_tests.sh playwright-ci

# Run all tests
./run_tests.sh all

# Run specific test file
./run_tests.sh file tests/test_github_pr.py

# Start Flask app for manual testing
./run_tests.sh start-app

# Stop Flask test app
./run_tests.sh stop-app

# Check dependencies
./run_tests.sh check
```

### Using pytest Directly

```bash
# Run all unit tests
pytest tests/test_*.py -v

# Run with coverage
pytest tests/test_*.py --cov=services --cov-report=html

# Run specific test class
pytest tests/test_github_pr.py::TestParsePrUrl -v

# Run specific test
pytest tests/test_github_pr.py::TestParsePrUrl::test_valid_pr_url -v

# Run Playwright tests
pytest tests/playwright/ -v

# Run tests with specific markers
pytest -m "unit" -v
pytest -m "playwright" -v
```

### Playwright Test Options

```bash
# Run with headed browser (watch tests)
pytest tests/playwright/ --headed

# Run with slow motion (better visibility)
pytest tests/playwright/ --headed --slowmo 1000

# Run specific browser
pytest tests/playwright/ --browser chromium
pytest tests/playwright/ --browser firefox

# Take screenshots on failure
pytest tests/playwright/ --screenshot only-on-failure

# Record videos
pytest tests/playwright/ --video retain-on-failure

# Run in parallel (requires pytest-xdist)
pytest tests/playwright/ -n 4
```

## Writing Tests

### Unit Test Example

```python
# tests/test_myfeature.py
import pytest
from services.myfeature import my_function

class TestMyFunction:
    """Tests for my_function."""

    def test_valid_input(self):
        """Test with valid input."""
        result = my_function("valid")
        assert result == "expected"

    def test_invalid_input(self):
        """Test with invalid input."""
        with pytest.raises(ValueError):
            my_function("invalid")
```

### Playwright Test Example

```python
# tests/playwright/test_myfeature.py
import pytest
from playwright.sync_api import Page, expect

def test_my_feature(authenticated_page: Page, base_url: str):
    """Test my feature."""
    # Navigate
    authenticated_page.goto(f"{base_url}/my-page")

    # Interact
    authenticated_page.click('button#my-button')

    # Assert
    result = authenticated_page.locator('.result')
    expect(result).to_have_text('Expected Text')
```

### Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
   - Good: `test_pr_preview_shows_error_on_invalid_url`
   - Bad: `test_preview`

2. **Test Organization**: Group related tests in classes
   ```python
   class TestPRSubmissionFlow:
       """Tests for PR submission workflow."""
   ```

3. **Fixtures**: Use fixtures for setup/teardown
   ```python
   @pytest.fixture
   def test_data():
       return {"key": "value"}
   ```

4. **Assertions**: Use descriptive assertion messages
   ```python
   assert result is not None, "Expected result to be populated"
   ```

5. **Mocking**: Mock external dependencies in unit tests
   ```python
   @patch('services.github_pr.requests.get')
   def test_with_mock(mock_get):
       mock_get.return_value = Mock(status_code=200)
   ```

## CI/CD Integration

Tests run automatically in GitHub Actions on:
- Push to `main`, `develop`, or `feature/*` branches
- Pull requests to `main` or `develop`

### GitHub Actions Workflow

The workflow (`.github/workflows/test.yml`) includes:
- Unit tests on Python 3.10 and 3.11
- Code coverage reporting to Codecov
- Playwright E2E tests
- Linting with flake8 and pylint

### Required Secrets

Configure these in GitHub Settings → Secrets:
- `ANTHROPIC_API_KEY`: For AI feedback tests
- `GITHUB_TOKEN`: For GitHub API rate limits (or use default GITHUB_TOKEN)

## Test Configuration

### pytest.ini

The `pytest.ini` file configures:
- Test discovery patterns
- Test paths
- Console output options
- Test markers (unit, integration, e2e, playwright, slow)

### Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_unit():
    pass

@pytest.mark.playwright
def test_e2e():
    pass

@pytest.mark.slow
def test_slow():
    pass
```

Run specific markers:
```bash
pytest -m unit        # Run only unit tests
pytest -m playwright  # Run only Playwright tests
pytest -m "not slow"  # Skip slow tests
```

## Troubleshooting

### Common Issues

#### 1. Playwright browser not found

```bash
# Install Playwright browsers
playwright install chromium
```

#### 2. Flask app not starting for E2E tests

```bash
# Check if port 5000 is already in use
lsof -i :5000

# Kill the process using port 5000
kill -9 <PID>

# Or use a different port in tests
export FLASK_PORT=5001
```

#### 3. Tests fail with import errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install -r requirements-test.txt

# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 4. Database errors in tests

```bash
# Create fresh test database
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### 5. GitHub API rate limit in tests

```bash
# Set GITHUB_TOKEN environment variable
export GITHUB_TOKEN=your_token_here

# Or create .env file with token
echo "GITHUB_TOKEN=your_token" >> .env
```

### Debugging Tests

#### Unit Tests

```bash
# Run with verbose output and show locals
pytest tests/test_github_pr.py -vv --showlocals

# Drop into debugger on failure
pytest tests/test_github_pr.py --pdb

# Run single test with print statements visible
pytest tests/test_github_pr.py::test_name -s
```

#### Playwright Tests

```bash
# Run with headed browser and slow motion
pytest tests/playwright/ --headed --slowmo 1000

# Take screenshots on failure
pytest tests/playwright/ --screenshot on

# Record videos
pytest tests/playwright/ --video on

# Enable Playwright debug mode
PWDEBUG=1 pytest tests/playwright/
```

### Getting Help

- Check test output for detailed error messages
- Review the test code and documentation
- Check GitHub Actions logs for CI failures
- Consult Playwright documentation: https://playwright.dev/python/
- Consult pytest documentation: https://docs.pytest.org/

## Test Coverage

View test coverage:

```bash
# Generate HTML coverage report
pytest tests/test_*.py --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html
```

Target coverage: 80%+ for new code

## Continuous Improvement

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests pass locally before pushing
3. Check CI test results
4. Add tests to cover edge cases
5. Update this documentation if needed

## Test Data

For Playwright tests, use these test resources:
- Test PR URL: `https://github.com/nsuberi/snippet-manager-starter/pull/1`
- Test user: Create in fixtures or use existing test account
- Test challenges: Seed test database with sample challenges

## Performance

- Unit tests should complete in < 5 seconds
- Playwright tests may take 30-60 seconds each
- Use `--lf` flag to run only last failed tests
- Use `-k` flag to run tests matching pattern
- Use `-x` flag to stop on first failure

```bash
# Run only last failed tests
pytest --lf

# Run tests matching pattern
pytest -k "test_pr"

# Stop on first failure
pytest -x
```
