"""
FastAPI application entry point for Trading Chatbot.
Handles API routes, middleware, and application lifecycle.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional
import structlog
from fastapi import FastAPI, HTTPException, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config.settings import settings
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    EvaluationRequest,
    EvaluationResponse,
    MetricsResponse,
    HealthResponse,
    IngestResponse
)
from src.agents.controller import ControllerAgent
from src.rag.ingestion import DocumentIngestion
from src.monitoring.evaluator import AutoEvaluator
from src.monitoring.logger import setup_logging, get_logger
from src.utils.helpers import generate_session_id

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global instances
controller_agent: Optional[ControllerAgent] = None
doc_ingestion: Optional[DocumentIngestion] = None
evaluator: Optional[AutoEvaluator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    global controller_agent, doc_ingestion, evaluator
    
    logger.info("Starting Trading Chatbot application", version=settings.app_version)
    
    try:
        # Initialize components
        logger.info("Initializing controller agent")
        controller_agent = ControllerAgent()
        await controller_agent.initialize()
        
        logger.info("Initializing document ingestion")
        doc_ingestion = DocumentIngestion()
        await doc_ingestion.initialize()
        
        logger.info("Initializing auto evaluator")
        evaluator = AutoEvaluator()
        await evaluator.initialize()
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")
    try:
        if controller_agent:
            await controller_agent.cleanup()
        if doc_ingestion:
            await doc_ingestion.cleanup()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Financial Trading Platform Chatbot with RAG and Multi-Agent Orchestration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": generate_session_id()
        }
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
@limiter.limit("10/minute")
async def health_check(request: Request):
    """
    Health check endpoint.
    Returns application status and component health.
    """
    try:
        health_status = {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "components": {
                "controller_agent": controller_agent is not None,
                "document_ingestion": doc_ingestion is not None,
                "evaluator": evaluator is not None,
            }
        }
        
        # Check if all components are initialized
        if not all(health_status["components"].values()):
            health_status["status"] = "degraded"
        
        return HealthResponse(**health_status)
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat(chat_request: ChatRequest, request: Request):
    """
    Main chat endpoint for conversing with the trading chatbot.
    
    Args:
        chat_request: ChatRequest containing message and optional session info
        request: FastAPI Request object for rate limiting
        
    Returns:
        ChatResponse with bot reply and metadata
    """
    if not controller_agent:
        logger.error("Controller agent not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready. Please try again."
        )
    
    # Generate session ID if not provided
    session_id = chat_request.session_id or generate_session_id()
    user_id = chat_request.user_id or "anonymous"
    
    logger.info(
        "Processing chat request",
        session_id=session_id,
        user_id=user_id,
        message_length=len(chat_request.message)
    )
    
    try:
        # Process message through controller agent
        response = await controller_agent.process_message(
            message=chat_request.message,
            session_id=session_id,
            user_id=user_id,
            context=chat_request.context
        )
        
        logger.info(
            "Chat request processed successfully",
            session_id=session_id,
            response_length=len(response.get("response", ""))
        )
        
        return ChatResponse(
            response=response.get("response", ""),
            session_id=session_id,
            metadata=response.get("metadata", {}),
            tools_used=response.get("tools_used", []),
            agent_path=response.get("agent_path", [])
        )
    
    except ValueError as e:
        logger.warning("Invalid request", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Error processing chat", error=str(e), session_id=session_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message. Please try again."
        )


@app.post("/ingest", response_model=IngestResponse, tags=["Documents"])
@limiter.limit("10/minute")
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = "general"
):
    """
    Ingest documents into the RAG system.
    
    Args:
        request: FastAPI Request object for rate limiting
        file: PDF or text file to ingest
        document_type: Type of document (faq, policy, product_info, general)
        
    Returns:
        IngestResponse with ingestion status
    """
    if not doc_ingestion:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document ingestion service not ready"
        )
    
    logger.info("Processing document ingestion", filename=file.filename, type=document_type)
    
    try:
        # Validate file type
        if not any(file.filename.endswith(ext) for ext in settings.allowed_file_types):
            raise ValueError(f"Unsupported file type. Allowed: {settings.allowed_file_types}")
        
        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise ValueError(f"File too large. Max size: {settings.max_file_size} bytes")
        
        # Process document
        result = await doc_ingestion.ingest_document(
            content=content,
            filename=file.filename,
            document_type=document_type
        )
        
        logger.info(
            "Document ingested successfully",
            filename=file.filename,
            chunks=result.get("chunks_created", 0)
        )
        
        return IngestResponse(
            success=True,
            filename=file.filename,
            chunks_created=result.get("chunks_created", 0),
            message="Document ingested successfully"
        )
    
    except ValueError as e:
        logger.warning("Invalid document", error=str(e), filename=file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error("Document ingestion failed", error=str(e), filename=file.filename, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest document"
        )


@app.post("/evaluate", response_model=EvaluationResponse, tags=["Monitoring"])
@limiter.limit("5/minute")
async def evaluate_responses(eval_request: EvaluationRequest, request: Request):
    """
    Evaluate chatbot responses against test cases.
    
    Args:
        eval_request: EvaluationRequest with test cases
        request: FastAPI Request object for rate limiting
        
    Returns:
        EvaluationResponse with metrics
    """
    if not evaluator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation service not ready"
        )
    
    logger.info("Running evaluation", test_cases=len(eval_request.test_cases))
    
    try:
        results = await evaluator.evaluate(eval_request.test_cases)
        
        logger.info("Evaluation complete", results=results.get("summary", {}))
        
        return EvaluationResponse(
            precision=results.get("precision", 0.0),
            recall=results.get("recall", 0.0),
            f1_score=results.get("f1_score", 0.0),
            avg_latency=results.get("avg_latency", 0.0),
            test_results=results.get("test_results", [])
        )
    
    except Exception as e:
        logger.error("Evaluation failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed"
        )


@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
@limiter.limit("20/minute")
async def get_metrics(request: Request, session_id: Optional[str] = None):
    """
    Get conversation metrics and statistics.
    
    Args:
        request: FastAPI Request object for rate limiting
        session_id: Optional session ID to filter metrics
        
    Returns:
        MetricsResponse with aggregated metrics
    """
    if not controller_agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    try:
        metrics = await controller_agent.get_metrics(session_id)
        
        return MetricsResponse(
            total_conversations=metrics.get("total_conversations", 0),
            total_messages=metrics.get("total_messages", 0),
            avg_response_time=metrics.get("avg_response_time", 0.0),
            tool_usage=metrics.get("tool_usage", {}),
            agent_usage=metrics.get("agent_usage", {}),
            error_rate=metrics.get("error_rate", 0.0)
        )
    
    except Exception as e:
        logger.error("Failed to fetch metrics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch metrics"
        )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )