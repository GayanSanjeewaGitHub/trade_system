"""
All Missing __init__.py Files
"""

# ============================================
# src/models/__init__.py
# ============================================
"""Models module"""

from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    EvaluationRequest,
    EvaluationResponse,
    MetricsResponse,
    HealthResponse,
    IngestResponse,
    TestCase,
    TestResult,
    TradeRequest,
    TradeResult,
    Portfolio,
    PortfolioItem
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "EvaluationRequest",
    "EvaluationResponse",
    "MetricsResponse",
    "HealthResponse",
    "IngestResponse",
    "TestCase",
    "TestResult",
    "TradeRequest",
    "TradeResult",
    "Portfolio",
    "PortfolioItem"
]


# ============================================
# src/rag/__init__.py
# ============================================
"""RAG module - Retrieval Augmented Generation"""

from src.rag.retriever import RAGRetriever
from src.rag.ingestion import DocumentIngestion

__all__ = ["RAGRetriever", "DocumentIngestion"]


# ============================================
# src/guardrails/__init__.py
# ============================================
"""Guardrails module - Input validation and safety"""

from src.guardrails.validators import GuardrailValidator

__all__ = ["GuardrailValidator"]


# ============================================
# src/monitoring/__init__.py
# ============================================
"""Monitoring module - Logging and evaluation"""

from src.monitoring.logger import setup_logging, get_logger
from src.monitoring.evaluator import AutoEvaluator

__all__ = ["setup_logging", "get_logger", "AutoEvaluator"]


# ============================================
# src/utils/__init__.py
# ============================================
"""Utilities module"""

from src.utils.helpers import (
    generate_session_id,
    generate_request_id,
    generate_user_id,
    hash_content,
    truncate_text,
    format_currency,
    calculate_percentage_change
)

__all__ = [
    "generate_session_id",
    "generate_request_id",
    "generate_user_id",
    "hash_content",
    "truncate_text",
    "format_currency",
    "calculate_percentage_change"
]