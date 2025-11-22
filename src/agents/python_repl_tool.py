"""
Python REPL Tool - Safe execution environment for generated code
"""
from langchain_experimental.tools import PythonREPLTool
from langchain.tools import tool
from typing import Any, Dict
import sys
from io import StringIO


class SafePythonREPL:
    """Wrapper for Python REPL with pre-configured context"""
    
    def __init__(self, database_url: str):
        """
        Initialize REPL with database connection
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.repl = PythonREPLTool()
        
        # Pre-import common libraries
        self.setup_code = f"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import json

# Create database connection
engine = create_engine('{database_url}')

# Helper function to convert figure to JSON
def fig_to_json(fig):
    return fig.to_json()
"""
        # Execute setup code
        try:
            self.repl.run(self.setup_code)
        except Exception as e:
            print(f"Warning: Setup code failed: {e}")
    
    def run(self, code: str) -> str:
        """
        Execute Python code in the REPL
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result or error message
        """
        try:
            result = self.repl.run(code)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


@tool
def python_repl_tool(code: str, database_url: str = None) -> str:
    """
    Execute Python code with access to database and visualization libraries.
    
    Use this tool to:
    - Execute SQL queries using pandas: pd.read_sql(query, engine)
    - Create Plotly visualizations
    - Perform data analysis
    
    Args:
        code: Python code to execute
        database_url: Database connection URL (optional)
        
    Returns:
        Result of code execution or error message
    """
    if database_url is None:
        import config
        database_url = str(config.DATABASE_URL)
    
    repl = SafePythonREPL(database_url)
    result = repl.run(code)
    
    return result
