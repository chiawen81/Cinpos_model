# Python Package Management with uv

Use uv exclusively for Python package management in this project.

## Virtual Environment
This project uses uv virtual environment located at `.venv/`

### Activating Virtual Environment
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

### Deactivating Virtual Environment
```bash
deactivate
```

## Package Management Commands
- All Python dependencies **must be installed, synchronized, and locked** using uv
- Never use pip, pip-tools, poetry, or conda directly for dependency management

Use these commands:
- Install dependencies: `uv add <package>`
- Remove dependencies: `uv remove <package>`
- Sync dependencies: `uv sync`
- Install all dependencies from pyproject.toml: `uv sync`

## Running Python Code
- Run a Python script with `uv run <script-name>.py`
- Run Python tools like Pytest with `uv run pytest` or `uv run ruff`
- Launch a Python repl with `uv run python`
- Run commands in virtual environment: `uv run <command>`

## Important Notes
- Always use `uv run` to execute Python scripts, which automatically uses the virtual environment
- No need to manually activate the virtual environment when using `uv run`
- The virtual environment is automatically created when running `uv sync`