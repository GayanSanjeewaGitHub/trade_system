"""
Real MCP Server for CSE Trading
Implements official Model Context Protocol
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import csv
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# Import trading server components directly (avoid src/__init__.py issues)
# We'll embed the trading server here to avoid import issues
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import only what we need
from tools.mcp_trading_server import (
    MCPTradingServer,
    get_mcp_server
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
app = Server("cse-trading-server")
trading_server: Optional[MCPTradingServer] = None


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available trading tools"""
    return [
        types.Tool(
            name="get_stock_price",
            description="Get current stock price and details for a CSE stock symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'JKH', 'DIAL')"
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="get_top_gainers",
            description="Get top gaining stocks by percentage change",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top gainers to return",
                        "default": 10
                    }
                }
            }
        ),
        types.Tool(
            name="get_top_losers",
            description="Get top losing stocks by percentage change",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top losers to return",
                        "default": 10
                    }
                }
            }
        ),
        types.Tool(
            name="get_sector_performance",
            description="Get sector-wise performance analysis",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="calculate_budget",
            description="Calculate total budget required for a trade including all CSE fees (broker commission, VAT, SEC levy, CDS fees, stamp duty)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of shares to trade"
                    },
                    "order_type": {
                        "type": "string",
                        "description": "Order type: 'BUY' or 'SELL'",
                        "enum": ["BUY", "SELL"],
                        "default": "BUY"
                    }
                },
                "required": ["symbol", "quantity"]
            }
        ),
        types.Tool(
            name="place_order",
            description="Place a trading order. Order will be queued for 3 minutes before processing. Can be cancelled during this time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of shares to trade"
                    },
                    "order_type": {
                        "type": "string",
                        "description": "Order type: 'BUY' or 'SELL'",
                        "enum": ["BUY", "SELL"],
                        "default": "BUY"
                    }
                },
                "required": ["symbol", "quantity"]
            }
        ),
        types.Tool(
            name="cancel_order",
            description="Cancel a pending order. Only works if order is still in the 3-minute waiting period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to cancel"
                    }
                },
                "required": ["order_id"]
            }
        ),
        types.Tool(
            name="get_order_status",
            description="Check the status of a trading order including time remaining before processing",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to check"
                    }
                },
                "required": ["order_id"]
            }
        ),
        types.Tool(
            name="get_all_orders",
            description="Get all orders with optional status filter",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "Optional filter: 'pending', 'completed', 'cancelled'",
                        "enum": ["pending", "completed", "cancelled", "rejected"]
                    }
                }
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests"""
    
    global trading_server
    if trading_server is None:
        trading_server = get_mcp_server()
        await trading_server.start_order_processor()
        logger.info(f"Trading server initialized with {len(trading_server.stock_data)} stocks")
    
    try:
        # Execute the requested tool
        if name == "get_stock_price":
            result = trading_server.get_stock_price(arguments["symbol"])
        
        elif name == "get_top_gainers":
            limit = arguments.get("limit", 10)
            result = trading_server.get_top_gainers(limit)
        
        elif name == "get_top_losers":
            limit = arguments.get("limit", 10)
            result = trading_server.get_top_losers(limit)
        
        elif name == "get_sector_performance":
            result = trading_server.get_sector_performance()
        
        elif name == "calculate_budget":
            result = trading_server.calculate_budget(
                arguments["symbol"],
                arguments["quantity"],
                arguments.get("order_type", "BUY")
            )
        
        elif name == "place_order":
            result = trading_server.place_order(
                arguments["symbol"],
                arguments["quantity"],
                arguments.get("order_type", "BUY")
            )
        
        elif name == "cancel_order":
            result = trading_server.cancel_order(arguments["order_id"])
        
        elif name == "get_order_status":
            result = trading_server.get_order_status(arguments["order_id"])
        
        elif name == "get_all_orders":
            result = trading_server.get_all_orders(
                arguments.get("status_filter")
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Return result as TextContent
        return [
            types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": str(e)
                })
            )
        ]


@app.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources (stock data)"""
    return [
        types.Resource(
            uri="stock://data/all",
            name="All Stock Data",
            description="Complete dataset of 40 CSE stocks",
            mimeType="application/json"
        ),
        types.Resource(
            uri="stock://data/gainers",
            name="Top Gainers",
            description="Top gaining stocks today",
            mimeType="application/json"
        ),
        types.Resource(
            uri="stock://data/losers",
            name="Top Losers",
            description="Top losing stocks today",
            mimeType="application/json"
        ),
        types.Resource(
            uri="stock://data/sectors",
            name="Sector Performance",
            description="Sector-wise performance analysis",
            mimeType="application/json"
        )
    ]


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource data"""
    
    global trading_server
    if trading_server is None:
        trading_server = get_mcp_server()
        await trading_server.start_order_processor()
    
    if uri == "stock://data/all":
        data = {
            symbol: {
                "name": stock.name,
                "price": stock.last_price,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "sector": stock.sector
            }
            for symbol, stock in trading_server.stock_data.items()
        }
        return json.dumps(data, indent=2)
    
    elif uri == "stock://data/gainers":
        return json.dumps(trading_server.get_top_gainers(10), indent=2)
    
    elif uri == "stock://data/losers":
        return json.dumps(trading_server.get_top_losers(10), indent=2)
    
    elif uri == "stock://data/sectors":
        return json.dumps(trading_server.get_sector_performance(), indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run the MCP server"""
    logger.info("Starting CSE Trading MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cse-trading-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
