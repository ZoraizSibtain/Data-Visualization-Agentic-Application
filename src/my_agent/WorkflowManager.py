import time
from langgraph.graph import StateGraph, END
from .State import InputState, OutputState, AgentState
from .SQLAgent import SQLAgent
from .DataFormatter import DataFormatter
from .metrics import metrics_tracker

class WorkflowManager:
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.data_formatter = DataFormatter()

    def create_workflow(self) -> StateGraph:
        """Create and configure the workflow graph.

        Optimized workflow:
        - Removed get_unique_nouns (expensive DB queries)
        - Removed validate_and_fix_sql (redundant with good prompts)
        - Combined format_results + choose_visualization into one call
        """
        workflow = StateGraph(AgentState, input=InputState, output=OutputState)

        # Add nodes to the graph (optimized - fewer LLM calls)
        workflow.add_node("generate_sql", self.sql_agent.generate_sql_direct)
        workflow.add_node("execute_sql", self.sql_agent.execute_sql)
        workflow.add_node("format_and_visualize", self.sql_agent.format_and_visualize)
        workflow.add_node("format_data_for_visualization", self.data_formatter.format_data_for_visualization)

        # Define edges (simplified flow)
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "format_and_visualize")
        workflow.add_edge("format_and_visualize", "format_data_for_visualization")
        workflow.add_edge("format_data_for_visualization", END)
        workflow.set_entry_point("generate_sql")

        return workflow
    
    def returnGraph(self):
        return self.create_workflow().compile()

    def run_sql_agent(self, question: str, uuid: str) -> dict:
        """Run the SQL agent workflow and return the formatted answer and visualization recommendation."""
        # Track individual step timings
        state = {"question": question, "uuid": uuid}

        # Step 1: Generate SQL
        start = time.time()
        sql_result = self.sql_agent.generate_sql_direct(state)
        state.update(sql_result)
        metrics_tracker.record_step(uuid, 'sql_gen', time.time() - start)

        # Step 2: Execute SQL
        start = time.time()
        exec_result = self.sql_agent.execute_sql(state)
        state.update(exec_result)
        metrics_tracker.record_step(uuid, 'execution', time.time() - start)

        # Step 3: Format and Visualize
        start = time.time()
        format_result = self.sql_agent.format_and_visualize(state)
        state.update(format_result)
        metrics_tracker.record_step(uuid, 'format', time.time() - start)

        # Step 4: Format data for visualization
        start = time.time()
        viz_result = self.data_formatter.format_data_for_visualization(state)
        state.update(viz_result)
        metrics_tracker.record_step(uuid, 'visualization', time.time() - start)

        # Debug: print what we got back
        print(f"Workflow result keys: {state.keys()}")
        print(f"Results value: {state.get('results')}")
        print(f"Answer value: {state.get('answer')}")

        return {
            "answer": state.get('answer', 'Unable to process query'),
            "visualization": state.get('visualization', 'none'),
            "visualization_reason": state.get('visualization_reason', ''),
            "formatted_data_for_visualization": state.get('formatted_data_for_visualization'),
            "sql_query": state.get('sql_query', ''),
            "raw_results": state.get('results'),
            "error": state.get('error')
        }