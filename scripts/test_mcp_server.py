"""
Test script for MCP Trading Server
Demonstrates all trading capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.mcp_trading_server import get_mcp_server
import json


async def test_stock_queries():
    """Test stock data queries"""
    print("\n" + "=" * 80)
    print("STOCK QUERIES TEST")
    print("=" * 80)
    
    server = get_mcp_server()
    
    # Test 1: Get specific stock price
    print("\n1. Get Stock Price (JKH)")
    result = server.get_stock_price("JKH")
    print(json.dumps(result, indent=2))
    
    # Test 2: Get top gainers
    print("\n2. Top 5 Gainers")
    gainers = server.get_top_gainers(5)
    for g in gainers:
        print(f"   {g['rank']}. {g['symbol']:8} - {g['name']:30} | +{g['change_percent']:6.2f}% | Price: LKR {g['price']:10,.2f}")
    
    # Test 3: Get top losers
    print("\n3. Top 5 Losers")
    losers = server.get_top_losers(5)
    for l in losers:
        print(f"   {l['rank']}. {l['symbol']:8} - {l['name']:30} | {l['change_percent']:6.2f}% | Price: LKR {l['price']:10,.2f}")
    
    # Test 4: Sector performance
    print("\n4. Sector Performance")
    sectors = server.get_sector_performance()
    for s in sectors:
        print(f"   {s['sector']:20} | Avg Change: {s['avg_change_percent']:6.2f}% | Stocks: {s['stock_count']}")


async def test_budget_calculator():
    """Test budget calculation"""
    print("\n" + "=" * 80)
    print("BUDGET CALCULATOR TEST")
    print("=" * 80)
    
    server = get_mcp_server()
    
    test_cases = [
        ("JKH", 1000, "BUY"),
        ("DIAL", 500, "BUY"),
        ("HNB", 2000, "BUY"),
    ]
    
    for symbol, quantity, order_type in test_cases:
        print(f"\n{order_type} {quantity} shares of {symbol}")
        budget = server.calculate_budget(symbol, quantity, order_type)
        
        if budget["status"] == "success":
            print(f"   Price per share: LKR {budget['price_per_share']:,.2f}")
            print(f"   Share cost:      LKR {budget['transaction_value']:,.2f}")
            print(f"   Broker fee:      LKR {budget['broker_commission']:,.2f}")
            print(f"   VAT:             LKR {budget['vat']:,.2f}")
            print(f"   SEC levy:        LKR {budget['sec_levy']:,.2f}")
            print(f"   CDS fee:         LKR {budget['cds_fee']:,.2f}")
            print(f"   Stamp duty:      LKR {budget['stamp_duty']:,.2f}")
            print(f"   {'-' * 50}")
            print(f"   TOTAL FEES:      LKR {budget['total_fees']:,.2f}")
            print(f"   TOTAL COST:      LKR {budget['total_cost']:,.2f}")


async def test_order_management():
    """Test order placement and management"""
    print("\n" + "=" * 80)
    print("ORDER MANAGEMENT TEST")
    print("=" * 80)
    
    server = get_mcp_server()
    await server.start_order_processor()
    
    # Test 1: Place order
    print("\n1. Placing order for 1000 JKH shares")
    order1 = server.place_order("JKH", 1000, "BUY")
    print(json.dumps(order1, indent=2))
    order1_id = order1["order_id"]
    
    # Test 2: Check order status
    print(f"\n2. Checking order status for {order1_id}")
    status1 = server.get_order_status(order1_id)
    print(json.dumps(status1, indent=2))
    
    # Test 3: Place another order
    print("\n3. Placing order for 500 DIAL shares")
    order2 = server.place_order("DIAL", 500, "BUY")
    print(json.dumps(order2, indent=2))
    order2_id = order2["order_id"]
    
    # Test 4: View all orders
    print("\n4. Viewing all pending orders")
    all_orders = server.get_all_orders("pending")
    print(json.dumps(all_orders, indent=2))
    
    # Test 5: Cancel first order
    print(f"\n5. Cancelling order {order1_id}")
    cancel_result = server.cancel_order(order1_id)
    print(json.dumps(cancel_result, indent=2))
    
    # Test 6: Try to cancel again (should fail)
    print(f"\n6. Trying to cancel {order1_id} again (should fail)")
    cancel_again = server.cancel_order(order1_id)
    print(json.dumps(cancel_again, indent=2))
    
    # Test 7: Wait and check if order2 is processed
    print("\n7. Waiting 10 seconds to check order processing...")
    await asyncio.sleep(10)
    
    status2 = server.get_order_status(order2_id)
    print(f"\nOrder {order2_id} status after 10 seconds:")
    print(json.dumps(status2, indent=2))
    
    # Test 8: View all orders
    print("\n8. Final view of all orders")
    final_orders = server.get_all_orders()
    print(json.dumps(final_orders, indent=2))


async def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 80)
    print("ERROR HANDLING TEST")
    print("=" * 80)
    
    server = get_mcp_server()
    
    # Test 1: Invalid stock symbol
    print("\n1. Query invalid stock (INVALID)")
    result = server.get_stock_price("INVALID")
    print(json.dumps(result, indent=2))
    
    # Test 2: Invalid order quantity
    print("\n2. Place order with 0 quantity")
    result = server.place_order("JKH", 0, "BUY")
    print(json.dumps(result, indent=2))
    
    # Test 3: Cancel non-existent order
    print("\n3. Cancel non-existent order")
    result = server.cancel_order("INVALID123")
    print(json.dumps(result, indent=2))


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MCP TRADING SERVER TEST SUITE" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        # Run tests
        await test_stock_queries()
        await test_budget_calculator()
        await test_order_management()
        await test_error_handling()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
