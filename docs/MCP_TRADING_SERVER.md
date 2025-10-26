# MCP Trading Server Documentation

## Overview

The MCP (Model Context Protocol) Trading Server provides a comprehensive trading infrastructure for the CSE (Colombo Stock Exchange) advisor agent. It handles stock data queries, order management with queue processing, and budget calculations with accurate CSE trading fees.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Advisor Agent                             │
│  (Natural language interface for trading)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ LangChain Tools
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               MCP Trading Server                             │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Stock Data     │  │ Order Queue  │  │ Fee Calculator │  │
│  │ Manager        │  │ (3-min delay)│  │ (CSE Fees)     │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ CSV Data
                            │
┌───────────────────────────▼─────────────────────────────────┐
│          cse_stock_data.csv (40 stocks)                      │
│  JKH, DIAL, HNB, LOLC, COMB, SLTL, etc.                     │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Stock Data Queries
- **Get Stock Price**: Retrieve current price and details for any CSE stock
- **Top Gainers**: Find stocks with highest percentage gains
- **Top Losers**: Find stocks with highest percentage losses
- **Sector Performance**: Analyze performance across sectors

### 2. Order Management
- **Order Queue**: 3-minute processing delay for all orders
- **Cancellation Window**: Cancel orders during the 3-minute waiting period
- **Order Tracking**: Real-time status updates for all orders
- **Order History**: View all orders with status filters

### 3. Budget Calculator
Accurate CSE trading fee calculations:
- **Broker Commission**: 0.4% (minimum LKR 100)
- **VAT**: 18% on broker commission
- **SEC Levy**: 0.1% of transaction value
- **CDS Fees**: 0.015% of transaction value
- **Stamp Duty**: 0.3% of transaction value

## Stock Dataset

40 CSE stocks across 9 sectors:

| Sector | Count | Examples |
|--------|-------|----------|
| Banking | 8 | HNB, COMB, SAMP, DFCC |
| Diversified | 7 | JKH, LOLC, EXPO, SEYB |
| Telecom | 5 | DIAL, SLT, HHL |
| Beverages | 4 | LION, COCL |
| Manufacturing | 4 | SLTL, TKYO |
| Power & Energy | 4 | LIOC, CPC |
| Hotels | 3 | AHUN, JINS |
| Consumer Goods | 3 | PABC, HARI |
| Healthcare | 2 | ASIR |

### Top Performers (Sample Data)
**Gainers:**
- DIAL: +9.20%
- LOLC: +7.78%
- HNB: +7.40%

**Losers:**
- SLTL: -7.30%
- PABC: -6.86%
- LIOC: -6.22%

## API Reference

### Stock Queries

#### `get_stock_price(symbol: str) -> dict`
Get current stock information.

**Parameters:**
- `symbol`: Stock ticker (e.g., "JKH")

**Returns:**
```json
{
  "symbol": "JKH",
  "name": "John Keells Holdings PLC",
  "price": 450.00,
  "change": 28.50,
  "change_percent": 6.76,
  "volume": 1234567,
  "high": 455.00,
  "low": 440.00,
  "market_cap": 125000000000,
  "sector": "Diversified"
}
```

#### `get_top_gainers(limit: int = 10) -> list`
Get top gaining stocks.

**Parameters:**
- `limit`: Number of stocks to return (default: 10)

**Returns:**
```json
[
  {
    "rank": 1,
    "symbol": "DIAL",
    "name": "Dialog Axiata PLC",
    "price": 12.00,
    "change": 1.02,
    "change_percent": 9.20,
    "volume": 5678901
  }
]
```

#### `get_top_losers(limit: int = 10) -> list`
Get top losing stocks.

#### `get_sector_performance() -> list`
Get sector-wise performance analysis.

**Returns:**
```json
[
  {
    "sector": "Banking",
    "avg_change_percent": 4.25,
    "stock_count": 8,
    "top_stocks": ["HNB", "COMB", "SAMP", "DFCC", "NDB"]
  }
]
```

### Budget Calculator

#### `calculate_budget(symbol: str, quantity: int, order_type: str = "BUY") -> dict`
Calculate total cost including all fees.

**Parameters:**
- `symbol`: Stock ticker
- `quantity`: Number of shares
- `order_type`: "BUY" or "SELL"

**Returns:**
```json
{
  "status": "success",
  "symbol": "JKH",
  "quantity": 1000,
  "price_per_share": 450.00,
  "transaction_value": 450000.00,
  "broker_commission": 1800.00,
  "vat": 324.00,
  "sec_levy": 450.00,
  "cds_fee": 67.50,
  "stamp_duty": 1350.00,
  "total_fees": 3991.50,
  "total_cost": 453991.50
}
```

### Order Management

#### `place_order(symbol: str, quantity: int, order_type: str = "BUY") -> dict`
Place a new trading order.

**Parameters:**
- `symbol`: Stock ticker
- `quantity`: Number of shares
- `order_type`: "BUY" or "SELL"

