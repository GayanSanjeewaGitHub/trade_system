"""
Advisor Agent - Handles trading actions and investment advice.
"""

import time
from typing import Dict, Any, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.config.settings import settings
from src.tools.stock_tools import get_stock_tools
from src.tools.budget_tools import get_budget_tools
from src.tools.mcp_tools import get_mcp_tools
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class AdvisorAgent:
    """Advisor agent that handles trading and provides investment advice."""
    
    def __init__(self):
        self.llm: Optional[ChatOpenAI] = None
        self.agent_executor: Optional[AgentExecutor] = None
        self.tools: List = []
    
    async def initialize(self) -> None:
        """Initialize Advisor agent with tools."""
        try:
            logger.info("Initializing Advisor agent")
            
            # Check if OpenAI API key is configured
            if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key":
                logger.warning("OpenAI API key not configured, Advisor agent will be limited")
                self.llm = None
                return
            
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                api_key=settings.openai_api_key
            )
            
            # Collect all tools
            self.tools = []
            self.tools.extend(await get_stock_tools())
            self.tools.extend(await get_budget_tools())
            
            if settings.mcp_enabled:
                self.tools.extend(await get_mcp_tools())
            
            # Create agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a financial trading advisor assistant. You help users with:
                - Getting stock prices and market information
                - Executing trades (buy/sell)
                - Portfolio management
                - Budget calculations
                
                Always confirm trades before executing. Be clear about risks. Use tools when needed."""),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_openai_functions_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=settings.max_agent_iterations,
                handle_parsing_errors=True
            )
            
            logger.info("Advisor agent initialized", tools_count=len(self.tools))
            
        except Exception as e:
            logger.error("Failed to initialize Advisor agent", error=str(e), exc_info=True)
            raise
    
    async def process(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process advisor query with tool execution.
        
        Args:
            query: User input
            session_id: Session identifier
            context: Additional context
            
        Returns:
            Dict with response and metadata
        """
        start_time = time.time()
        
        try:
            logger.info("Processing Advisor query", session_id=session_id)
            
            # Check if agent is properly initialized
            if not self.llm or not self.agent_executor:
                fallback_response = """I'm here to help with trading and investment activities on the CSE platform.
                However, my trading capabilities are currently not available. I can help with:
                - Buying and selling shares/stocks
                - Checking current stock prices
                - Portfolio management and analysis
                - Investment planning and advice
                - Market analysis and trends
                - Dividend information
                - Broker services and recommendations
                
                Please ensure the system is properly configured to enable trading features."""
                
                return {
                    "response": fallback_response,
                    "tools_used": [],
                    "confidence": 0.0
                }
            
            # Execute agent
            result = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": context.get("chat_history", []) if context else []
            })
            
            latency = (time.time() - start_time) * 1000
            
            # Extract tool usage
            tools_used = []
            if hasattr(result, "intermediate_steps"):
                tools_used = [
                    step[0].tool for step in result.get("intermediate_steps", [])
                ]
            
            logger.info(
                "Advisor query processed",
                session_id=session_id,
                latency_ms=latency,
                tools_used=tools_used
            )
            
            return {
                "response": result.get("output", ""),
                "tools_used": tools_used,
                "latency_ms": latency
            }
            
        except Exception as e:
            logger.error("Advisor processing failed", error=str(e), session_id=session_id, exc_info=True)
            return {
                "response": "I encountered an error processing your trading request. Please try again or contact support if the issue persists.",
                "tools_used": [],
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up Advisor agent")