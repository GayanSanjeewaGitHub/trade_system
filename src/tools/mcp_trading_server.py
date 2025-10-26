"""
Advanced MCP Server for CSE Trading Operations
Provides stock data, order management, and budget calculations
"""

import asyncio
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class StockData:
    """Stock data model"""
    symbol: str
    name: str
    last_price: float
    change: float
    change_percent: float
    volume: int
    turnover: float
    high: float
    low: float
    open: float
    market_cap: float
    sector: str


@dataclass
class Order:
    """Trading order model"""
    order_id: str
    symbol: str
    quantity: int
    order_type: str  # BUY or SELL
    price: float
    status: OrderStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    total_amount: float = 0.0
    fees: Dict[str, float] = None


class CSEFees:
    """CSE trading fees calculator"""
    BROKER_COMMISSION_RATE = 0.004  # 0.4%
    BROKER_MIN_COMMISSION = 100.0  # LKR 100 minimum
    
    SEC_LEVY_RATE = 0.001  # 0.1%
    CDS_FEE_RATE = 0.00015  # 0.015%
    STAMP_DUTY_RATE = 0.003  # 0.3%
    
    VAT_RATE = 0.18  # 18% VAT on broker commission
    
    @classmethod
    def calculate_fees(cls, transaction_value: float) -> Dict[str, float]:
        """Calculate all trading fees"""
        # Broker commission (with minimum)
        broker_commission = max(
            transaction_value * cls.BROKER_COMMISSION_RATE,
            cls.BROKER_MIN_COMMISSION
        )
        
        # VAT on broker commission
        vat = broker_commission * cls.VAT_RATE
        
        # SEC levy
        sec_levy = transaction_value * cls.SEC_LEVY_RATE
        
        # CDS fee
        cds_fee = transaction_value * cls.CDS_FEE_RATE
        
        # Stamp duty
        stamp_duty = transaction_value * cls.STAMP_DUTY_RATE
        
        total_fees = broker_commission + vat + sec_levy + cds_fee + stamp_duty
        
        return {
            "broker_commission": round(broker_commission, 2),
            "vat": round(vat, 2),
            "sec_levy": round(sec_levy, 2),
            "cds_fee": round(cds_fee, 2),
            "stamp_duty": round(stamp_duty, 2),
            "total_fees": round(total_fees, 2),
            "transaction_value": round(transaction_value, 2),
            "total_cost": round(transaction_value + total_fees, 2)
        }


