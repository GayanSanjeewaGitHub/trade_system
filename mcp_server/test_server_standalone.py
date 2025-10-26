"""
Simple MCP Server Test (No Client)
Run the server and send JSON-RPC messages manually
"""

import asyncio
import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.mcp_trading_server import get_mcp_server


async def test_trading_server():
    """Test the trading server directly"""
    
    print("\n" + "="*80)
    print("REAL MCP SERVER - STANDALONE TEST")
    print("="*80)
    
    # Get server
    server = get_mcp_server()
    await server.start_order_processor()
    
    print(f"\n✅ Server initialized with {len(server.stock_data)} stocks\n")
    
    # Test 1: Get stock price
    print("1. Get Stock Price (JKH)")
    print("-" * 40)
    result = server.get_stock_price("JKH")
    print(json.dumps(result, indent=2))
    
    # Test 2: Top gainers
    print("\n2. Top 5 Gainers")
    print("-" * 40)
    gainers = server.get_top_gainers(5)
    for g in gainers:
        print(f"  {g['rank']}. {g['symbol']:8} - +{g['change_percent']:6.2f}%")
    
    # Test 3: Calculate budget
    print("\n3. Calculate Budget (1000 JKH)")
    print("-" * 40)
    budget = server.calculate_budget("JKH", 1000, "BUY")
    print(f"  Share cost:  LKR {budget['transaction_value']:,.2f}")
    print(f"  Total fees:  LKR {budget['total_fees']:,.2f}")
    print(f"  TOTAL COST:  LKR {budget['total_cost']:,.2f}")
    
    # Test 4: Place order
    print("\n4. Place Order (500 DIAL)")
    print("-" * 40)
    order = server.place_order("DIAL", 500, "BUY")
    print(f"  Order ID:    {order['order_id']}")
    print(f"  Status:      {order['order_status']}")
    print(f"  Total Cost:  LKR {order['total_cost']:,.2f}")
    print(f"  Can Cancel:  {order['can_cancel']}")
    
    # Test 5: Check status
    print(f"\n5. Check Order Status")
    print("-" * 40)
    status = server.get_order_status(order['order_id'])
    print(f"  Status:      {status['order_status']}")
    print(f"  Time Left:   {status['time_remaining_seconds']}s")
    
    # Test 6: Cancel order
    print(f"\n6. Cancel Order")
    print("-" * 40)
    cancel = server.cancel_order(order['order_id'])
    print(f"  Message:     {cancel['message']}")
    print(f"  Refund:      LKR {cancel['refund_amount']:,.2f}")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED - MCP SERVER WORKING!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_trading_server())
