"""
Workflow Manager - Orchestrates multi-agent workflow for data analysis
"""
from typing import TypedDict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from agents.python_repl_tool import SafePythonREPL
from utils.prompts import SYSTEM_PROMPT, CODE_GENERATION_PROMPT, ERROR_RECOVERY_PROMPT
import config
import json
import re


class AgentState(TypedDict):
    """State for the agent workflow"""
    user_input: str
    messages: List
    schema: str
    code: Optional[str]
    result: Optional[str]
    figure_json: Optional[str]
    iterations: int
    error: Optional[str]
    final_response: str


class WorkflowManager:
    """Manages the multi-agent workflow for data analysis"""
    
    def __init__(self, api_key: str, database_url: str, schema: str):
        """
        Initialize workflow manager
        
        Args:
            api_key: OpenAI API key
            database_url: Database connection URL
            schema: Database schema description
        """
        self.api_key = api_key
        self.database_url = database_url
        self.schema = schema
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE
        )
        
        # Initialize Python REPL
        self.repl = SafePythonREPL(database_url)
    
    def run_query(self, user_question: str) -> dict:
        """
        Process a user question through the workflow
        
        Args:
            user_question: Natural language question from user
            
        Returns:
            Dictionary with result, figure_json, sql_query, execution_time, and response
        """
        import time
        from utils.sql_extractor import extract_sql_from_code
        
        start_time = time.time()
        
        state = AgentState(
            user_input=user_question,
            messages=[],
            schema=self.schema,
            code=None,
            result=None,
            figure_json=None,
            iterations=0,
            error=None,
            final_response=""
        )
        
        # Step 1: Generate code to answer the question
        state = self._generate_code(state)
        
        # Step 2: Execute code with retry logic
        max_retries = config.MAX_ITERATIONS
        while state['iterations'] < max_retries:
            state = self._execute_code(state)
            
            if state['error'] is None:
                # Success!
                break
            else:
                # Try to fix the error
                state = self._fix_error(state)
                state['iterations'] += 1
        
        # Step 3: Format final response
        state = self._format_response(state)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Extract SQL query from code
        sql_query = extract_sql_from_code(state['code']) if state['code'] else None
        
        return {
            'response': state['final_response'],
            'figure_json': state['figure_json'],
            'code': state['code'],
            'sql_query': sql_query,
            'execution_time': execution_time,
            'error': state['error']
        }
    
    def _generate_code(self, state: AgentState) -> AgentState:
        """Generate Python code to answer the user's question"""
        
        # Create prompt emphasizing visualization
        prompt = f"""{SYSTEM_PROMPT}

User Question: {state['user_input']}

Database Schema:
{state['schema']}

Generate Python code that:
1. Retrieves the necessary data using SQL
2. Creates an appropriate VISUALIZATION (chart/graph) using Plotly
3. Stores the figure in a variable called 'fig'
4. Converts the figure to JSON and stores in 'result_json' using: result_json = fig.to_json()

IMPORTANT: 
- ALWAYS create a visualization (bar, line, scatter, pie, etc.) unless the question explicitly asks for raw data
- Use pd.read_sql() to execute SQL queries
- Make the visualization interactive and informative
- Include proper titles and labels

Return ONLY the Python code, no explanations.
"""
        
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        # Extract code from response
        code = self._extract_code(response.content)
        
        state['code'] = code
        state['messages'].append(('user', state['user_input']))
        state['messages'].append(('assistant', f"Generated code:\n```python\n{code}\n```"))
        
        return state
    
    def _execute_code(self, state: AgentState) -> AgentState:
        """Execute the generated code"""
        
        if state['code'] is None:
            state['error'] = "No code to execute"
            return state
        
        try:
            # Modify code to print result_json with a marker
            modified_code = state['code'] + "\n\n# Print result for extraction\nif 'result_json' in dir():\n    print('<<<FIGURE_JSON_START>>>')\n    print(result_json)\n    print('<<<FIGURE_JSON_END>>>')"
            
            # Execute code
            result = self.repl.run(modified_code)
            
            # Try to extract figure JSON from output
            if '<<<FIGURE_JSON_START>>>' in result and '<<<FIGURE_JSON_END>>>' in result:
                start_marker = '<<<FIGURE_JSON_START>>>'
                end_marker = '<<<FIGURE_JSON_END>>>'
                start_idx = result.find(start_marker) + len(start_marker)
                end_idx = result.find(end_marker)
                
                if start_idx > 0 and end_idx > start_idx:
                    json_str = result[start_idx:end_idx].strip()
                    # Validate it's valid JSON
                    try:
                        json.loads(json_str)  # Test if valid JSON
                        state['figure_json'] = json_str
                    except:
                        pass
            
            state['result'] = result
            state['error'] = None
            
        except Exception as e:
            state['error'] = str(e)
            state['result'] = None
        
        return state
    
    def _fix_error(self, state: AgentState) -> AgentState:
        """Attempt to fix code that produced an error"""
        
        prompt = ERROR_RECOVERY_PROMPT.format(
            error=state['error'],
            code=state['code']
        )
        
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        # Extract fixed code
        code = self._extract_code(response.content)
        state['code'] = code
        
        return state
    
    def _format_response(self, state: AgentState) -> AgentState:
        """Format the final response for the user"""
        
        if state['error']:
            state['final_response'] = f"I encountered an error while processing your question: {state['error']}"
        elif state['figure_json']:
            state['final_response'] = "I've created a visualization to answer your question."
        elif state['result']:
            state['final_response'] = f"Here's what I found:\n\n{state['result']}"
        else:
            state['final_response'] = "I processed your question but didn't generate any output."
        
        return state
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from LLM response"""
        
        # Try to find code in markdown code blocks
        code_pattern = r'```python\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Try without language specifier
        code_pattern = r'```\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the whole text
        return text.strip()


def create_workflow(api_key: str, database_url: str, schema: str) -> WorkflowManager:
    """
    Factory function to create a workflow manager
    
    Args:
        api_key: OpenAI API key
        database_url: Database connection URL
        schema: Database schema description
        
    Returns:
        Configured WorkflowManager instance
    """
    return WorkflowManager(api_key, database_url, schema)
