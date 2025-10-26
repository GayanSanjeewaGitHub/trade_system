"""
Configuration settings for the Trading Chatbot application.
Manages all environment variables and application constants.
"""

from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    app_name: str = "TradingChatbot"
    app_version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    debug: bool = False

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["*"]
    max_request_size: int = 10485760  # 10MB

    # LLM Configuration
    openai_api_key: str = "your-openai-api-key"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: int = 60

    # Pinecone Configuration
    pinecone_api_key: str = "your-pinecone-api-key"
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "trading-chatbot-index"
    pinecone_dimension: int = 1536
    pinecone_metric: str = "cosine"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Langfuse Configuration
    langfuse_public_key: str = "your-langfuse-public-key"
    langfuse_secret_key: str = "your-langfuse-secret-key"
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = True

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"

    # Guardrails Configuration
    max_trade_amount: float = 100000.0
    min_trade_amount: float = 1.0
    max_message_length: int = 5000
    restricted_topics: List[str] = ["illegal", "violence", "hate", "manipulation"]
    profanity_threshold: float = 0.8

    # Agent Configuration
    max_agent_iterations: int = 10
    agent_timeout: int = 120
    max_tool_retries: int = 3

    # MCP Configuration
    mcp_server_url: str = "http://localhost:8001"
    mcp_timeout: int = 30
    mcp_enabled: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 60000
    rate_limit_per_hour: int = 100000

    # Session Management
    session_timeout: int = 36000  # 1 hour
    max_conversation_history: int = 500

    # Monitoring & Evaluation
    enable_auto_eval: bool = True
    eval_sample_rate: float = 0.1
    metrics_retention_days: int = 30

    # Redis Configuration (optional for caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_ttl: int = 3600

    # Document Processing
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = [".pdf", ".txt", ".md", ".docx"]
    temp_upload_dir: str = "/tmp/uploads"

    # Logging
    log_format: str = "json"
    log_file: Optional[str] = None
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    def get_openai_config(self) -> dict:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
            "timeout": self.llm_timeout,
        }

    def get_pinecone_config(self) -> dict:
        """Get Pinecone configuration dictionary."""
        return {
            "api_key": self.pinecone_api_key,
            "environment": self.pinecone_environment,
            "index_name": self.pinecone_index_name,
            "dimension": self.pinecone_dimension,
            "metric": self.pinecone_metric,
        }

    def get_langfuse_config(self) -> dict:
        """Get Langfuse configuration dictionary."""
        return {
            "public_key": self.langfuse_public_key,
            "secret_key": self.langfuse_secret_key,
            "host": self.langfuse_host,
            "enabled": self.langfuse_enabled,
        }

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ["development", "dev"]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to avoid reloading settings on every call.
    """
    return Settings()


# Global settings instance
settings = get_settings()