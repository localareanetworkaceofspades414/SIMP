# Code Quality & Formatting Guide

This document explains how to maintain code quality for the SIMP Protocol project.

## Quick Start

### Install Development Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Format Code with Black

```bash
# Format all Python files
black simp/ tests/ bin/ --line-length=120

# Check formatting without modifying
black --check simp/ tests/ bin/ --line-length=120
```

### Lint with Flake8

```bash
# Check for style issues
flake8 simp/ tests/ bin/

# See configuration in .flake8
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=simp --cov-report=html

# Run protocol validation
python3 bin/test_protocol.py
```

### Type Checking with mypy

```bash
# Check types
mypy simp/

# See configuration in pyproject.toml
```

---

## Code Standards

### Style Guide

- **Line length:** 120 characters (see `.flake8` and `pyproject.toml`)
- **Formatter:** Black (automatic)
- **Linter:** Flake8 (automatic)
- **Type hints:** Python 3.9+ (strongly encouraged)

### Docstring Format

All functions should have docstrings following this format:

```python
def route_intent(
    self,
    intent_id: str,
    source_agent: str,
    target_agent: str,
    intent_type: str,
    payload: Dict[str, Any]
) -> bool:
    """
    Route an intent to the target agent.

    Args:
        intent_id: Unique identifier for the intent
        source_agent: ID of agent sending the intent
        target_agent: ID of agent to receive the intent
        intent_type: Type/handler name for the intent
        payload: Intent data payload

    Returns:
        True if successfully routed, False otherwise

    Raises:
        ValueError: If target agent not found
        TimeoutError: If agent doesn't respond in time
    """
```

### Type Hints

```python
from typing import Dict, List, Optional, Any, Callable

def example(
    agent_id: str,
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """Example function with type hints"""
    pass
```

### Class Docstrings

```python
class SimpBroker:
    """
    SIMP Protocol Broker.

    Central message router for inter-agent communication.
    Manages agent registration, intent routing, and response handling.

    Attributes:
        config: Broker configuration
        agents: Registry of connected agents
        intent_records: History of intents and responses
        stats: Performance statistics
    """
```

---

## CI/CD Workflow

### GitHub Actions

Tests run automatically on every push and pull request.

**Workflow:** `.github/workflows/tests.yml`

**Runs:**
1. Flake8 linting (warnings don't block)
2. Black formatting check (warnings don't block)
3. Pytest test suite
4. Protocol validation
5. Coverage report

### Local Testing Before Push

```bash
# Run all checks locally
flake8 simp/ tests/ bin/
black --check simp/ tests/ bin/
pytest tests/ -v
python3 bin/test_protocol.py
```

---

## Pre-commit Hook (Optional)

To automatically format code before committing:

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
black simp/ tests/ bin/ --line-length=120
pytest tests/ -q
EOF

chmod +x .git/hooks/pre-commit
```

---

## Editor Setup

### VS Code

Install extensions:
- Python (Microsoft)
- Pylance
- Black Formatter

`.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=120"],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=120"],
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

### PyCharm

Settings → Editor → Code Style → Python:
- Scheme: `Black`
- Line length: `120`

---

## Common Issues

### Import Sorting

Use `isort` to organize imports:

```bash
pip install isort
isort simp/ tests/ bin/
```

### Type Checking Errors

If `mypy` reports issues, either:
1. Add type hints to fix
2. Add type: ignore comment if unavoidable

```python
value = some_untyped_function()  # type: ignore
```

### Formatting Conflicts

If Black conflicts with flake8, Black takes precedence. The `.flake8` config ignores common Black formatting rules:

```
ignore = E203, E501, W503
```

---

## Contributing Code

Before submitting a PR:

1. **Format code**
   ```bash
   black simp/ tests/ bin/ --line-length=120
   ```

2. **Check linting**
   ```bash
   flake8 simp/ tests/ bin/
   ```

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Verify protocol**
   ```bash
   python3 bin/test_protocol.py
   ```

5. **Check coverage** (optional)
   ```bash
   pytest tests/ --cov=simp --cov-report=html
   open htmlcov/index.html
   ```

---

## Questions?

- See `.flake8` for linting rules
- See `pyproject.toml` for Black/pytest/mypy configuration
- See `.github/workflows/tests.yml` for CI/CD pipeline
- Check existing code for style examples

---

**Last Updated:** April 2, 2026
**Status:** Ready for launch
