# Financial Trading Platform Chatbot

A production-ready agentic chatbot for financial trading operations with RAG, multi-agent orchestration, tool integration, and comprehensive monitoring.

## 🚀 Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/GayanSanjeewaGitHub/trade_system.git
cd trade_system

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Start backend with Docker
cd docker
docker-compose up -d
cd ..

# 4. Test backend
curl http://localhost:8000/health

# 5. Run frontend (optional)
cd frontend
.\START.bat

# 6. Run evaluation
python eval_client_simple.py --limit 5
```

Access:
- **Backend API**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501
- **Langfuse**: http://localhost:3000

## 🏗️ Architecture

```
trading-chatbot/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Configuration management
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── controller.py          # Main controller agent
│   │   ├── faq_agent.py           # FAQ retrieval agent
│   │   └── advisor_agent.py       # Trading advisor agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── stock_tools.py         # Stock price & trading tools
│   │   ├── budget_tools.py        # Budget calculation tools
│   │   └── mcp_tools.py           # MCP-based tools
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py           # Document ingestion pipeline
│   │   └── retriever.py           # RAG retriever
│   ├── guardrails/
│   │   ├── __init__.py
│   │   └── validators.py          # Safety & validation layer
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── evaluator.py           # Auto-evaluation script
│   │   └── logger.py              # Logging utilities
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   └── utils/
│       ├── __init__.py
│       └── helpers.py             # Utility functions
├── data/
│   ├── documents/                 # FAQ, policies, product info
│   │   ├── faq.txt
│   │   ├── policies.txt
│   │   └── product_info.txt
│   └── ground_truth/              # Evaluation datasets
│       └── test_qa_pairs.json
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_guardrails.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── .env.example
├── .gitignore
├── pyproject.toml                 # UV package management
├── requirements.txt
└── README.md
```

## 🚀 Features

### 1. **RAG (Retrieval Augmented Generation)**
- Document ingestion from FAQs, policies, and product information
- Pinecone vector database for semantic search
- Contextual retrieval for accurate answers

### 2. **Multi-Agent Orchestration**
- **Controller Agent**: Main orchestrator delegating tasks
- **FAQ Agent**: Handles factual questions using RAG
- **Advisor Agent**: Provides trading advice and executes actions

### 3. **Tools Integration**
- `get_stock_price()`: Fetch real-time stock prices (mocked)
- `execute_trade()`: Buy/sell shares
- `calculate_budget()`: Portfolio budget analysis
- `get_portfolio()`: View current holdings
- **MCP Tool**: Model Context Protocol integration for advanced operations

### 4. **Guardrails**
- Content filtering for inappropriate requests
- Trade limit validation (max transaction size)
- Restricted topic detection
- Input sanitization

### 5. **Monitoring & Evaluation**
- Langfuse integration for tracing
- Auto-evaluation against ground-truth QA pairs
- Metrics: precision, recall, latency, tool usage
- Conversation logging and analytics dashboard

## 📋 Prerequisites

- Python 3.14+
- Docker & Docker Compose
- UV package manager
- Pinecone account
- OpenAI API key (or other LLM provider)
- Langfuse account

## 🛠️ Installation

### 1. Clone the repository
```powershell
git clone https://github.com/GayanSanjeewaGitHub/trade_system.git
cd trade_system
```

### 2. Install UV (if not installed)
```powershell
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create virtual environment and install dependencies
```powershell
# Create virtual environment
uv venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 4. Set up environment variables
```powershell
# Copy example env file
cp .env.example .env

# Edit .env with your credentials (use notepad, VS Code, or any editor)
notepad .env
```

### 5. Start infrastructure with Docker
```powershell
cd docker
docker-compose up -d
cd ..
```

### 6. Verify Installation
```powershell
# Check backend health
curl http://localhost:8000/health

# Or in PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.7

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=trading-chatbot-index

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Application Configuration
APP_NAME=TradingChatbot
APP_VERSION=1.0.0
LOG_LEVEL=INFO
ENVIRONMENT=production

# Guardrails Configuration
MAX_TRADE_AMOUNT=100000
MIN_TRADE_AMOUNT=1
RESTRICTED_TOPICS=illegal,violence,hate

