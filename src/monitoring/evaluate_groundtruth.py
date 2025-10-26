"""
Ground Truth Evaluation Script
Compares agent responses against ground-truth Q&A pairs and generates detailed reports.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.controller import ControllerAgent
from src.config.settings import settings
from src.monitoring.logger import get_logger
from langchain_openai import OpenAIEmbeddings
import numpy as np

logger = get_logger(__name__)


class GroundTruthEvaluator:
    """Evaluates agent responses against ground truth Q&A pairs."""
    
    def __init__(self):
        self.controller: ControllerAgent = None
        self.embeddings: OpenAIEmbeddings = None
        self.results: List[Dict[str, Any]] = []
        
    async def initialize(self) -> None:
        """Initialize controller and embeddings."""
        print("\n🔧 Initializing evaluation components...")
        
        # Initialize controller agent
        self.controller = ControllerAgent()
        await self.controller.initialize()
        print("✅ Controller agent initialized")
        
        # Initialize embeddings for semantic similarity
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key
        )
        print("✅ Embeddings initialized")
        
    async def load_ground_truth(self, filepath: str) -> List[Dict[str, Any]]:
        """Load ground truth Q&A pairs from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data)} ground truth Q&A pairs")
            return data
        except Exception as e:
            print(f"❌ Failed to load ground truth: {e}")
            return []
    
    async def evaluate_single(
        self,
        question: str,
        expected_answer: str,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Evaluate a single question-answer pair."""
        start_time = time.time()
        
        try:
            # Get agent response
            result = await self.controller.process_message(
                message=question,
                session_id=f"eval_{int(time.time())}",
                user_id="evaluator",
                context={}
            )
            
            actual_answer = result.get("response", "")
            agent_path = result.get("agent_path", [])
            tools_used = result.get("tools_used", [])
            latency_ms = result.get("metadata", {}).get("latency_ms", 0)
            
            # Calculate semantic similarity
            similarity_score = await self._calculate_semantic_similarity(
                expected_answer,
                actual_answer
            )
            
            # Calculate exact match metrics
            exact_match = self._check_exact_match(expected_answer, actual_answer)
            keyword_match = self._calculate_keyword_overlap(expected_answer, actual_answer)
            
            # Determine if passed (threshold: 0.7)
            passed = similarity_score >= 0.7
            
            elapsed_time = (time.time() - start_time) * 1000
            
            return {
                "question": question,
                "expected_answer": expected_answer,
                "actual_answer": actual_answer,
                "category": category,
                "metrics": {
                    "semantic_similarity": round(similarity_score, 4),
                    "exact_match": exact_match,
                    "keyword_overlap": round(keyword_match, 4),
                    "overall_score": round(similarity_score, 4)
                },
                "performance": {
                    "latency_ms": round(latency_ms, 2),
                    "evaluation_time_ms": round(elapsed_time, 2)
                },
                "agent_info": {
                    "agent_path": agent_path,
                    "tools_used": tools_used
                },
                "passed": passed,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Evaluation failed for question", question=question, error=str(e))
            return {
                "question": question,
                "expected_answer": expected_answer,
                "actual_answer": f"ERROR: {str(e)}",
                "category": category,
                "metrics": {
                    "semantic_similarity": 0.0,
                    "exact_match": False,
                    "keyword_overlap": 0.0,
                    "overall_score": 0.0
                },
                "performance": {
                    "latency_ms": 0.0,
                    "evaluation_time_ms": (time.time() - start_time) * 1000
                },
                "agent_info": {
                    "agent_path": [],
                    "tools_used": []
                },
                "passed": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _calculate_semantic_similarity(
        self,
        expected: str,
        actual: str
    ) -> float:
        """Calculate semantic similarity using embeddings."""
        try:
            # Get embeddings
            expected_emb = await self.embeddings.aembed_query(expected)
            actual_emb = await self.embeddings.aembed_query(actual)
            
            # Calculate cosine similarity
            similarity = np.dot(expected_emb, actual_emb) / (
                np.linalg.norm(expected_emb) * np.linalg.norm(actual_emb)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error("Semantic similarity calculation failed", error=str(e))
            return 0.0
    
    def _check_exact_match(self, expected: str, actual: str) -> bool:
        """Check if answers match exactly (case-insensitive)."""
        expected_clean = expected.lower().strip()
        actual_clean = actual.lower().strip()
        return expected_clean == actual_clean
    
    def _calculate_keyword_overlap(self, expected: str, actual: str) -> float:
        """Calculate keyword overlap between expected and actual answers."""
        # Extract keywords (simple approach - words longer than 3 chars)
        import re
        
        def extract_keywords(text: str) -> set:
            words = re.findall(r'\b\w+\b', text.lower())
            return set(w for w in words if len(w) > 3 and w not in {
                'the', 'and', 'that', 'this', 'with', 'from', 'have', 'been',
                'they', 'their', 'which', 'about', 'would', 'could', 'should'
            })
        
        expected_keywords = extract_keywords(expected)
        actual_keywords = extract_keywords(actual)
        
        if not expected_keywords:
            return 0.0
        
        overlap = expected_keywords & actual_keywords
        return len(overlap) / len(expected_keywords)
    
    async def evaluate_all(
        self,
        ground_truth: List[Dict[str, Any]],
        limit: int = None
    ) -> Dict[str, Any]:
        """Evaluate all ground truth pairs."""
        print(f"\n{'='*80}")
        print(f"📊 Starting Ground Truth Evaluation")
        print(f"{'='*80}\n")
        
        test_cases = ground_truth[:limit] if limit else ground_truth
        total = len(test_cases)
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{total}] Evaluating: {test_case['question'][:60]}...")
            
            result = await self.evaluate_single(
                question=test_case['question'],
                expected_answer=test_case['expected_answer'],
                category=test_case.get('category', 'general')
            )
            
            results.append(result)
            
            # Print result
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            score = result['metrics']['semantic_similarity']
            latency = result['performance']['latency_ms']
            
            print(f"   {status} | Score: {score:.3f} | Latency: {latency:.0f}ms")
            
            # Brief answer preview
            actual_preview = result['actual_answer'][:100] + "..." if len(result['actual_answer']) > 100 else result['actual_answer']
            print(f"   Answer: {actual_preview}")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        # Calculate aggregate metrics
        metrics = self._calculate_aggregate_metrics(results)
        
        # Save results
        report = {
            "summary": metrics,
            "results": results,
            "metadata": {
                "total_tests": total,
                "timestamp": datetime.now().isoformat(),
                "settings": {
                    "llm_model": settings.llm_model,
                    "embedding_model": settings.embedding_model,
                    "similarity_threshold": settings.similarity_threshold
                }
            }
        }
        
        self._save_report(report)
        self._print_summary(metrics)
        
        return report
    
    def _calculate_aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics from results."""
        total = len(results)
        passed = sum(1 for r in results if r['passed'])
        failed = total - passed
        
        # Category-wise breakdown
        categories = {}
        for result in results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0, 'avg_score': 0.0}
            
            categories[cat]['total'] += 1
            if result['passed']:
                categories[cat]['passed'] += 1
            categories[cat]['avg_score'] += result['metrics']['semantic_similarity']
        
        # Calculate averages for categories
        for cat in categories:
            categories[cat]['avg_score'] /= categories[cat]['total']
            categories[cat]['avg_score'] = round(categories[cat]['avg_score'], 4)
            categories[cat]['pass_rate'] = round(
                (categories[cat]['passed'] / categories[cat]['total']) * 100, 2
            )
        
        # Overall metrics
        avg_similarity = sum(r['metrics']['semantic_similarity'] for r in results) / total
        avg_keyword_overlap = sum(r['metrics']['keyword_overlap'] for r in results) / total
        avg_latency = sum(r['performance']['latency_ms'] for r in results) / total
        
        # Agent routing accuracy
        agent_paths = [r['agent_info']['agent_path'] for r in results]
        faq_routed = sum(1 for path in agent_paths if 'faq' in path)
        advisor_routed = sum(1 for path in agent_paths if 'advisor' in path)
        
        return {
            "pass_rate": round((passed / total) * 100, 2),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "metrics": {
                "avg_semantic_similarity": round(avg_similarity, 4),
                "avg_keyword_overlap": round(avg_keyword_overlap, 4),
                "avg_latency_ms": round(avg_latency, 2)
            },
            "category_breakdown": categories,
            "agent_routing": {
                "faq_routed": faq_routed,
                "advisor_routed": advisor_routed,
                "faq_percentage": round((faq_routed / total) * 100, 2)
            }
        }
    
    def _save_report(self, report: Dict[str, Any]) -> None:
        """Save evaluation report to file."""
        try:
            # Create reports directory
            reports_dir = Path("logs/evaluations")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Save detailed JSON report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = reports_dir / f"groundtruth_eval_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Detailed report saved: {json_file}")
            
            # Save CSV summary for easy analysis
            csv_file = reports_dir / f"groundtruth_eval_{timestamp}.csv"
            self._save_csv_summary(report['results'], csv_file)
            
            print(f"💾 CSV summary saved: {csv_file}")
            
        except Exception as e:
            logger.error("Failed to save report", error=str(e))
    
    def _save_csv_summary(self, results: List[Dict[str, Any]], filepath: Path) -> None:
        """Save results summary as CSV."""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Question', 'Category', 'Passed', 'Semantic Similarity',
                'Keyword Overlap', 'Latency (ms)', 'Agent Path'
            ])
            
            for r in results:
                writer.writerow([
                    r['question'],
                    r['category'],
                    'PASS' if r['passed'] else 'FAIL',
                    r['metrics']['semantic_similarity'],
                    r['metrics']['keyword_overlap'],
                    r['performance']['latency_ms'],
                    ' -> '.join(r['agent_info']['agent_path'])
                ])
    
    def _print_summary(self, metrics: Dict[str, Any]) -> None:
        """Print evaluation summary."""
        print(f"\n{'='*80}")
        print(f"📈 EVALUATION SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Overall Performance:")
        print(f"  • Total Tests: {metrics['total_tests']}")
        print(f"  • Passed: {metrics['passed']} ({metrics['pass_rate']}%)")
        print(f"  • Failed: {metrics['failed']}")
        print(f"\nQuality Metrics:")
        print(f"  • Avg Semantic Similarity: {metrics['metrics']['avg_semantic_similarity']:.4f}")
        print(f"  • Avg Keyword Overlap: {metrics['metrics']['avg_keyword_overlap']:.4f}")
        print(f"  • Avg Latency: {metrics['metrics']['avg_latency_ms']:.2f} ms")
        
        print(f"\nAgent Routing:")
        print(f"  • FAQ Agent: {metrics['agent_routing']['faq_routed']} ({metrics['agent_routing']['faq_percentage']}%)")
        print(f"  • Advisor Agent: {metrics['agent_routing']['advisor_routed']}")
        
        print(f"\nCategory Breakdown:")
        for cat, data in metrics['category_breakdown'].items():
            print(f"  • {cat.upper()}: {data['passed']}/{data['total']} ({data['pass_rate']}%) | Avg Score: {data['avg_score']:.4f}")
        
        print(f"\n{'='*80}\n")


async def main():
    """Main evaluation function."""
    print("\n" + "="*80)
    print("🤖 Ground Truth Evaluation System")
    print("="*80 + "\n")
    
    evaluator = GroundTruthEvaluator()
    
    try:
        # Initialize
        await evaluator.initialize()
        
        # Load ground truth (path relative to project root)
        project_root = Path(__file__).parent.parent.parent
        ground_truth_path = project_root / "src" / "data" / "ground_truth" / "test_qa_pairs.json"
        ground_truth = await evaluator.load_ground_truth(str(ground_truth_path))
        
        if not ground_truth:
            print("❌ No ground truth data found!")
            return
        
        # Run evaluation (limit to first N for testing, or None for all)
        limit = None  # Set to 5 for quick test, None for full evaluation
        
        report = await evaluator.evaluate_all(ground_truth, limit=limit)
        
        print("\n✅ Evaluation complete!")
        print(f"📊 Pass Rate: {report['summary']['pass_rate']}%")
        
        # Cleanup
        if evaluator.controller:
            await evaluator.controller.cleanup()
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        logger.error("Evaluation failed", error=str(e), exc_info=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
