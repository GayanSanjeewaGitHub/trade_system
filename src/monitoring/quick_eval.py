"""
Quick Evaluation Script
Run a subset of ground truth tests for rapid validation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.monitoring.evaluate_groundtruth import GroundTruthEvaluator


async def quick_test():
    """Run quick evaluation on first 5 test cases."""
    print("\n🚀 Quick Evaluation Test\n")
    
    evaluator = GroundTruthEvaluator()
    
    try:
        await evaluator.initialize()
        
        # Load ground truth (path relative to project root)
        project_root = Path(__file__).parent.parent.parent
        ground_truth_path = project_root / "src" / "data" / "ground_truth.py" / "test_qa_pairs.json"
        ground_truth = await evaluator.load_ground_truth(str(ground_truth_path))
        
        if not ground_truth:
            print("❌ No ground truth data found!")
            return
        
        # Run on first 5 cases
        print(f"Testing first 5 out of {len(ground_truth)} total cases\n")
        report = await evaluator.evaluate_all(ground_truth, limit=5)
        
        print(f"\n✨ Quick Test Complete!")
        print(f"Pass Rate: {report['summary']['pass_rate']}%")
        
        # Cleanup
        await evaluator.controller.cleanup()
        
    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(quick_test())
