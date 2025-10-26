# Real MCP Server for CSE Trading

This is a **real** Model Context Protocol (MCP) server that can run standalone or in Docker and be accessed by MCP clients.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to LLMs. It allows:
- **Separation of concerns**: Trading logic in MCP server, AI agent as client
- **Reusability**: Multiple agents/apps can connect to same server
- **Scalability**: Run server in Docker, connect from anywhere
- **Standard protocol**: Works with any MCP-compatible client

## Architecture

```
┌─────────────────────────────────────────┐
│         Advisor Agent (Client)           │
│  Uses MCP Client to connect to server   │
└──────────────────┬──────────────────────┘
                   │
                   │ MCP Protocol (stdio/HTTP)
                   │
┌──────────────────▼──────────────────────┐
│      CSE Trading MCP Server              │
│  Running in Docker                       │
│  ┌────────────┐  ┌──────────────┐       │
│  │ 9 Tools    │  │ 4 Resources  │       │
│  └────────────┘  └──────────────┘       │
└──────────────────┬──────────────────────┘
                   │
                   │ Loads data
                   │
┌──────────────────▼──────────────────────┐
│     cse_stock_data.csv (40 stocks)      │
└─────────────────────────────────────────┘
```

## Files

- `server.py` - Real MCP server implementation
- `client.py` - MCP client for connecting to server
- `Dockerfile` - Docker image configuration
- `docker-compose.yml` - Docker deployment
- `requirements.txt` - MCP SDK dependencies

## MCP Tools (9)

1. **get_stock_price** - Get current stock price
2. **get_top_gainers** - Top gaining stocks
3. **get_top_losers** - Top losing stocks
4. **get_sector_performance** - Sector analysis
5. **calculate_budget** - Total cost with fees
6. **place_order** - Place order (3-min queue)
7. **cancel_order** - Cancel pending order
8. **get_order_status** - Check order status
9. **get_all_orders** - List all orders

## MCP Resources (4)

1. **stock://data/all** - All stock data
2. **stock://data/gainers** - Top gainers
3. **stock://data/losers** - Top losers
4. **stock://data/sectors** - Sector performance

## Quick Start

### Option 1: Run Locally with Python

```powershell
# Install dependencies
pip install mcp

# Run server
cd mcp_server
python server.py
```

### Option 2: Run in Docker

```powershell
# Build and run
cd mcp_server
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 3: Test with Client

```powershell
# Run test client
cd mcp_server
python client.py
```

## Using the MCP Server

### From Python Client

```python
from mcp_server.client import MCPTradingClient

async def main():
    client = MCPTradingClient()
    await client.connect()
    
    # Get stock price
    price = await client.get_stock_price("JKH")
    print(price)
    
    # Place order
    order = await client.place_order("DIAL", 500, "BUY")
    print(order)
    
    await client.disconnect()
```

### From Advisor Agent

The advisor agent will automatically connect to the MCP server and use it as a tool provider.

## MCP Protocol Details

### Transport
- **stdio**: Standard input/output (default)
- **HTTP/SSE**: Server-Sent Events (optional, port 8080)

### Message Format
All messages follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_stock_price",
    "arguments": {
      "symbol": "JKH"
    }
  }
}
```

### Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"symbol\": \"JKH\", \"price\": 195.50}"
      }
    ]
  }
}
```

## Example: Client-Server Interaction

**1. Client connects to server**
```python
client = MCPTradingClient()
await client.connect()
```

**2. Client lists available tools**
```python
tools = await client.list_tools()
# Returns: 9 trading tools
```

**3. Client calls a tool**
```python
result = await client.call_tool(
    "get_stock_price",
    {"symbol": "JKH"}
)
# Returns: {"symbol": "JKH", "price": 195.50, ...}
```

**4. Client reads a resource**
```python
data = await client.read_resource("stock://data/gainers")
# Returns: JSON with top gainers
```

## Docker Deployment

### Build Image

```powershell
cd mcp_server
docker build -t cse-trading-mcp:latest -f Dockerfile ..
```

### Run Container

```powershell
docker run -d \
  --name cse-trading-mcp \
  -p 8080:8080 \
  -v "$(pwd)/../src/data:/app/src/data:ro" \
  cse-trading-mcp:latest
```

### Check Health

```powershell
docker exec cse-trading-mcp python -c "print('Server running')"
```

## Connecting from Advisor Agent

Update `advisor_agent.py` to use MCP client:

```python
from mcp_server.client import MCPTradingClient

class AdvisorAgent:
    def __init__(self):
        self.mcp_client = MCPTradingClient()
    
    async def initialize(self):
        await self.mcp_client.connect()
        
        # Use MCP tools
        tools = await self.mcp_client.list_tools()
        # Wrap as LangChain tools
        self.tools = self._create_langchain_tools(tools)
    
    async def cleanup(self):
        await self.mcp_client.disconnect()
```

## Benefits of Real MCP Server

✅ **Standard Protocol**: Works with any MCP client  
✅ **Containerized**: Run in Docker for isolation  
✅ **Scalable**: Multiple agents can connect  
✅ **Maintainable**: Separate trading logic from agent  
✅ **Testable**: Test server independently  
✅ **Extensible**: Easy to add new tools  

## Troubleshooting

### Server won't start
**Check:** MCP library installed
```powershell
pip show mcp
```

### Client can't connect
**Check:** Server is running
```powershell
docker ps | grep mcp
```

### Tool calls fail
**Check:** Stock data CSV exists
```powershell
ls ../src/data/cse_stock_data.csv
```

## MCP Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)

## Next Steps

1. ✅ Install MCP SDK: `pip install mcp`
2. ✅ Run server: `python server.py`
3. ✅ Test client: `python client.py`
4. ⏳ Deploy to Docker: `docker-compose up -d`
5. ⏳ Connect advisor agent to MCP server
6. ⏳ Add HTTP/SSE transport for web clients

---

**Version**: 1.0.0  
**Protocol**: Model Context Protocol (MCP)  
**Transport**: stdio (default), HTTP/SSE (optional)
