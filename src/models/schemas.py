"""
Pydantic models for request/response validation.
Ensures type safety and automatic validation across the application.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types for ingestion."""
    FAQ = "faq"
    POLICY = "policy"
    PRODUCT_INFO = "product_info"
    GENERAL = "general"


class AgentType(str, Enum):
    """Available agent types in the system."""
    CONTROLLER = "controller"
    FAQ = "faq"
    ADVISOR = "advisor"


class ToolType(str, Enum):
    """Available tool types."""
    STOCK_PRICE = "get_stock_price"
    EXECUTE_TRADE = "execute_trade"
    CALCULATE_BUDGET = "calculate_budget"
    GET_PORTFOLIO = "get_portfolio"
    MCP_TOOL = "mcp_tool"


# Request Models

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message."""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class TestCase(BaseModel):
    """Individual test case for evaluation."""
    question: str = Field(..., description="Test question")
    expected_answer: str = Field(..., description="Expected answer")
    category: Optional[str] = Field(None, description="Question category")
    
    
class EvaluationRequest(BaseModel):
    """Request model for evaluation endpoint."""
    test_cases: List[TestCase] = Field(..., min_length=1, description="List of test cases")
    include_latency: bool = Field(True, description="Include latency metrics")


# Response Models

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Bot response")
    session_id: str = Field(..., description="Session identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    tools_used: List[str] = Field(default_factory=list, description="Tools invoked")
    agent_path: List[str] = Field(default_factory=list, description="Agent execution path")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool = Field(..., description="Ingestion success status")
    filename: str = Field(..., description="Ingested filename")
    chunks_created: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestResult(BaseModel):
    """Individual test result."""
    question: str
    expected_answer: str
    actual_answer: str
    score: float = Field(..., ge=0.0, le=1.0)
    latency_ms: float
    passed: bool


class EvaluationResponse(BaseModel):
    """Response model for evaluation endpoint."""
    precision: float = Field(..., ge=0.0, le=1.0, description="Precision score")
    recall: float = Field(..., ge=0.0, le=1.0, description="Recall score")
    f1_score: float = Field(..., ge=0.0, le=1.0, description="F1 score")
    avg_latency: float = Field(..., description="Average latency in ms")
    test_results: List[TestResult] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    total_conversations: int = Field(..., description="Total conversations")
    total_messages: int = Field(..., description="Total messages processed")
    avg_response_time: float = Field(..., description="Average response time in ms")
    tool_usage: Dict[str, int] = Field(default_factory=dict, description="Tool usage counts")
    agent_usage: Dict[str, int] = Field(default_factory=dict, description="Agent usage counts")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    components: Dict[str, bool] = Field(default_factory=dict, description="Component health")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Internal Models

class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Conversation history model."""
    session_id: str
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    """Tool invocation record."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentExecution(BaseModel):
    """Agent execution record."""
    agent_type: AgentType
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    tools_used: List[ToolCall] = Field(default_factory=list)
    error: Optional[str] = None
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Document model for RAG."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_type: DocumentType
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """Document chunk after splitting."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TradeRequest(BaseModel):
    """Trade execution request."""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    action: str = Field(..., pattern="^(buy|sell)$", description="Trade action")
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: Optional[float] = Field(None, gt=0, description="Limit price")
    
    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol."""
        return v.upper().strip()


class TradeResult(BaseModel):
    """Trade execution result."""
    success: bool
    trade_id: Optional[str] = None
    symbol: str
    action: str
    quantity: int
    executed_price: float
    total_amount: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PortfolioItem(BaseModel):
    """Portfolio holding item."""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    total_value: float
    profit_loss: float
    profit_loss_pct: float


class Portfolio(BaseModel):
    """User portfolio."""
    user_id: str
    holdings: List[PortfolioItem] = Field(default_factory=list)
    cash_balance: float
    total_value: float
    total_profit_loss: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)