**Returns:**
```json
{
  "status": "success",
  "order_id": "ORD20250115000001",
  "symbol": "JKH",
  "quantity": 1000,
  "price_per_share": 450.00,
  "order_status": "PENDING",
  "total_cost": 453991.50,
  "estimated_processing_time": "3 minutes",
  "can_cancel": true
}
```

#### `cancel_order(order_id: str) -> dict`
Cancel a pending order.

**Parameters:**
- `order_id`: Order ID to cancel

**Returns:**
```json
{
  "status": "success",
  "message": "Order ORD20250115000001 cancelled successfully",
  "order_id": "ORD20250115000001",
  "refund_amount": 453991.50
}
```

#### `get_order_status(order_id: str) -> dict`
Check order status.

**Returns:**
```json
{
  "status": "success",
  "order_id": "ORD20250115000001",
  "order_status": "PENDING",
  "time_remaining_seconds": 145,
  "can_cancel": true,
  "total_amount": 453991.50
}
```

#### `get_all_orders(status_filter: str = None) -> dict`
Get all orders with optional filter.

**Parameters:**
- `status_filter`: Optional ("pending", "completed", "cancelled")

## Order Processing Flow

```
User Request
     │
     ▼
Place Order ──────────────────┐
     │                         │
     │                         │ 3-Minute Window
     ▼                         │
Order Queue                    │
     │                         │
     │ Can Cancel ◄────────────┘
     │
     ▼ After 3 minutes
Process Order
     │
     ├──► COMPLETED (if valid)
     │
     └──► REJECTED (if invalid)
```

## Usage Examples

### Python (Direct)

```python
import asyncio
from src.tools.mcp_trading_server import get_mcp_server

async def trade_example():
    server = get_mcp_server()
    await server.start_order_processor()
    
    # Get stock price
    price = server.get_stock_price("JKH")
    print(f"JKH Price: LKR {price['price']}")
    
    # Calculate budget
    budget = server.calculate_budget("JKH", 1000, "BUY")
    print(f"Total Cost: LKR {budget['total_cost']}")
    
    # Place order
    order = server.place_order("JKH", 1000, "BUY")
    order_id = order["order_id"]
    print(f"Order placed: {order_id}")
    
    # Check status
    status = server.get_order_status(order_id)
    print(f"Status: {status['order_status']}")
    
    # Cancel if needed
    if status["can_cancel"]:
        cancel = server.cancel_order(order_id)
        print(f"Cancelled: {cancel['message']}")

asyncio.run(trade_example())
```

### Natural Language (via Advisor Agent)

```
User: "What are the top 5 gaining stocks today?"
Agent: [Uses mcp_get_top_gainers(5)]
      "Here are today's top gainers:
       1. DIAL (+9.20%)
       2. LOLC (+7.78%)
       ..."

User: "I want to buy 1000 JKH shares. How much will it cost?"
Agent: [Uses mcp_calculate_budget("JKH", 1000, "BUY")]
      "To buy 1000 JKH shares:
       - Share cost: LKR 450,000
       - Broker fees: LKR 1,800
       - Total fees: LKR 3,991.50
       - TOTAL: LKR 453,991.50"

User: "Go ahead and place the order"
Agent: [Uses mcp_place_order("JKH", 1000, "BUY")]
      "Order placed successfully!
       Order ID: ORD20250115000001
       You have 3 minutes to cancel if needed."

User: "Cancel that order"
Agent: [Uses mcp_cancel_order("ORD20250115000001")]
      "Order cancelled. Refund: LKR 453,991.50"
```

## Testing

Run the comprehensive test suite:

```powershell
python scripts/test_mcp_server.py
```

Tests include:
1. Stock queries (price, gainers, losers, sectors)
2. Budget calculations
3. Order placement and cancellation
4. Order status tracking
5. Error handling

## Configuration

No configuration needed - the server auto-loads from:
```
src/data/cse_stock_data.csv
```

## Limitations

1. **Static Data**: Stock prices are from CSV (not real-time)
2. **Mock Orders**: Orders are in-memory (not sent to exchange)
3. **40 Stocks**: Limited to dataset stocks
4. **No Authentication**: No user authentication system
5. **Single Instance**: Not designed for multi-user production

## Future Enhancements

- [ ] Real-time price feeds from CSE API
- [ ] Internet fallback for unknown stocks
- [ ] User authentication and portfolios
- [ ] Database persistence for orders
- [ ] WebSocket for real-time updates
- [ ] Advanced order types (limit, stop-loss)
- [ ] Portfolio tracking and P&L
- [ ] Trade execution confirmation

## Troubleshooting

### Stock not found
**Error**: `"Stock XYZ not found in database"`
**Solution**: Check `cse_stock_data.csv` - only 40 stocks available

### Order cannot be cancelled
**Error**: `"Order cannot be cancelled. Status: completed"`
**Solution**: Orders can only be cancelled within 3-minute window

### Import errors
**Error**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Run from project root or add to Python path

## Support

For issues or questions:
1. Check test suite results
2. Review logs in `logs/` directory
3. Validate stock symbols in CSV
4. Ensure async/await patterns used correctly

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**License**: Internal Use
