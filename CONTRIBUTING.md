# Contributing to claude-learn

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/mofeed28/claude-learn.git
cd claude-learn

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest scraper/tests/ -v

# Run with coverage
pytest scraper/tests/ -v --cov=scraper --cov-report=term-missing

# Run specific test file
pytest scraper/tests/test_fetcher.py -v

# Run security tests only
pytest scraper/tests/ -v -m security
```

## Linting & Formatting

```bash
# Check lint errors
ruff check scraper/

# Auto-fix lint errors
ruff check scraper/ --fix

# Check formatting
ruff format --check scraper/

# Auto-format
ruff format scraper/

# Type checking
mypy scraper/
```

## Pull Request Process

1. Fork the repository and create a feature branch from `master`
2. Make your changes with tests
3. Ensure all checks pass: `pytest`, `ruff check`, `ruff format --check`, `mypy`
4. Write a clear PR description using the template
5. Submit the PR

## Code Style

- Follow existing patterns in the codebase
- Use type hints for all function signatures
- Keep functions focused and small
- Write tests for new functionality

## Reporting Issues

Use the GitHub issue templates for bug reports and feature requests.