class MCPTradingServer:
    """MCP Server for trading operations"""
    
    def __init__(self, data_file: str):
        self.data_file = Path(data_file)
        self.stock_data: Dict[str, StockData] = {}
        self.order_queue: List[Order] = []
        self.processed_orders: List[Order] = []
        self.order_counter = 0
        self.processing_task = None
        
        self.load_stock_data()
    
    def load_stock_data(self):
        """Load stock data from CSV file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip empty rows and comments
                    if not row.get('symbol') or row['symbol'].startswith('#'):
                        continue
                    
                    stock = StockData(
                        symbol=row['symbol'].strip(),
                        name=row['name'].strip(),
                        last_price=float(row['last_price']),
                        change=float(row['change']),
                        change_percent=float(row['change_percent']),
                        volume=int(row['volume']),
                        turnover=float(row['turnover']),
                        high=float(row['high']),
                        low=float(row['low']),
                        open=float(row['open']),
                        market_cap=float(row['market_cap']),
                        sector=row['sector'].strip()
                    )
                    self.stock_data[stock.symbol] = stock
            
            logger.info(f"Loaded {len(self.stock_data)} stocks from {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to load stock data: {e}")
            self.stock_data = {}
    
    async def start_order_processor(self):
        """Start background order processor"""
        if self.processing_task is None:
            self.processing_task = asyncio.create_task(self._process_orders())
            logger.info("Order processor started")
    
    async def _process_orders(self):
        """Process orders in queue (3 minutes delay)"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                current_time = datetime.now()
                
                for order in self.order_queue[:]:
                    # Process orders older than 3 minutes
                    if current_time - order.created_at >= timedelta(minutes=3):
                        # Check if stock price is still valid
                        stock = self.stock_data.get(order.symbol)
                        
                        if stock and order.status == OrderStatus.PENDING:
                            order.status = OrderStatus.COMPLETED
                            order.processed_at = current_time
                            self.order_queue.remove(order)
                            self.processed_orders.append(order)
                            
                            logger.info(f"Order {order.order_id} completed: {order.order_type} {order.quantity} {order.symbol} @ {order.price}")
                        else:
                            order.status = OrderStatus.REJECTED
                            order.processed_at = current_time
                            self.order_queue.remove(order)
                            self.processed_orders.append(order)
                            
                            logger.info(f"Order {order.order_id} rejected")
            
            except Exception as e:
                logger.error(f"Error processing orders: {e}")
    
    def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """Get current stock price"""
        stock = self.stock_data.get(symbol.upper())
        if stock:
            return {
                "symbol": stock.symbol,
                "name": stock.name,
                "price": stock.last_price,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "volume": stock.volume,
                "high": stock.high,
                "low": stock.low,
                "open": stock.open,
                "market_cap": stock.market_cap,
                "sector": stock.sector,
                "status": "success"
            }
        return {
            "symbol": symbol,
            "status": "not_found",
            "message": f"Stock {symbol} not found in database. Use internet search tool."
        }
    
    def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """Get top gaining stocks"""
        sorted_stocks = sorted(
            self.stock_data.values(),
            key=lambda x: x.change_percent,
            reverse=True
        )
        
        return [
            {
                "rank": i + 1,
                "symbol": stock.symbol,
                "name": stock.name,
                "price": stock.last_price,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "volume": stock.volume
            }
            for i, stock in enumerate(sorted_stocks[:limit])
        ]
    
    def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """Get top losing stocks"""
        sorted_stocks = sorted(
            self.stock_data.values(),
            key=lambda x: x.change_percent
        )
        
        return [
            {
                "rank": i + 1,
                "symbol": stock.symbol,
                "name": stock.name,
                "price": stock.last_price,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "volume": stock.volume
            }
            for i, stock in enumerate(sorted_stocks[:limit])
        ]
    
    def get_sector_performance(self) -> List[Dict]:
        """Get sector-wise performance"""
        sector_data = {}
        
        for stock in self.stock_data.values():
            if stock.sector not in sector_data:
                sector_data[stock.sector] = {
                    "total_change": 0,
                    "count": 0,
                    "stocks": []
                }
            
            sector_data[stock.sector]["total_change"] += stock.change_percent
            sector_data[stock.sector]["count"] += 1
            sector_data[stock.sector]["stocks"].append(stock.symbol)
        
        result = []
        for sector, data in sector_data.items():
            avg_change = data["total_change"] / data["count"] if data["count"] > 0 else 0
            result.append({
                "sector": sector,
                "avg_change_percent": round(avg_change, 2),
                "stock_count": data["count"],
                "top_stocks": data["stocks"][:5]
            })
        
        return sorted(result, key=lambda x: x["avg_change_percent"], reverse=True)
    
    def calculate_budget(
        self,
        symbol: str,
        quantity: int,
        order_type: str = "BUY"
    ) -> Dict:
        """Calculate total budget required for a trade"""
        stock = self.stock_data.get(symbol.upper())
        
        if not stock:
            return {
                "status": "error",
                "message": f"Stock {symbol} not found"
            }
        
        transaction_value = stock.last_price * quantity
        fees = CSEFees.calculate_fees(transaction_value)
        
        return {
            "status": "success",
            "symbol": stock.symbol,
            "name": stock.name,
            "quantity": quantity,
            "price_per_share": stock.last_price,
            "order_type": order_type,
            **fees,
            "breakdown": {
                "share_cost": round(transaction_value, 2),
                "broker_commission": fees["broker_commission"],
                "vat_on_commission": fees["vat"],
                "sec_levy": fees["sec_levy"],
                "cds_fee": fees["cds_fee"],
                "stamp_duty": fees["stamp_duty"]
            }
        }
    
    def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str = "BUY"
    ) -> Dict:
        """Place a trading order"""
        stock = self.stock_data.get(symbol.upper())
        
        if not stock:
            return {
                "status": "error",
                "message": f"Stock {symbol} not found"
            }
        
        if quantity <= 0:
            return {
                "status": "error",
                "message": "Quantity must be greater than 0"
            }
        
        # Generate order ID
        self.order_counter += 1
        order_id = f"ORD{datetime.now().strftime('%Y%m%d')}{self.order_counter:06d}"
        
        # Calculate costs
        transaction_value = stock.last_price * quantity
        fees = CSEFees.calculate_fees(transaction_value)
        
        # Create order
        order = Order(
            order_id=order_id,
            symbol=stock.symbol,
            quantity=quantity,
            order_type=order_type.upper(),
            price=stock.last_price,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            total_amount=fees["total_cost"],
            fees=fees
        )
        
        # Add to queue
        self.order_queue.append(order)
        
        logger.info(f"Order placed: {order_id} - {order_type} {quantity} {symbol} @ {stock.last_price}")
        
        return {
            "status": "success",
            "message": "Order placed successfully",
            "order_id": order_id,
            "symbol": stock.symbol,
            "name": stock.name,
            "quantity": quantity,
            "price_per_share": stock.last_price,
            "order_type": order_type.upper(),
            "order_status": "PENDING",
            "total_cost": fees["total_cost"],
            "estimated_processing_time": "3 minutes",
            "can_cancel": True,
            "fees": fees
        }
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel a pending order"""
        # Find order in queue
        for order in self.order_queue:
            if order.order_id == order_id:
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CANCELLED
                    order.processed_at = datetime.now()
                    self.order_queue.remove(order)
                    self.processed_orders.append(order)
                    
                    logger.info(f"Order cancelled: {order_id}")
                    
                    return {
                        "status": "success",
                        "message": f"Order {order_id} cancelled successfully",
                        "order_id": order_id,
                        "refund_amount": order.total_amount
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Order {order_id} cannot be cancelled. Status: {order.status.value}"
                    }
        
        # Check processed orders
        for order in self.processed_orders:
            if order.order_id == order_id:
                return {
                    "status": "error",
                    "message": f"Order {order_id} already processed. Status: {order.status.value}",
                    "order_status": order.status.value
                }
        
        return {
            "status": "error",
            "message": f"Order {order_id} not found"
        }
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        # Check pending orders
        for order in self.order_queue:
            if order.order_id == order_id:
                time_remaining = timedelta(minutes=3) - (datetime.now() - order.created_at)
                
                return {
                    "status": "success",
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "price": order.price,
                    "order_type": order.order_type,
                    "order_status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                    "time_remaining_seconds": max(0, int(time_remaining.total_seconds())),
                    "can_cancel": order.status == OrderStatus.PENDING,
                    "total_amount": order.total_amount
                }
        
        # Check processed orders
        for order in self.processed_orders:
            if order.order_id == order_id:
                return {
                    "status": "success",
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "price": order.price,
                    "order_type": order.order_type,
                    "order_status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                    "processed_at": order.processed_at.isoformat() if order.processed_at else None,
                    "can_cancel": False,
                    "total_amount": order.total_amount
                }
        
        return {
            "status": "error",
            "message": f"Order {order_id} not found"
        }
    
    def get_all_orders(self, status_filter: Optional[str] = None) -> Dict:
        """Get all orders with optional status filter"""
        all_orders = self.order_queue + self.processed_orders
        
        if status_filter:
            filtered = [o for o in all_orders if o.status.value == status_filter.lower()]
        else:
            filtered = all_orders
        
        return {
            "status": "success",
            "total_orders": len(filtered),
            "orders": [
                {
                    "order_id": o.order_id,
                    "symbol": o.symbol,
                    "quantity": o.quantity,
                    "price": o.price,
                    "order_type": o.order_type,
                    "status": o.status.value,
                    "total_amount": o.total_amount,
                    "created_at": o.created_at.isoformat()
                }
                for o in sorted(filtered, key=lambda x: x.created_at, reverse=True)
            ]
        }


# Global server instance
_server: Optional[MCPTradingServer] = None


def get_mcp_server() -> MCPTradingServer:
    """Get or create MCP server instance"""
    global _server
    if _server is None:
        data_file = Path(__file__).parent.parent / "data" / "cse_stock_data.csv"
        _server = MCPTradingServer(str(data_file))
        # Start order processor
        asyncio.create_task(_server.start_order_processor())
    return _server


# MCP Tool Functions (for agent integration)

async def mcp_get_stock_price(symbol: str) -> Dict:
    """MCP Tool: Get stock price"""
    server = get_mcp_server()
    return server.get_stock_price(symbol)


async def mcp_get_top_gainers(limit: int = 10) -> List[Dict]:
    """MCP Tool: Get top gaining stocks"""
    server = get_mcp_server()
    return server.get_top_gainers(limit)


async def mcp_get_top_losers(limit: int = 10) -> List[Dict]:
    """MCP Tool: Get top losing stocks"""
    server = get_mcp_server()
    return server.get_top_losers(limit)


async def mcp_get_sector_performance() -> List[Dict]:
    """MCP Tool: Get sector performance"""
    server = get_mcp_server()
    return server.get_sector_performance()


async def mcp_calculate_budget(symbol: str, quantity: int, order_type: str = "BUY") -> Dict:
    """MCP Tool: Calculate trading budget"""
    server = get_mcp_server()
    return server.calculate_budget(symbol, quantity, order_type)


async def mcp_place_order(symbol: str, quantity: int, order_type: str = "BUY") -> Dict:
    """MCP Tool: Place trading order"""
    server = get_mcp_server()
    return server.place_order(symbol, quantity, order_type)


async def mcp_cancel_order(order_id: str) -> Dict:
    """MCP Tool: Cancel pending order"""
    server = get_mcp_server()
    return server.cancel_order(order_id)


async def mcp_get_order_status(order_id: str) -> Dict:
    """MCP Tool: Get order status"""
    server = get_mcp_server()
    return server.get_order_status(order_id)


async def mcp_get_all_orders(status_filter: Optional[str] = None) -> Dict:
    """MCP Tool: Get all orders"""
    server = get_mcp_server()
    return server.get_all_orders(status_filter)


if __name__ == "__main__":
    # Test the server
    async def test_server():
        server = get_mcp_server()
        await server.start_order_processor()
        
        print("\n=== Stock Price ===")
        print(server.get_stock_price("JKH"))
        
        print("\n=== Top Gainers ===")
        gainers = server.get_top_gainers(5)
        for g in gainers:
            print(f"{g['rank']}. {g['symbol']} ({g['name']}): +{g['change_percent']}%")
        
        print("\n=== Top Losers ===")
        losers = server.get_top_losers(5)
        for l in losers:
            print(f"{l['rank']}. {l['symbol']} ({l['name']}): {l['change_percent']}%")
        
        print("\n=== Budget Calculation ===")
        budget = server.calculate_budget("JKH", 1000, "BUY")
        print(json.dumps(budget, indent=2))
        
        print("\n=== Place Order ===")
        order = server.place_order("DIAL", 500, "BUY")
        print(json.dumps(order, indent=2))
        
        # Wait a bit
        await asyncio.sleep(2)
        
        print("\n=== Order Status ===")
        status = server.get_order_status(order["order_id"])
        print(json.dumps(status, indent=2))
        
        print("\n=== Cancel Order ===")
        cancel = server.cancel_order(order["order_id"])
        print(json.dumps(cancel, indent=2))
    
    asyncio.run(test_server())
