# PyCode Test Suite

Comprehensive test suite for PyCode features using pytest.

## Running Tests

### Install test dependencies
```bash
pip install -r requirements-test.txt
```

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_logging.py
pytest tests/test_retry.py
pytest tests/test_tool_validation.py
pytest tests/test_provider_aliases.py
```

### Run with coverage
```bash
pytest --cov=src/pycode --cov-report=html
```

### Run async tests only
```bash
pytest -m asyncio
```

## Test Structure

- `test_logging.py` - Tests for structured logging system
  - PyCodeLogger class
  - Log levels (quiet, normal, verbose, debug)
  - Contextual logging
  - File logging
  - Global logger instance

- `test_retry.py` - Tests for retry logic with exponential backoff
  - Retry decorator
  - Retry strategies (api_call, network, quick)
  - RetryContext for manual control
  - Exponential backoff timing
  - Exception handling

- `test_tool_validation.py` - Tests for tool parameter validation
  - ToolParameterValidator class
  - Required field validation
  - Type checking
  - Numeric range validation
  - String pattern validation
  - Enum validation
  - Standard tool schemas (write, read, edit, bash, grep, glob)

- `test_provider_aliases.py` - Tests for provider and model aliases
  - ProviderResolver class
  - Provider alias resolution
  - Model alias resolution
  - Provider inference from model names
  - Default models
  - Alias listings

## Test Coverage

Target coverage: 80%+

Areas covered:
- ✅ Logging system
- ✅ Retry logic
- ✅ Tool validation
- ✅ Provider aliases
- ⏳ CLI commands (TODO)
- ⏳ Config management (TODO)
- ⏳ Session management (TODO)
- ⏳ Integration tests (TODO)

## Writing Tests

### Fixtures

Available fixtures (defined in `conftest.py`):
- `temp_dir` - Temporary directory for file operations
- `temp_file` - Create temporary files

### Example Test

```python
import pytest

def test_example():
    \"\"\"Test example functionality\"\"\"
    assert True

@pytest.mark.asyncio
async def test_async_example():
    \"\"\"Test async functionality\"\"\"
    result = await some_async_function()
    assert result == expected

def test_with_temp_file(temp_file):
    \"\"\"Test using temp file fixture\"\"\"
    file_path = temp_file("test.txt", "content")
    assert file_path.exists()
```

## Test Markers

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests (slow)
- `@pytest.mark.unit` - Unit tests (fast)

## CI/CD

These tests are designed to run in CI/CD pipelines:
- Fast execution (<30s for unit tests)
- No external dependencies
- Isolated test environment
- Clear pass/fail criteria
