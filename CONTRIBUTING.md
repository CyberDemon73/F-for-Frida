# Contributing to F-for-Frida

First off, thank you for considering contributing to F-for-Frida! It's people like you that make this tool better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct: be respectful, inclusive, and constructive.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

**When reporting a bug, include:**
- Python version (`python --version`)
- OS and version
- ADB version (`adb --version`)
- Device information (model, Android version)
- Complete error message/traceback
- Steps to reproduce

### 💡 Suggesting Features

Feature requests are welcome! Please provide:
- Clear description of the feature
- Use case / why it's needed
- Possible implementation approach (optional)

### 🔧 Pull Requests

1. **Fork** the repo and create your branch from `main`
2. **Install** development dependencies: `pip install -e ".[dev]"`
3. **Write** tests for your changes
4. **Ensure** tests pass: `pytest`
5. **Format** code: `black f_for_frida/`
6. **Lint** code: `flake8 f_for_frida/`
7. **Update** documentation if needed
8. **Submit** your PR

### Coding Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small
- Add comments for complex logic

### Commit Messages

Use clear, descriptive commit messages:
- `feat: add support for wireless ADB`
- `fix: handle timeout in device detection`
- `docs: update installation instructions`
- `refactor: simplify frida manager logic`

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/F-for-Frida.git
cd F-for-Frida

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black f_for_frida/

# Type checking
mypy f_for_frida/
```

## Questions?

Feel free to open an issue for any questions!
