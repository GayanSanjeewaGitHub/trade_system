"""
Auto-evaluation script for chatbot responses.
Evaluates accuracy, relevance, and performance metrics.
"""

import time
import json
from typing import List, Dict, Any
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.evaluation import load_evaluator

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class AutoEvaluator:
    """Automated evaluation system for chatbot responses."""
    
    def __init__(self):
        self.llm: ChatOpenAI = None
        self.embeddings: OpenAIEmbeddings = None
        self.results_history: List[Dict[str, Any]] = []
        
    async def initialize(self) -> None:
        """Initialize evaluation components."""
        try:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.0,
                api_key=settings.openai_api_key
            )
            
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=settings.openai_api_key
            )
            
            logger.info("Auto-evaluator initialized")
            
        except Exception as e:
            logger.error("Failed to initialize evaluator", error=str(e))
            raise
    
    async def evaluate(self, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluate chatbot responses against test cases.
        
        Args:
            test_cases: List of test cases with questions and expected answers
            
        Returns:
            Evaluation results with metrics
        """
        logger.info("Starting evaluation", test_count=len(test_cases))
        
        results = []
        total_latency = 0.0
        
        for i, test_case in enumerate(test_cases):
            try:
                start_time = time.time()
                
                # Get actual response from chatbot
                # In production, this would call the controller agent
                actual_answer = await self._get_chatbot_response(test_case["question"])
                
                latency = (time.time() - start_time) * 1000
                total_latency += latency
                
                # Evaluate response
                score = await self._evaluate_response(
                    test_case["question"],
                    test_case["expected_answer"],
                    actual_answer
                )
                
                passed = score >= 0.7  # Threshold for passing
                
                result = {
                    "question": test_case["question"],
                    "expected_answer": test_case["expected_answer"],
                    "actual_answer": actual_answer,
                    "score": score,
                    "latency_ms": latency,
                    "passed": passed,
                    "category": test_case.get("category", "general")
                }
                
                results.append(result)
                
                logger.info(
                    "Test case evaluated",
                    index=i+1,
                    score=score,
                    passed=passed,
                    latency_ms=latency
                )
                
            except Exception as e:
                logger.error("Test case evaluation failed", index=i, error=str(e))
                results.append({
                    "question": test_case["question"],
                    "error": str(e),
                    "passed": False
                })
        
        # Calculate metrics
        passed_count = sum(1 for r in results if r.get("passed", False))
        total_count = len(results)
        
        precision = passed_count / total_count if total_count > 0 else 0.0
        recall = precision  # Simplified - in production would be more complex
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        avg_latency = total_latency / total_count if total_count > 0 else 0.0
        
        evaluation_result = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "avg_latency": round(avg_latency, 2),
            "test_results": results,
            "summary": {
                "total_tests": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
                "pass_rate": round(precision * 100, 2)
            }
        }
        
        # Store results
        self.results_history.append(evaluation_result)
        await self._save_results(evaluation_result)
        
        logger.info(
            "Evaluation complete",
            precision=precision,
            passed=passed_count,
            total=total_count
        )
        
        return evaluation_result
    
    async def _get_chatbot_response(self, question: str) -> str:
        """
        Get chatbot response for a question.
        In production, this would call the controller agent.
        """
        try:
            # Mock implementation - replace with actual agent call
            from src.agents.controller import ControllerAgent
            
            controller = ControllerAgent()
            await controller.initialize()
            
            result = await controller.process_message(
                message=question,
                session_id="eval-session",
                user_id="evaluator"
            )
            
            return result.get("response", "")
            
        except Exception as e:
            logger.error("Failed to get chatbot response", error=str(e))
            return f"Error: {str(e)}"
    
    async def _evaluate_response(
        self,
        question: str,
        expected: str,
        actual: str
    ) -> float:
        """
        Evaluate response quality using semantic similarity.
        
        Returns:
            Score between 0 and 1
        """
        try:
            # Use embedding-based similarity
            expected_embedding = await self.embeddings.aembed_query(expected)
            actual_embedding = await self.embeddings.aembed_query(actual)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(expected_embedding, actual_embedding)
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error("Response evaluation failed", error=str(e))
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def _save_results(self, results: Dict[str, Any]) -> None:
        """Save evaluation results to file."""
        try:
            results_dir = Path("logs/evaluations")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"evaluation_{timestamp}.json"
            
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
            
            logger.info("Evaluation results saved", filename=str(filename))
            
        except Exception as e:
            logger.error("Failed to save results", error=str(e))
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all evaluation metrics."""
        if not self.results_history:
            return {"message": "No evaluation results available"}
        
        total_evals = len(self.results_history)
        avg_precision = sum(r["precision"] for r in self.results_history) / total_evals
        avg_f1 = sum(r["f1_score"] for r in self.results_history) / total_evals
        
        return {
            "total_evaluations": total_evals,
            "avg_precision": round(avg_precision, 3),
            "avg_f1_score": round(avg_f1, 3),
            "latest_result": self.results_history[-1] if self.results_history else None
        }