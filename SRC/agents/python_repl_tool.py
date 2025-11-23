from langchain_experimental.tools import PythonREPLTool
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL


class SafePythonREPL:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.repl = PythonREPLTool()

        # Setup code with imports and database connection
        self.setup_code = f'''
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# Create engine with connection pooling
_db_engine = create_engine(
    "{self.database_url}",
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

# Safe wrapper for pd.read_sql that works with SQLAlchemy 2.x
def read_sql_safe(query, con=None, **kwargs):
    if con is None:
        con = _db_engine
    with con.connect() as conn:
        # Wrap string queries with text() for SQLAlchemy 2.x compatibility
        if isinstance(query, str):
            query = text(query)
        return pd.read_sql_query(query, conn, **kwargs)

# Override pd.read_sql with safe version
_original_read_sql = pd.read_sql
pd.read_sql = read_sql_safe
engine = _db_engine

# Helper to output figure JSON
def output_figure(fig):
    """Output Plotly figure as JSON between markers for extraction."""
    fig_json = fig.to_json()
    print("<<<FIGURE_JSON_START>>>")
    print(fig_json)
    print("<<<FIGURE_JSON_END>>>")
    return fig
'''

        # Run setup code
        self._initialized = False

    def initialize(self):
        """Initialize the REPL with setup code."""
        if not self._initialized:
            self.repl.run(self.setup_code)
            self._initialized = True

    def run(self, code: str) -> str:
        """Execute Python code in the REPL."""
        self.initialize()
        result = self.repl.run(code)
        return result if result else ""

    def cleanup(self):
        """Clean up database connections."""
        if not self._initialized:
            return
        cleanup_code = '''
if '_db_engine' in dir():
    _db_engine.dispose()
'''
        try:
            self.repl.run(cleanup_code)
        except Exception:
            pass
        self._initialized = False
