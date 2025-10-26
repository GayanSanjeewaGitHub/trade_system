"""
Evaluation Runner Script
Run ground truth evaluation from project root.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main evaluation
from src.monitoring.evaluate_groundtruth import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
