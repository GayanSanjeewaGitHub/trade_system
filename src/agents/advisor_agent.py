"""
Advisor Agent - Handles trading actions and investment advice.
Now integrated with MCP Trading Server for real-time stock data and order management.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.config.settings import settings
from src.tools.mcp_trading_server import (
    mcp_get_stock_price,
    mcp_get_top_gainers,
    mcp_get_top_losers,
    mcp_get_sector_performance,
    mcp_calculate_budget,
    mcp_place_order,
    mcp_cancel_order,
    mcp_get_order_status,
    mcp_get_all_orders,
    get_mcp_server
)
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class AdvisorAgent:
    """Advisor agent that handles trading and provides investment advice using MCP server."""
    
    def __init__(self):
        self.llm: Optional[ChatOpenAI] = None
        self.agent_executor: Optional[AgentExecutor] = None
        self.tools: List = []
        self.mcp_server = None
    
    def _create_mcp_tools(self) -> List:
        """Create LangChain tools from MCP server functions"""
        
        @tool
        async def get_stock_price(symbol: str) -> dict:
            """Get current stock price and details for a given symbol.
            
            Args:
                symbol: Stock ticker symbol (e.g., 'JKH', 'DIAL')
            
            Returns:
                Dictionary with price, change, volume, and other stock details
            """
            return await mcp_get_stock_price(symbol)
        
        @tool
        async def get_top_gainers(limit: int = 10) -> list:
            """Get top gaining stocks by percentage change.
            
            Args:
                limit: Number of top gainers to return (default 10)
            
            Returns:
                List of stocks sorted by highest percentage gains
            """
            return await mcp_get_top_gainers(limit)
        
        @tool
        async def get_top_losers(limit: int = 10) -> list:
            """Get top losing stocks by percentage change.
            
            Args:
                limit: Number of top losers to return (default 10)
            
            Returns:
                List of stocks sorted by highest percentage losses
            """
            return await mcp_get_top_losers(limit)
        
        @tool
        async def get_sector_performance() -> list:
            """Get sector-wise performance analysis.
            
            Returns:
                List of sectors with average performance metrics
            """
            return await mcp_get_sector_performance()
        
        @tool
        async def calculate_trading_budget(symbol: str, quantity: int, order_type: str = "BUY") -> dict:
            """Calculate total budget required for a trade including all fees.
            
            Includes: broker commission (0.4%), VAT (18%), SEC levy (0.1%), 
                     CDS fees (0.015%), stamp duty (0.3%)
            
            Args:
                symbol: Stock ticker symbol
                quantity: Number of shares
                order_type: 'BUY' or 'SELL' (default 'BUY')
            
            Returns:
                Detailed breakdown of costs and total amount required
            """
            return await mcp_calculate_budget(symbol, quantity, order_type)
        
        @tool
        async def place_stock_order(symbol: str, quantity: int, order_type: str = "BUY") -> dict:
            """Place a trading order. Order will be queued for 3 minutes before processing.
            
            During the 3-minute window, the order can be cancelled. After 3 minutes,
            the order will be processed automatically.
            
            Args:
                symbol: Stock ticker symbol
                quantity: Number of shares
                order_type: 'BUY' or 'SELL' (default 'BUY')
            
            Returns:
                Order confirmation with order ID, total cost, and processing details
            """
            return await mcp_place_order(symbol, quantity, order_type)
        
        @tool
        async def cancel_stock_order(order_id: str) -> dict:
            """Cancel a pending order before it's processed.
            
            Orders can only be cancelled during the 3-minute waiting period.
            Once processed, cancellation is not possible.
            
            Args:
                order_id: The order ID to cancel
            
            Returns:
                Cancellation confirmation with refund details
            """
            return await mcp_cancel_order(order_id)
        
        @tool
        async def check_order_status(order_id: str) -> dict:
            """Check the status of a trading order.
            
            Shows whether order is pending, processing, completed, or cancelled.
            For pending orders, shows time remaining before processing.
            
            Args:
                order_id: The order ID to check
            
            Returns:
                Order status with timing and cancellation eligibility
            """
            return await mcp_get_order_status(order_id)
        
        @tool
        async def view_all_orders(status_filter: str = None) -> dict:
            """View all trading orders with optional status filter.
            
            Args:
                status_filter: Optional filter ('pending', 'completed', 'cancelled')
            
            Returns:
                List of all orders matching the filter
            """
            return await mcp_get_all_orders(status_filter)
        
        return [
            get_stock_price,
            get_top_gainers,
            get_top_losers,
            get_sector_performance,
            calculate_trading_budget,
            place_stock_order,
            cancel_stock_order,
            check_order_status,
            view_all_orders
        ]
    
    async def initialize(self) -> None:
        """Initialize Advisor agent with MCP trading tools."""
        try:
            logger.info("Initializing Advisor agent with MCP server")
            
            # Initialize MCP server
            self.mcp_server = get_mcp_server()
            await self.mcp_server.start_order_processor()
            logger.info(f"MCP server loaded with {len(self.mcp_server.stock_data)} stocks")
            
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
            
            # Create MCP tools
            self.tools = self._create_mcp_tools()
            
            # Create agent with enhanced system prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert CSE (Colombo Stock Exchange) trading advisor assistant.

**Your Capabilities:**
- Real-time stock price queries from CSE market data
- Market analysis: top gainers, top losers, sector performance
- Budget calculations with accurate CSE trading fees
- Order placement with 3-minute processing queue
- Order cancellation during waiting period
- Order status tracking

**CSE Trading Fees (automatically calculated):**
- Broker Commission: 0.4% (min LKR 100)
- VAT on Commission: 18%
- SEC Levy: 0.1%
- CDS Fees: 0.015%
- Stamp Duty: 0.3%

**Order Processing:**
- Orders are queued for 3 minutes before execution
- During this period, users can cancel orders
- After 3 minutes, orders are automatically processed
- Always provide order ID for tracking

**Response Guidelines:**
1. Always confirm trade details before placing orders
2. Show budget breakdown for transparency
3. Explain fees clearly to users
4. Warn about market risks when appropriate
5. For stock queries, check if symbol exists in database first
6. Provide order IDs for all placed orders
7. Remind users about the 3-minute cancellation window

**Available Stock Universe:**
40 CSE stocks across sectors: Banking, Telecom, Manufacturing, Power & Energy, Beverages, Hotels, Healthcare, Diversified, Consumer Goods.

Be professional, clear, and helpful. Always prioritize user understanding and safety."""),
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
            
            logger.info("Advisor agent initialized successfully", 
                       tools_count=len(self.tools),
                       stocks_loaded=len(self.mcp_server.stock_data))
            
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