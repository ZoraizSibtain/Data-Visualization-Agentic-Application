from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ChartDetector:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def detect_chart_type(self, query: str, sql_query: str) -> str:
        prompt = ChatPromptTemplate.from_template("""
        You are a data visualization expert. Determine the best chart type for the following user query and generated SQL.
        
        User Query: {query}
        SQL Query: {sql_query}
        
        Available Chart Types:
        - "line": For trends over time (e.g., monthly revenue, sales over years).
        - "bar": For categorical comparisons (e.g., sales by product, ratings by manufacturer).
        - "pie": For parts of a whole (e.g., distribution of status, percentage shares).
        - "scatter": For relationships between two variables.
        - "table": If the query asks for a list, specific details, or if no other chart type fits well.
        
        Rules:
        1. Return ONLY one of the strings: "line", "bar", "pie", "scatter", "table".
        2. If the user explicitly asks for a specific chart (e.g., "plot a line chart"), prioritize that.
        3. If the output is likely a single number or a text list, use "table".
        
        Chart Type:
        """)
        
        chain = prompt | self.llm | StrOutputParser()

        chart_type = chain.invoke({"query": query, "sql_query": sql_query})
        # Clean up: remove quotes, whitespace, and convert to lowercase
        chart_type = chart_type.strip().lower().strip('"').strip("'")

        # Validate chart type
        valid_types = ["line", "bar", "pie", "scatter", "table"]
        if chart_type not in valid_types:
            chart_type = "table"

        return chart_type
