import pandas as pd
from typing import Dict, Any
import uuid
import time

from my_agent.WorkflowManager import WorkflowManager
from my_agent.metrics import metrics_tracker

class QueryProcessor:
    def __init__(self):
        self.workflow_manager = WorkflowManager()

    def process_natural_language(self, query: str) -> Dict[str, Any]:
        # Check cache first
        cached = metrics_tracker.get_cached_result(query)
        if cached:
            return cached

        # Generate a unique session ID
        session_uuid = str(uuid.uuid4())

        # Start tracking metrics
        metrics_tracker.start_query(session_uuid, query)
        start_time = time.time()

        try:
            # Run the SQL agent workflow
            result = self.workflow_manager.run_sql_agent(query, session_uuid)

            print(f"Generated SQL: {result.get('sql_query')}")
            print(f"Detected Chart Type: {result.get('visualization')}")

            # Convert raw results to DataFrame
            raw_results = result.get('raw_results')
            sql_query = result.get('sql_query', '')

            # Check for NOT_RELEVANT or None (but not empty list)
            if raw_results == "NOT_RELEVANT" or raw_results is None:
                metrics_tracker.complete_query(
                    session_uuid, success=True,
                    sql_generated=sql_query, chart_type="none", results_count=0
                )
                return {
                    "status": "success",
                    "message": result.get('answer', 'No data found for this query.'),
                    "sql_query": sql_query,
                    "chart_type": "none",
                    "data": None
                }

            # Check for empty results list
            if isinstance(raw_results, list) and len(raw_results) == 0:
                metrics_tracker.complete_query(
                    session_uuid, success=True,
                    sql_generated=sql_query, chart_type="none", results_count=0
                )
                return {
                    "status": "success",
                    "message": result.get('answer', 'Query executed but returned no results.'),
                    "sql_query": sql_query,
                    "chart_type": "none",
                    "data": None
                }

            # Convert results to DataFrame
            if isinstance(raw_results, list) and len(raw_results) > 0:
                # Create DataFrame from results
                df = pd.DataFrame(raw_results)
            else:
                df = pd.DataFrame()

            if df.empty:
                return {
                    "status": "success",
                    "message": "No data found for this query.",
                    "sql_query": sql_query,
                    "chart_type": "none",
                    "data": None
                }

            # Map visualization type to chart type
            viz_type = result.get('visualization', 'table')
            if viz_type == 'horizontal_bar':
                chart_type = 'bar'
            elif viz_type == 'none':
                chart_type = 'table'
            else:
                chart_type = viz_type

            # Complete metrics tracking
            metrics_tracker.complete_query(
                session_uuid, success=True,
                sql_generated=sql_query, chart_type=chart_type,
                results_count=len(df)
            )
            # Save session analytics
            metrics_tracker.save_to_file()

            response = {
                "status": "success",
                "sql_query": sql_query,
                "chart_type": chart_type,
                "data": df,
                "answer": result.get('answer'),
                "formatted_data": result.get('formatted_data_for_visualization')
            }

            # Cache the result
            metrics_tracker.cache_result(query, response)

            return response

        except Exception as e:
            # Track failed query
            metrics_tracker.complete_query(
                session_uuid, success=False, error=str(e)
            )
            return {
                "status": "error",
                "message": str(e),
                "sql_query": ""
            }
