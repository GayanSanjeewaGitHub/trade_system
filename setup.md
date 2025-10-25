# 🚀 Complete Setup Guide - Trading Chatbot

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.14** (or 3.11+)
- **UV** package manager
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Git**

### Required API Keys
- **OpenAI API Key** - For LLM and embeddings
- **Pinecone API Key** - For vector database
- **Langfuse Keys** - For monitoring (optional but recommended)

---

## Quick Start

### For Linux/Mac:

```bash
# 1. Clone and navigate
cd trading-chatbot

# 2. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# 3. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run setup script
chmod +x run.sh
./run.sh
```

### For Windows:

```batch
# 1. Install UV from: https://github.com/astral-sh/uv

# 2. Setup environment
copy .env.example .env
REM Edit .env with your API keys

# 3. Run setup script
run.bat
```

---

## Detailed Setup

### Step 1: Project Structure

Create the following directory structure:

```
trading-chatbot/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   ├── faq_agent.py
│   │   └── advisor_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── stock_tools.py
│   │   ├── budget_tools.py
│   │   └── mcp_tools.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py
│   │   └── ingestion.py
│   ├── guardrails/
│   │   ├── __init__.py
│   │   └── validators.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── evaluator.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── data/
│   ├── documents/
│   │   ├── faq.txt
│   │   ├── policies.txt
│   │   └── product_info.txt
│   └── ground_truth/
│       └── test_qa_pairs.json
├── tests/
│   ├── __init__.py
│   └── test_agents.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
├── run.sh
└── run.bat
```

### Step 2: Install UV

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

**Windows (PowerShell as Admin):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Verify installation:
```bash
uv --version
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
uv venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
# Install all dependencies
uv pip install -r requirements.txt

# Verify installation
python -c "import langchain; import fastapi; print('Dependencies OK')"
```

### Step 5: Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```env
# Required
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-pinecone-key
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key

# Optional (defaults provided)
LLM_MODEL=gpt-4-turbo-preview
PINECONE_INDEX_NAME=trading-chatbot-index
```

### Step 6: Setup Pinecone

1. Go to [pinecone.io](https://www.pinecone.io)
2. Create a free account
3. Create a new index:
   - **Name**: `trading-chatbot-index`
   - **Dimensions**: `1536`
   - **Metric**: `cosine`
   - **Cloud**: `AWS` or `GCP`
4. Copy your API key to `.env`

### Step 7: Setup Langfuse (Optional)

1. Go to [langfuse.com](https://langfuse.com)
2. Create account
3. Create new project
4. Copy public and secret keys to `.env`

Or run locally with Docker:
```bash
docker-compose -f docker/docker-compose.yml up -d langfuse postgres
```

### Step 8: Create Data Files

Create sample documents in `data/documents/`:

**faq.txt:**
```
Q: What are the trading fees?
A: 0.1% per transaction

Q: What is the minimum deposit?
A: $100 minimum, $500 recommended
```

**policies.txt:**
```
Trading Platform Policies

1. Account Security - 2FA required
2. Trading Hours - 9:30 AM - 4:00 PM ET
3. Fees - 0.1% per stock trade
```

---

## Configuration

### Key Configuration Options

Edit `src/config/settings.py` or `.env`:

```python
# LLM Settings
LLM_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7

# Guardrails
MAX_TRADE_AMOUNT=100000.0
MIN_TRADE_AMOUNT=1.0
RESTRICTED_TOPICS=illegal,violence,hate

# Agent Settings
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT=120
```

---

## Running the Application

### Method 1: Direct Python

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 2: Using Scripts

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```batch
run.bat
```

### Method 3: Docker

```bash
# Build and run
docker-compose -f docker/docker-compose.yml up --build

# Run in background
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f app

# Stop
docker-compose -f docker/docker-compose.yml down
```

### Accessing the Application

Once running:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run Specific Tests

```bash
# Test agents only
pytest tests/test_agents.py -v

# Test specific function
pytest tests/test_agents.py::TestControllerAgent::test_initialization -v
```

### Manual Testing

Test the chat endpoint:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the trading fees?",
    "session_id": "test-123"
  }'
```

Test stock price:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the price of AAPL?",
    "session_id": "test-