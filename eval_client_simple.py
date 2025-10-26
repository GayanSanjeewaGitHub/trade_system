"""
Ground Truth Evaluation Client (No External Dependencies)
Simple script to trigger ground truth evaluation via API using only standard library.
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from typing import Optional


def run_evaluation(
    base_url: str = "http://localhost:8000",
    limit: Optional[int] = None,
    verbose: bool = True
) -> dict:
    """
    Trigger ground truth evaluation via API.
    
    Args:
        base_url: Base URL of the API server
        limit: Optional limit on number of test cases
        verbose: Whether to print detailed output
        
    Returns:
        Evaluation results dictionary
    """
    endpoint = f"{base_url}/evaluate/groundtruth"
    
    if verbose:
        print("=" * 80)
        print("🤖 Ground Truth Evaluation via API")
        print("=" * 80)
        print(f"\n📡 Connecting to: {endpoint}")
        if limit:
            print(f"📊 Test limit: {limit} cases")
        print()
    
    try:
        # Build request URL with params
        if limit:
            url = f"{endpoint}?{urlencode({'limit': limit})}"
        else:
            url = endpoint
        
        # Send request
        if verbose:
            print("⏳ Sending evaluation request...")
            print("   (This may take a few minutes...)")
            print()
        
        req = Request(url)
        req.add_header('Content-Type', 'application/json')
        
        with urlopen(req, timeout=600) as response:
            if response.status == 200:
                data = response.read()
                results = json.loads(data.decode('utf-8'))
                
                if verbose:
                    print_results(results)
                
                return results
            else:
                error_msg = f"API request failed with status {response.status}"
                print(f"\n❌ Error: {error_msg}")
                return None
    
    except HTTPError as e:
        error_msg = f"HTTP Error {e.code}"
        try:
            error_detail = json.loads(e.read().decode('utf-8')).get('detail', 'Unknown error')
            error_msg += f": {error_detail}"
        except:
            pass
        
        print(f"\n❌ Error: {error_msg}")
        return None
    
    except URLError as e:
        print(f"\n❌ Error: Could not connect to {base_url}")
        print("   Make sure the backend is running:")
        print("   docker-compose -f docker/docker-compose.yml up -d")
        return None
    
    except TimeoutError:
        print(f"\n❌ Error: Request timed out")
        print("   Evaluation takes time. Try with a smaller limit parameter.")
        return None
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def print_results(results: dict):
    """Print formatted evaluation results."""
    summary = results.get('summary', {})
    test_results = results.get('results', [])
    
    print("\n✅ Evaluation complete!")
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    print(f"\nOverall Performance:")
    print(f"  • Total Tests: {summary.get('total_tests', 0)}")
    print(f"  • Passed: {summary.get('passed', 0)}")
    print(f"  • Failed: {summary.get('failed', 0)}")
    print(f"  • Pass Rate: {summary.get('pass_rate', 0)}%")
    
    print(f"\nQuality Metrics:")
    print(f"  • Avg Similarity: {summary.get('avg_similarity', 0):.4f}")
    print(f"  • Avg Latency: {summary.get('avg_latency_ms', 0):.2f} ms")
    
    category_breakdown = summary.get('category_breakdown', {})
    if category_breakdown:
        print(f"\nCategory Breakdown:")
        for cat, data in category_breakdown.items():
            print(f"  • {cat.upper()}: {data['passed']}/{data['total']} ({data['pass_rate']}%)")
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED RESULTS")
    print("=" * 80)
    
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result.get('passed') else "❌ FAIL"
        score = result.get('similarity_score', 0)
        latency = result.get('latency_ms', 0)
        
        print(f"\n[{i}] {result.get('question', 'N/A')[:70]}...")
        print(f"    {status} | Score: {score:.3f} | Latency: {latency:.0f}ms")
        print(f"    Category: {result.get('category', 'general')}")
        
        # Show answer preview for failed tests
        if not result.get('passed'):
            actual = result.get('actual_answer', '')[:150]
            expected = result.get('expected_answer', '')[:150]
            print(f"    Expected: {expected}...")
            print(f"    Actual:   {actual}...")
    
    print("\n" + "=" * 80)


def save_results(results: dict, filename: str = "evaluation_results.json"):
    """Save results to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {filename}")
    except Exception as e:
        print(f"\n⚠️  Failed to save results: {e}")


def main():
    """Main function with CLI argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run ground truth evaluation via API"
    )
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the API server (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of test cases (for quick testing)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to JSON file'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    results = run_evaluation(
        base_url=args.url,
        limit=args.limit,
        verbose=not args.quiet
    )
    
    if results and args.save:
        save_results(results)
    
    # Exit with appropriate code
    if results:
        pass_rate = results.get('summary', {}).get('pass_rate', 0)
        if pass_rate < 80:
            print(f"\n⚠️  Warning: Pass rate ({pass_rate}%) is below 80% threshold")
            sys.exit(1)
        else:
            sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
