# UV Environment Setup for Frontend

This guide shows how to set up and use the UV environment for the Trading Chatbot frontend.

## Prerequisites

Make sure UV is installed:
```bash
pip install uv
```

Or on Windows with PowerShell:
```powershell
pip install uv
```

## Setup Instructions

### 1. Initialize UV Environment

From the `frontend` directory:

```bash
cd frontend
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Generate a `uv.lock` file

### 2. Activate the Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 3. Run the Streamlit App

With the environment activated:
```bash
streamlit run app.py
```

Or use UV to run directly without activating:
```bash
uv run streamlit run app.py
```

## Using UV Commands

### Add a new dependency
```bash
uv add package-name
```

### Remove a dependency
```bash
uv remove package-name
```

### Update dependencies
```bash
uv sync --upgrade
```

### Run commands in the UV environment
```bash
uv run <command>
```

Example:
```bash
uv run streamlit run app.py
```

## Quick Start Scripts

### Windows (run_uv.bat)
```batch
.\run_uv.bat
```

### Linux/Mac (run_uv.sh)
```bash
./run_uv.sh
```

## Troubleshooting

### "uv: command not found"
Install UV first:
```bash
pip install uv
```

### Permission denied on scripts
**Linux/Mac:**
```bash
chmod +x run_uv.sh
```

**Windows:** Run PowerShell as Administrator if you encounter execution policy issues.

### Virtual environment issues
Remove and recreate:
```bash
rm -rf .venv
uv sync
```

## Project Structure

```
frontend/
├── .venv/              # Virtual environment (created by uv sync)
├── pyproject.toml      # Project configuration and dependencies
├── uv.lock            # Locked dependency versions (created by uv sync)
├── app.py             # Main Streamlit application
├── requirements.txt    # Alternative pip requirements (for non-uv setups)
└── README.md          # Documentation
```

## Benefits of Using UV

- ⚡ **Fast**: Much faster than pip for dependency resolution
- 🔒 **Reliable**: Lock file ensures reproducible installations
- 🎯 **Simple**: Modern Python packaging standard
- 🔄 **Compatible**: Works with standard Python packaging tools
