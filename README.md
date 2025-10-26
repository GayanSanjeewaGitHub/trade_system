# Financial Trading Platform Chatbot

A production-ready agentic chatbot for financial trading operations with RAG, multi-agent orchestration, tool integration, and comprehensive monitoring.

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
```bash
git clone <repository-url>
cd trading-chatbot
```

### 2. Install UV (if not installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create virtual environment and install dependencies
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Start infrastructure with Docker
```bash
cd docker
docker-compose up -d
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

# MCP Configuration
MCP_SERVER_URL=http://localhost:8001
MCP_TIMEOUT=30
```

## 🏃 Running the Application

### Development Mode
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode (Docker)
```bash
docker-compose up --build
```

### Access Points
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Langfuse**: http://localhost:3000 (if running locally)

## 📝 API Endpoints

### Health Check
```bash
GET /health
```

### Chat
```bash
POST /chat
Content-Type: application/json

{
  "message": "What is the current price of AAPL?",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

### Ingest Documents
```bash
POST /ingest
Content-Type: multipart/form-data

file: <document.pdf>
document_type: faq
```

### Evaluation
```bash
POST /evaluate
Content-Type: application/json

{
  "test_cases": [
    {
      "question": "What is the trading fee?",
      "expected_answer": "The trading fee is 0.1% per transaction"
    }
  ]
}
```

### Get Metrics
```bash
GET /metrics?session_id=<session_id>
```

## 🧪 Testing

### Run all tests
```bash
pytest tests/ -v --cov=src
```

### Run specific test file
```bash
pytest tests/test_agents.py -v
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

## 📊 Monitoring & Evaluation

### View Langfuse Traces
1. Navigate to Langfuse dashboard
2. View conversation traces with tool calls
3. Analyze latency and performance metrics

### Run Auto-Evaluation
```bash
python -m src.monitoring.evaluator
```

Evaluation metrics include:
- **Precision**: Accuracy of retrieved information
- **Recall**: Coverage of expected information
- **Latency**: Response time per query
- **Tool Usage**: Frequency and success rate of tool calls

## 🐳 Docker Commands

### Build and start services
```bash
docker-compose up --build -d
```

### View logs
```bash
docker-compose logs -f app
```

### Stop services
```bash
docker-compose down
```

### Rebuild specific service
```bash
docker-compose up --build app
```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Use secrets management in production
3. **Input Validation**: All inputs are sanitized through Pydantic models
4. **Rate Limiting**: Implemented at API level
5. **Content Filtering**: Guardrails prevent malicious queries

## 📈 Performance Optimization

1. **Caching**: Implement Redis for frequent queries
2. **Async Operations**: All I/O operations are async
3. **Connection Pooling**: Database connections are pooled
4. **Batch Processing**: Document ingestion uses batching
5. **Vector Index**: Optimized Pinecone index configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Pinecone Connection Issues
```bash
# Verify API key
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='YOUR_KEY'); print(pc.list_indexes())"
```

### Langfuse Integration Issues
```bash
# Check Langfuse connectivity
curl -X GET "https://cloud.langfuse.com/api/public/health"
```

### Docker Issues
```bash
# Clean up Docker
docker system prune -a
docker-compose down -v
```

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact: support@tradingchatbot.com

---

**Built with ❤️ using FastAPI, LangGraph, Pinecone, and Langfuse**

uv add "packageA" "packageB"

 
docker build -f docker/Dockerfile -t trading-chatbot .
.\START.bat