import pandas as pd
from sqlalchemy import create_engine, text
from typing import Dict, Any
from agentic_processor.sql_generator import SQLGenerator
from agentic_processor.chart_detector import ChartDetector
from config.settings import DATABASE_URL

class QueryProcessor:
    def __init__(self):
        self.sql_generator = SQLGenerator()
        self.chart_detector = ChartDetector()
        self.engine = create_engine(DATABASE_URL)

    def process_natural_language(self, query: str) -> Dict[str, Any]:
        # 1. Generate SQL
        sql_query = self.sql_generator.generate_sql(query)
        print(f"Generated SQL: {sql_query}")
        
        # 2. Detect Chart Type
        chart_type = self.chart_detector.detect_chart_type(query, sql_query)
        print(f"Detected Chart Type: {chart_type}")
        
        # 3. Execute SQL
        try:
            with self.engine.connect() as conn:
                # Use pandas to read sql for easy dataframe handling
                df = pd.read_sql(text(sql_query), conn)
                
            if df.empty:
                return {
                    "status": "success",
                    "message": "No data found for this query.",
                    "sql_query": sql_query,
                    "chart_type": "none",
                    "data": None
                }
                
            return {
                "status": "success",
                "sql_query": sql_query,
                "chart_type": chart_type,
                "data": df
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "sql_query": sql_query
            }
