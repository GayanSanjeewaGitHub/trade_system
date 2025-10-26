"""
Quick Evaluation Runner Script
Run quick evaluation (first 5 test cases) from project root.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the quick evaluation
from src.monitoring.quick_eval import quick_test
import asyncio

if __name__ == "__main__":
    asyncio.run(quick_test())