# Agent Keywords (CSV format)
ADVISOR_KEYWORDS=trading,trade,buy,sell,stock,price,portfolio,shares,investment,market,execute,purchase,advisor,recommend,suggest,should I,analysis,budget
FAQ_KEYWORDS=what,how,when,where,who,explain,define,meaning,information,about,details,tell me,describe,CSE,Colombo Stock Exchange,account,register,fees,charges,commission,requirements,documents,process,procedure,steps,rules,regulations,policies,terms,conditions,hours,time,contact,support,help,mobile app,download,install,benefits,features,types,products,services,securities,bonds,debentures,treasury,index,ASPI,S&P,history,established,founded,location,address,phone,email,eligible,qualify,open account,close account,minimum,maximum,deposit,withdrawal,transfer,settlement,clearing,trading days,holidays,suspension,halt,circuit breaker,price band,tick size,lot size,board,diri savi,odd lot,voting,dividends,rights,bonus,IPO,corporate actions,announcements,disclosures,financial statements,annual report,prospectus

# MCP Configuration (Optional)
MCP_SERVER_URL=http://localhost:8001
MCP_TIMEOUT=30

# RAG Configuration
SIMILARITY_THRESHOLD=0.5
CHUNK_SIZE=200
CHUNK_OVERLAP=50
```

### Key Configuration Notes:

1. **API Keys**: Get your keys from:
   - OpenAI: https://platform.openai.com/api-keys
   - Pinecone: https://app.pinecone.io/
   - Langfuse: https://cloud.langfuse.com/

2. **Agent Keywords**: Configure which keywords route to which agent (CSV format)

3. **Similarity Threshold**: Controls RAG retrieval sensitivity (0.0-1.0, default 0.5)

4. **Environment**: Set to `development` for local testing, `production` for deployment

## 🏃 Running the Application

### Option 1: Docker (Recommended)
```powershell
# Start all services (backend + dependencies)
cd docker
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Option 2: Development Mode (Local)
```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Frontend (Streamlit)
```powershell
cd frontend

# Using batch file
.\START.bat

# Or using PowerShell
.\Start-Streamlit.ps1

# Or manually
streamlit run app.py
```

### Access Points
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501
- **Langfuse**: http://localhost:3000 (if running locally)

## 📝 API Endpoints

### Health Check
```powershell
# Using curl
curl http://localhost:8000/health

# Using PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

### Chat
```powershell
# Using curl
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{\"message\": \"What is the current price of AAPL?\", \"session_id\": \"optional-session-id\", \"user_id\": \"optional-user-id\"}'

# Using PowerShell
$body = @{
    message = "What is the current price of AAPL?"
    session_id = "session-123"
    user_id = "user-456"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"
```

### Ingest Documents
```powershell
# Using curl
curl -X POST http://localhost:8000/ingest -F "file=@document.pdf" -F "document_type=faq"

# Using PowerShell
$form = @{
    file = Get-Item -Path "document.pdf"
    document_type = "faq"
}

Invoke-RestMethod -Uri http://localhost:8000/ingest -Method POST -Form $form
```

### Ground Truth Evaluation
```powershell
# Run evaluation with limit
curl http://localhost:8000/evaluate/groundtruth?limit=5

# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/evaluate/groundtruth?limit=5"

# Full evaluation
curl http://localhost:8000/evaluate/groundtruth
```

### Get Metrics
```powershell
# Using curl
curl http://localhost:8000/metrics?session_id=session-123

# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/metrics?session_id=session-123"
```

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

## 💡 Common Workflows

### Daily Development Workflow
```powershell
# 1. Start backend
cd docker
docker-compose up -d
cd ..

# 2. Start frontend
cd frontend
.\START.bat

# 3. View logs (in separate terminal)
cd docker
docker-compose logs -f app
```

### Testing Changes
```powershell
# 1. Make code changes
# 2. Rebuild Docker image
cd docker
docker-compose up --build app -d

# 3. Run tests
cd ..
pytest tests/ -v

# 4. Run evaluation
python eval_client_simple.py --limit 5
```

### Adding New Documents
```powershell
# 1. Place document in src/data/ folder
# 2. Restart backend to auto-ingest
cd docker
docker-compose restart app

# 3. Or use API to ingest
curl -X POST http://localhost:8000/ingest -F "file=@mydoc.txt" -F "document_type=faq"
```

