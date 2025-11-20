#!/usr/bin/env python3
"""
Test script for Robot Vacuum Depot Analytics
Tests all sample queries and reports performance metrics
"""

import time
import sys
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from agentic_processor.query_processor import QueryProcessor
from my_agent.metrics import metrics_tracker

# Sample queries to test
TEST_QUERIES = [
    # Tabular/Text Queries
    "Which robot vacuum models have the highest number of delayed deliveries across all Chicago ZIP codes?",
    "Which warehouses are currently below their restock threshold based on stock level and capacity?",
    "Which Zip code has the highest number of delayed deliveries?",
    "Among all manufacturers, who has the best average review rating for their products?",

    # Chart Queries
    "Plot a line chart of total monthly revenue to visualize sales trends over time.",
    "What is the percentage distribution of delivery statuses across all orders?",
    "Plot the average review rating per manufacturer to analyze product satisfaction by brand.",
    "Compare average shipping cost by carrier to evaluate cost efficiency.",

    # Additional test queries
    "What are the top 5 best-selling products?",
    "Show the total revenue by customer segment",
]

def test_query(processor: QueryProcessor, query: str, index: int) -> dict:
    """Test a single query and return results"""
    print(f"\n{'='*60}")
    print(f"Test {index + 1}: {query[:60]}...")
    print('='*60)

    start_time = time.time()
    result = processor.process_natural_language(query)
    elapsed = time.time() - start_time

    status = result.get('status', 'unknown')
    sql = result.get('sql_query', 'N/A')
    chart_type = result.get('chart_type', 'none')
    data = result.get('data')
    message = result.get('message', '')

    # Determine result status
    if status == 'error':
        test_status = 'FAILED'
        row_count = 0
    elif data is not None and not data.empty:
        test_status = 'PASSED'
        row_count = len(data)
    elif message:
        test_status = 'NO DATA'
        row_count = 0
    else:
        test_status = 'UNKNOWN'
        row_count = 0

    print(f"Status: {test_status}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Chart Type: {chart_type}")
    print(f"Rows: {row_count}")

    if sql and sql != 'N/A':
        # Truncate SQL for display
        sql_display = sql[:200] + '...' if len(sql) > 200 else sql
        print(f"SQL: {sql_display}")

    if message:
        print(f"Message: {message[:100]}")

    if status == 'error':
        print(f"Error: {message}")

    return {
        'query': query,
        'status': test_status,
        'time': elapsed,
        'chart_type': chart_type,
        'rows': row_count,
        'sql': sql,
        'error': message if status == 'error' else None
    }

def run_tests():
    """Run all test queries and generate report"""
    print("\n" + "="*60)
    print("ROBOT VACUUM DEPOT ANALYTICS - TEST SUITE")
    print("="*60)

    processor = QueryProcessor()
    results = []

    total_start = time.time()

    for i, query in enumerate(TEST_QUERIES):
        try:
            result = test_query(processor, query, i)
            results.append(result)
        except Exception as e:
            print(f"EXCEPTION: {str(e)}")
            results.append({
                'query': query,
                'status': 'EXCEPTION',
                'time': 0,
                'chart_type': 'none',
                'rows': 0,
                'sql': '',
                'error': str(e)
            })

    total_time = time.time() - total_start

    # Generate summary report
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for r in results if r['status'] == 'PASSED')
    no_data = sum(1 for r in results if r['status'] == 'NO DATA')
    failed = sum(1 for r in results if r['status'] in ['FAILED', 'EXCEPTION'])

    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"No Data: {no_data}")
    print(f"Failed: {failed}")
    print(f"\nTotal Time: {total_time:.2f}s")
    print(f"Avg Time per Query: {total_time/len(results):.2f}s")

    # Performance metrics
    times = [r['time'] for r in results]
    under_5s = sum(1 for t in times if t < 5)
    under_3s = sum(1 for t in times if t < 3)

    print(f"\nPerformance:")
    print(f"  Under 5s: {under_5s}/{len(results)} ({under_5s/len(results)*100:.1f}%)")
    print(f"  Under 3s: {under_3s}/{len(results)} ({under_3s/len(results)*100:.1f}%)")
    print(f"  Min Time: {min(times):.2f}s")
    print(f"  Max Time: {max(times):.2f}s")

    # Chart type distribution
    chart_types = {}
    for r in results:
        ct = r['chart_type']
        chart_types[ct] = chart_types.get(ct, 0) + 1

    print(f"\nChart Types:")
    for ct, count in sorted(chart_types.items()):
        print(f"  {ct}: {count}")

    # Failed queries details
    if failed > 0:
        print(f"\nFailed Queries:")
        for r in results:
            if r['status'] in ['FAILED', 'EXCEPTION']:
                print(f"  - {r['query'][:50]}...")
                if r['error']:
                    print(f"    Error: {r['error'][:100]}")

    # Get analytics from metrics tracker
    print("\n" + "="*60)
    print("METRICS TRACKER ANALYTICS")
    print("="*60)

    analytics = metrics_tracker.get_analytics()
    print(f"\nTotal Queries Tracked: {analytics['total_queries']}")
    print(f"Success Rate: {analytics['success_rate']}%")
    print(f"Avg Response Time: {analytics['avg_response_time']}s")
    print(f"Queries Under 5s: {analytics['queries_under_5s']}%")

    # Save results to JSON file for web dashboard
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': len(results),
            'passed': passed,
            'no_data': no_data,
            'failed': failed,
            'total_time': round(total_time, 2),
            'avg_time': round(total_time / len(results), 2),
            'under_5s_percent': round((under_5s / len(results)) * 100, 1),
            'under_3s_percent': round((under_3s / len(results)) * 100, 1),
            'min_time': round(min(times), 2),
            'max_time': round(max(times), 2),
        },
        'chart_distribution': chart_types,
        'analytics': analytics,
        'queries': [
            {
                'query': r['query'],
                'status': r['status'],
                'time': round(r['time'], 2),
                'chart_type': r['chart_type'],
                'rows': r['rows'],
                'error': r.get('error')
            }
            for r in results
        ]
    }

    # Save to file
    results_file = 'test_results.json'
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n✅ Results saved to {results_file}")

    return results

if __name__ == "__main__":
    try:
        results = run_tests()

        # Exit with error code if any tests failed
        failed = sum(1 for r in results if r['status'] in ['FAILED', 'EXCEPTION'])
        sys.exit(1 if failed > 0 else 0)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite failed with error: {e}")
        sys.exit(1)
