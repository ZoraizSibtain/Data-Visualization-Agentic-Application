from typing import TypedDict, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
import time
import re
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LLM_MODEL, LLM_TEMPERATURE, MAX_ITERATIONS
from .python_repl_tool import SafePythonREPL
from utils.prompts import SYSTEM_PROMPT, ERROR_RECOVERY_PROMPT
from utils.sql_extractor import extract_sql_from_code


class AgentState(TypedDict):
    user_input: str
    messages: List
    schema: str
    code: Optional[str]
    result: Optional[str]
    figure_json: Optional[str]
    iterations: int
    error: Optional[str]
    final_response: str
    execution_time: float


class WorkflowManager:
    def __init__(self, api_key: str, database_url: str = None):
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=api_key
        )
        self.repl = SafePythonREPL(database_url)
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        """Create the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("execute_code", self._execute_code)
        workflow.add_node("fix_error", self._fix_error)
        workflow.add_node("format_response", self._format_response)

        # Set entry point
        workflow.set_entry_point("generate_code")

        # Add edges
        workflow.add_edge("generate_code", "execute_code")
        workflow.add_conditional_edges(
            "execute_code",
            self._should_retry,
            {
                "retry": "fix_error",
                "success": "format_response",
                "max_retries": "format_response"
            }
        )
        workflow.add_edge("fix_error", "execute_code")
        workflow.add_edge("format_response", END)

        return workflow.compile()

    def _generate_code(self, state: AgentState) -> AgentState:
        """Generate Python code with SQL query and visualization."""
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(schema=state["schema"])),
            HumanMessage(content=state["user_input"])
        ]

        response = self.llm.invoke(messages)
        code = self._extract_code(response.content)

        state["code"] = code
        state["messages"].append(AIMessage(content=response.content))

        return state

    def _execute_code(self, state: AgentState) -> AgentState:
        """Execute the generated code."""
        try:
            result = self.repl.run(state["code"])

            # Debug: print result to console
            print(f"[DEBUG] REPL result length: {len(result) if result else 0}")
            if result and '<<<FIGURE_JSON_START>>>' in result:
                print("[DEBUG] Figure markers found in result")
            else:
                print(f"[DEBUG] No figure markers. Result preview: {result[:500] if result else 'empty'}")

            # Extract figure JSON if present
            figure_json = self._extract_figure_json(result)
            if figure_json:
                state["figure_json"] = figure_json
                print(f"[DEBUG] Figure JSON extracted, length: {len(figure_json)}")
                # Clean result of figure JSON markers
                result = re.sub(
                    r'<<<FIGURE_JSON_START>>>.*?<<<FIGURE_JSON_END>>>',
                    '[Visualization generated]',
                    result,
                    flags=re.DOTALL
                )
            else:
                print("[DEBUG] No figure JSON extracted")

            state["result"] = result
            state["error"] = None

        except Exception as e:
            state["error"] = str(e)
            state["iterations"] += 1
            print(f"[DEBUG] Execution error: {e}")

        return state

    def _fix_error(self, state: AgentState) -> AgentState:
        """Fix code that produced an error."""
        error_prompt = ERROR_RECOVERY_PROMPT.format(
            code=state["code"],
            error=state["error"],
            schema=state["schema"]
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(schema=state["schema"])),
            HumanMessage(content=state["user_input"]),
            AIMessage(content=state["code"]),
            HumanMessage(content=error_prompt)
        ]

        response = self.llm.invoke(messages)
        code = self._extract_code(response.content)

        state["code"] = code
        state["messages"].append(AIMessage(content=response.content))

        return state

    def _format_response(self, state: AgentState) -> AgentState:
        """Format the final response for the user."""
        if state["error"]:
            state["final_response"] = f"I encountered an error after {state['iterations']} attempts:\n\n{state['error']}\n\nPlease try rephrasing your question."
        else:
            # Format result for display
            result = state["result"] or ""

            # Clean up the result
            if "[Visualization generated]" in result:
                state["final_response"] = "I've generated a visualization for your query."
            elif result.strip():
                state["final_response"] = result
            else:
                state["final_response"] = "Query executed successfully."

        return state

    def _should_retry(self, state: AgentState) -> str:
        """Determine if we should retry after an error."""
        if state["error"] is None:
            return "success"
        elif state["iterations"] >= MAX_ITERATIONS:
            return "max_retries"
        else:
            return "retry"

    def _extract_code(self, content: str) -> str:
        """Extract Python code from LLM response."""
        # Look for code blocks - use findall and take the first one only
        code_matches = re.findall(r'```(?:python)?\s*(.*?)```', content, re.DOTALL)
        if code_matches:
            return code_matches[0].strip()

        # If no code block, assume entire content is code
        return content.strip()

    def _extract_figure_json(self, result: str) -> Optional[str]:
        """Extract Plotly figure JSON from execution result."""
        match = re.search(
            r'<<<FIGURE_JSON_START>>>\s*(.*?)\s*<<<FIGURE_JSON_END>>>',
            result,
            re.DOTALL
        )
        if match:
            try:
                # Validate JSON
                json.loads(match.group(1))
                return match.group(1)
            except json.JSONDecodeError:
                return None
        return None

    def run(self, user_input: str, schema: str) -> dict:
        """Run the workflow for a user query."""
        start_time = time.time()

        initial_state = {
            "user_input": user_input,
            "messages": [],
            "schema": schema,
            "code": None,
            "result": None,
            "figure_json": None,
            "iterations": 0,
            "error": None,
            "final_response": "",
            "execution_time": 0
        }

        result = self.workflow.invoke(initial_state)
        result["execution_time"] = time.time() - start_time

        # Extract SQL from code
        sql_query = extract_sql_from_code(result.get("code", ""))

        return {
            "response": result["final_response"],
            "sql_query": sql_query,
            "python_code": result["code"],
            "figure_json": result["figure_json"],
            "execution_time": result["execution_time"],
            "error": result["error"]
        }

    def cleanup(self):
        """Clean up resources."""
        self.repl.cleanup()