### Debugging Issues
```powershell
# 1. Check backend logs
cd docker
docker-compose logs -f app

# 2. Check backend health
curl http://localhost:8000/health

# 3. Test specific endpoint
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{\"message\": \"test\"}'

# 4. View Langfuse traces
# Open http://localhost:3000 in browser
```

### Deploying to Production
```powershell
# 1. Update .env with production credentials
# 2. Build production Docker image
docker build -f docker/Dockerfile -t trading-chatbot:latest .

# 3. Push to registry
docker tag trading-chatbot:latest your-registry/trading-chatbot:latest
docker push your-registry/trading-chatbot:latest

# 4. Deploy using docker-compose
docker-compose -f docker/docker-compose.yml up -d
```

## 🧪 Testing

### Run All Tests
```powershell
pytest tests/ -v --cov=src
```

### Run Specific Test File
```powershell
pytest tests/test_agents.py -v
```

### Run With Coverage Report
```powershell
pytest --cov=src --cov-report=html

# View coverage report
start htmlcov/index.html
```

### Quick Manual Testing

#### Test Chat Endpoint
```powershell
# Using curl
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{\"message\": \"What is CSE?\", \"session_id\": \"test-123\"}'

# Using PowerShell
$body = @{
    message = "What is the Colombo Stock Exchange?"
    session_id = "test-123"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat -Method POST -Body $body -ContentType "application/json"
```

#### Test Health Endpoint
```powershell
curl http://localhost:8000/health

# Or
Invoke-WebRequest http://localhost:8000/health
```

## 📊 Monitoring & Evaluation

### Run Ground Truth Evaluation

#### Quick Test (5 cases)
```powershell
python eval_client_simple.py --limit 5
```

#### Medium Test (10 cases)
```powershell
python eval_client_simple.py --limit 10
```

#### Full Evaluation (31 cases)
```powershell
python eval_client_simple.py
```

#### Save Results to JSON
```powershell
python eval_client_simple.py --save
```

#### Interactive Menu (PowerShell)
```powershell
.\run_eval.ps1
```

Then select:
- `1` for Quick Test (5 cases)
- `2` for Medium Test (10 cases)
- `3` for Full Evaluation (31 cases)

#### Using Batch File
```cmd
run_eval.bat
```

### Evaluation Results

The evaluation system will show:
- **Overall Performance**: Total tests, pass rate, failed tests
- **Quality Metrics**: Average similarity score, latency
- **Category Breakdown**: Results by category (FAQ, Organization, Regulations)
- **Detailed Results**: Individual test results with scores

Sample output:
```
================================================================================
📊 SUMMARY
================================================================================

Overall Performance:
  • Total Tests: 31
  • Passed: 29
  • Failed: 2
  • Pass Rate: 93.5%

Quality Metrics:
  • Avg Similarity: 0.8745
  • Avg Latency: 8234.12 ms

Category Breakdown:
  • FAQ: 20/21 (95.2%)
  • ORGANIZATION: 7/8 (87.5%)
  • REGULATIONS: 2/2 (100.0%)
```

