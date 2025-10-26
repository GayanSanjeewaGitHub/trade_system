"""
MCP Client for connecting to CSE Trading MCP Server
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPTradingClient:
    """Client for CSE Trading MCP Server"""
    
    def __init__(self, server_script_path: str = None):
        """
        Initialize MCP client
        
        Args:
            server_script_path: Path to MCP server script (for stdio transport)
        """
        if server_script_path is None:
            # Default to local server.py
            server_script_path = str(
                Path(__file__).parent / "server.py"
            )
        
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self._client = None
        self._read_stream = None
        self._write_stream = None
    
    async def connect(self):
        """Connect to MCP server"""
        logger.info(f"Connecting to MCP server at {self.server_script_path}")
        
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script_path],
            env=None
        )
        
        # Create stdio client
        stdio = stdio_client(server_params)
        self._read_stream, self._write_stream = await stdio.__aenter__()
        
        # Create session
        self.session = ClientSession(self._read_stream, self._write_stream)
        await self.session.__aenter__()
        
        # Initialize connection
        await self.session.initialize()
        
        logger.info("Connected to MCP server")
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        logger.info("Disconnected from MCP server")
    
    async def list_tools(self) -> List[Dict]:
        """List available tools"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        response = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in response.tools
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        logger.info(f"Calling tool: {name} with args: {arguments}")
        
        result = await self.session.call_tool(name, arguments)
        
        # Extract text content from result
        if result.content:
            content = result.content[0]
            if hasattr(content, 'text'):
                return json.loads(content.text)
        
        return None
    
    async def list_resources(self) -> List[Dict]:
        """List available resources"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        response = await self.session.list_resources()
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mimeType
            }
            for resource in response.resources
        ]
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        response = await self.session.read_resource(uri)
        
        if response.contents:
            return response.contents[0].text
        
        return None
    
    # Convenience methods for trading operations
    
    async def get_stock_price(self, symbol: str) -> Dict:
        """Get stock price"""
        return await self.call_tool("get_stock_price", {"symbol": symbol})
    
    async def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """Get top gainers"""
        return await self.call_tool("get_top_gainers", {"limit": limit})
    
    async def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """Get top losers"""
        return await self.call_tool("get_top_losers", {"limit": limit})
    
    async def get_sector_performance(self) -> List[Dict]:
        """Get sector performance"""
        return await self.call_tool("get_sector_performance", {})
    
    async def calculate_budget(
        self,
        symbol: str,
        quantity: int,
        order_type: str = "BUY"
    ) -> Dict:
        """Calculate trading budget"""
        return await self.call_tool(
            "calculate_budget",
            {
                "symbol": symbol,
                "quantity": quantity,
                "order_type": order_type
            }
        )
    
    async def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str = "BUY"
    ) -> Dict:
        """Place order"""
        return await self.call_tool(
            "place_order",
            {
                "symbol": symbol,
                "quantity": quantity,
                "order_type": order_type
            }
        )
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        return await self.call_tool("cancel_order", {"order_id": order_id})
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        return await self.call_tool("get_order_status", {"order_id": order_id})
    
    async def get_all_orders(self, status_filter: str = None) -> Dict:
        """Get all orders"""
        args = {}
        if status_filter:
            args["status_filter"] = status_filter
        return await self.call_tool("get_all_orders", args)


async def test_client():
    """Test the MCP client"""
    client = MCPTradingClient()
    
    try:
        # Connect
        await client.connect()
        
        # List tools
        print("\n=== Available Tools ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        
        # List resources
        print("\n=== Available Resources ===")
        resources = await client.list_resources()
        for resource in resources:
            print(f"- {resource['name']}: {resource['description']}")
        
        # Get stock price
        print("\n=== Get Stock Price (JKH) ===")
        price = await client.get_stock_price("JKH")
        print(json.dumps(price, indent=2))
        
        # Get top gainers
        print("\n=== Top 5 Gainers ===")
        gainers = await client.get_top_gainers(5)
        for g in gainers:
            print(f"{g['rank']}. {g['symbol']} - {g['name']}: +{g['change_percent']}%")
        
        # Calculate budget
        print("\n=== Calculate Budget (1000 JKH) ===")
        budget = await client.calculate_budget("JKH", 1000, "BUY")
        print(json.dumps(budget, indent=2))
        
        # Place order
        print("\n=== Place Order (500 DIAL) ===")
        order = await client.place_order("DIAL", 500, "BUY")
        print(json.dumps(order, indent=2))
        
        # Get order status
        if order.get("order_id"):
            print(f"\n=== Order Status ({order['order_id']}) ===")
            status = await client.get_order_status(order["order_id"])
            print(json.dumps(status, indent=2))
            
            # Cancel order
            print(f"\n=== Cancel Order ({order['order_id']}) ===")
            cancel = await client.cancel_order(order["order_id"])
            print(json.dumps(cancel, indent=2))
        
        # Read resource
        print("\n=== Read Resource (stock://data/gainers) ===")
        data = await client.read_resource("stock://data/gainers")
        print(data)
        
    finally:
        # Disconnect
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_client())
