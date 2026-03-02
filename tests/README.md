# RecallEngine Test Suite

This directory contains comprehensive tests for the RecallEngine project.

## Test Structure

```
tests/
├── __init__.py                    # Package marker
├── conftest.py                    # Shared pytest fixtures
├── test_keyword_search_cli.py     # Unit tests for keyword_search_cli module
├── test_misc.py                   # Unit tests for misc module
└── test_integration.py            # Integration and end-to-end tests
```

## Test Coverage

### Unit Tests

#### test_keyword_search_cli.py
- **TestTokensStemmer**: Tests the Porter Stemming functionality
  - Basic stemming of words to root forms
  - Handling of duplicates
  - Edge cases (empty lists, already-stemmed words)

- **TestCleanPunctuation**: Tests punctuation removal
  - Common punctuation marks
  - Special characters
  - Empty strings

- **TestRemoveStopWords**: Tests stop word filtering
  - Removal of common words
  - Handling when all tokens are stop words
  - Edge cases

- **TestStandardizeTexts**: Tests the full normalization pipeline
  - Complete text processing workflow
  - Complex sentences
  - Empty strings

- **TestMatchKeyword**: Tests keyword matching
  - Exact matches
  - Substring matches
  - Case-insensitive matching

#### test_misc.py
- **TestGetStopWords**: Tests stop word file loading
  - Successful file reads
  - Error handling (file not found, permissions)
  - Whitespace handling

- **TestDatasetLoader**: Tests dataset file loading
  - Various file types
  - Error handling
  - Large files

### Integration Tests

#### test_integration.py
- **TestEndToEndSearch**: Complete search workflow tests
  - Successful searches with results
  - Searches with no matches
  - Invalid commands
  - Help command

- **TestSearchWorkflow**: Component integration tests
  - Query normalization pipeline
  - Title matching logic
  - Multiple movie searches

- **TestEdgeCases**: Boundary condition tests
  - Empty queries
  - Special characters
  - Unicode handling
  - Very long queries

- **TestDataIntegrity**: Data handling tests
  - Malformed JSON
  - Missing keys
  - Empty datasets

## Running Tests

### Install Test Dependencies

```bash
# Using poetry
poetry install --with dev

# Or using pip
pip install pytest pytest-cov
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=recall_engine --cov-report=html

# Run with detailed output
pytest -vv
```

### Run Specific Test Files

```bash
# Run only unit tests for keyword_search_cli
pytest tests/test_keyword_search_cli.py

# Run only misc module tests
pytest tests/test_misc.py

# Run only integration tests
pytest tests/test_integration.py
```

### Run Specific Test Classes

```bash
# Run specific test class
pytest tests/test_keyword_search_cli.py::TestTokensStemmer

# Run specific test method
pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_basic_stemming
```

### Run Tests with Pattern Matching

```bash
# Run tests matching a pattern
pytest -k "stemmer"

# Run tests NOT matching a pattern
pytest -k "not integration"
```

## Test Output

### Successful Run
```
======================== test session starts ========================
collected 45 items

tests/test_keyword_search_cli.py ................           [ 35%]
tests/test_misc.py ............                              [ 62%]
tests/test_integration.py .................                 [100%]

======================== 45 passed in 2.34s =========================
```

### With Coverage
```bash
pytest --cov=recall_engine --cov-report=term-missing
```

This will show which lines are not covered by tests.

## Writing New Tests

### Test Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure

```python
import pytest
from unittest.mock import patch

class TestNewFeature:
    """Test description."""
    
    def test_basic_functionality(self):
        """Test basic use case."""
        # Arrange
        input_data = "test"
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == expected_output
    
    @patch('module.dependency')
    def test_with_mock(self, mock_dependency):
        """Test with mocked dependencies."""
        mock_dependency.return_value = "mocked"
        result = function_to_test()
        assert result == "expected"
```

## Continuous Integration

These tests are designed to be run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install poetry
      - run: poetry install --with dev
      - run: poetry run pytest --cov
```

## Troubleshooting

### Import Errors
If you encounter import errors, ensure the project is installed:
```bash
poetry install
```

### Missing Dependencies
Install test dependencies:
```bash
poetry install --with dev
```

### Path Issues
The tests use `sys.path` manipulation to import modules. If you encounter path issues, run tests from the project root.

## Contributing

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure all tests pass
3. Maintain >80% code coverage
4. Add descriptive docstrings to tests