### View Langfuse Traces
1. Navigate to Langfuse dashboard (http://localhost:3000)
2. View conversation traces with tool calls
3. Analyze latency and performance metrics

### API-Based Evaluation
```bash
# Via API endpoint
curl http://localhost:8000/evaluate/groundtruth?limit=5
```

### Evaluation Files
- `eval_client_simple.py` - Python client (no external dependencies required)
- `eval_client.py` - Alternative client (requires `requests` library)
- `run_eval.ps1` - PowerShell interactive runner
- `run_eval.bat` - Windows batch runner
- `EVALUATION_FIXED.md` - Detailed evaluation documentation

## 🐳 Docker Commands

### Start All Services
```powershell
cd docker
docker-compose up -d
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service (backend app)
docker-compose logs -f app

# Specific service (Langfuse)
docker-compose logs -f langfuse
```

### Stop Services
```powershell
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Rebuild Services
```powershell
# Rebuild all services
docker-compose up --build -d

# Rebuild specific service
docker-compose up --build app -d
```

### Check Service Status
```powershell
docker-compose ps
```

### Restart Services
```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
```

### Clean Up Docker
```powershell
# Remove unused containers, networks, images
docker system prune -a

# Remove all stopped containers
docker container prune

# Remove unused volumes
docker volume prune
```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Use secrets management in production
3. **Input Validation**: All inputs are sanitized through Pydantic models
4. **Rate Limiting**: Implemented at API level
5. **Content Filtering**: Guardrails prevent malicious queries

## 📈 Performance Optimization

1. **Caching**: Redis for frequent queries (configured in Docker)
2. **Async Operations**: All I/O operations are async
3. **Connection Pooling**: Database connections are pooled
4. **Batch Processing**: Document ingestion uses batching
5. **Vector Index**: Optimized Pinecone index configuration
6. **Parallel Keyword Matching**: 5-10x faster intent classification using ThreadPoolExecutor

## 📦 Package Management

This project uses **UV** for fast, reliable dependency management.

### Adding New Packages
```powershell
# Add single package
uv add package-name

# Add multiple packages
uv add "packageA" "packageB"

# Add dev dependency
uv add --dev pytest

# Add with version constraint
uv add "fastapi>=0.100.0"
```

### Updating Dependencies
```powershell
# Update all packages
uv sync

# Update specific package
uv add --upgrade package-name

# Update pyproject.toml and lock file
uv lock
```

### Removing Packages
```powershell
uv remove package-name
```

### Installing from requirements.txt
```powershell
uv pip install -r requirements.txt
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Backend Not Starting

```powershell
# Check Docker services
cd docker
docker-compose ps

# View logs
docker-compose logs app

# Restart services
docker-compose restart app
```

### Pinecone Connection Issues
```powershell
# Test Pinecone connection
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='YOUR_KEY'); print(pc.list_indexes())"

# Check environment variables
cat .env | Select-String PINECONE
```

### Langfuse Integration Issues
```powershell
# Check Langfuse connectivity
curl -X GET "https://cloud.langfuse.com/api/public/health"

# Check local Langfuse
curl http://localhost:3000
```

### Docker Issues
```powershell
# Clean up Docker
docker system prune -a

# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up --build -d
```

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### Evaluation Script Issues
```powershell
# Make sure backend is running
curl http://localhost:8000/health

# Test with single case
python eval_client_simple.py --limit 1

# Check Python version
python --version

# Should be Python 3.10 or higher
```

### Module Not Found Errors
```powershell
# Reinstall dependencies
uv pip install -r requirements.txt

# Or install specific package
uv pip install <package-name>
```

### Database Connection Issues
```powershell
# Check PostgreSQL
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Check Redis
docker-compose logs redis
```

## 📞 Support

For issues and questions:
- Create an issue on GitHub: https://github.com/GayanSanjeewaGitHub/trade_system/issues
- Check documentation: See `EVALUATION_FIXED.md` for evaluation details
- View API docs: http://localhost:8000/docs

## 📚 Additional Documentation

- `EVALUATION_FIXED.md` - Complete evaluation system guide
- `EVAL_QUICKSTART.md` - Quick start guide for evaluations
- `setup.md` - Detailed setup instructions
- `docker/READ.md` - Docker configuration details
- `frontend/README.md` - Frontend-specific documentation
- `frontend/UV_SETUP.md` - UV package manager setup

## 🎯 Command Reference

### Quick Commands
```powershell
# Start everything
cd docker && docker-compose up -d && cd ..

# Stop everything
cd docker && docker-compose down && cd ..

# View logs
cd docker && docker-compose logs -f app

# Run evaluation
python eval_client_simple.py --limit 5

# Test chat
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{\"message\": \"What is CSE?\"}'

# Check health
curl http://localhost:8000/health

# Run tests
pytest tests/ -v

# Start frontend
cd frontend && .\START.bat
```

### PowerShell Aliases (Optional)
Add these to your PowerShell profile for convenience:
```powershell
# Open PowerShell profile
notepad $PROFILE

# Add these functions
function Start-TradingBackend { cd docker; docker-compose up -d; cd .. }
function Stop-TradingBackend { cd docker; docker-compose down; cd .. }
function View-TradingLogs { cd docker; docker-compose logs -f app; cd .. }
function Test-TradingEval { python eval_client_simple.py --limit 5 }
function Start-TradingFrontend { cd frontend; .\START.bat; cd .. }

# Use as:
# Start-TradingBackend
# Stop-TradingBackend
# View-TradingLogs
# Test-TradingEval
# Start-TradingFrontend
```

---

**Built with ❤️ using FastAPI, LangGraph, Pinecone, and Langfuse**