# Quick Start: Real MCP Server

## 1️⃣ Test MCP Server (Standalone)

```powershell
cd mcp_server
python test_server_standalone.py
```

**Expected Output:**
```
✅ Server initialized with 40 stocks
✅ Stock price: JKH @ LKR 195.50 (+6.83%)
✅ Top gainers: DIAL +9.20%
✅ Budget: 1000 JKH = LKR 197,234.08
✅ Order placed: ORD20251026000001
✅ Order cancelled: Refund LKR 4,586.47
```

## 2️⃣ Run MCP Server (Docker)

```powershell
cd mcp_server
docker-compose up -d
```

**Check Logs:**
```powershell
docker-compose logs -f
```

**Stop:**
```powershell
docker-compose down
```

## 3️⃣ Connect from Python

```python
from mcp_server.client import MCPTradingClient
import asyncio

async def main():
    client = MCPTradingClient()
    await client.connect()
    
    # Get stock price
    price = await client.get_stock_price("JKH")
    print(f"{price['symbol']}: LKR {price['price']}")
    
    # Place order
    order = await client.place_order("DIAL", 500, "BUY")
    print(f"Order ID: {order['order_id']}")
    
    await client.disconnect()

asyncio.run(main())
```

## 4️⃣ Available Tools

- `get_stock_price(symbol)` - Get current price
- `get_top_gainers(limit)` - Top gaining stocks
- `get_top_losers(limit)` - Top losing stocks
- `calculate_budget(symbol, qty)` - Cost with fees
- `place_order(symbol, qty, type)` - Place order
- `cancel_order(order_id)` - Cancel order
- `get_order_status(order_id)` - Check status
- `get_all_orders(filter)` - List orders

## 5️⃣ Data Resources

- `stock://data/all` - All stocks
- `stock://data/gainers` - Top gainers
- `stock://data/losers` - Top losers
- `stock://data/sectors` - Sector performance

## 🔍 Verify Installation

```powershell
# Check MCP SDK
pip show mcp

# Check stock data
cat src/data/cse_stock_data.csv | Select-Object -First 5

# Test server import
python -c "import sys; sys.path.insert(0, 'src'); from tools.mcp_trading_server import get_mcp_server; print(f'{len(get_mcp_server().stock_data)} stocks')"
```

## 🐋 Docker Commands

```powershell
# Build
docker build -t cse-trading-mcp -f mcp_server/Dockerfile .

# Run
docker run -d --name mcp-server cse-trading-mcp

# Logs
docker logs -f mcp-server

# Stop
docker stop mcp-server && docker rm mcp-server
```

## 📚 Documentation

- **Full Guide**: [docs/REAL_MCP_SERVER.md](../docs/REAL_MCP_SERVER.md)
- **MCP Details**: [README.md](README.md)
- **API Reference**: [docs/MCP_TRADING_SERVER.md](../docs/MCP_TRADING_SERVER.md)

---

**Ready to go!** 🚀
