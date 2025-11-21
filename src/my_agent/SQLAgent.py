from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .DatabaseManager import DatabaseManager
from .LLMManager import LLMManager
from .RAGLayer import RAGLayer

class SQLAgent:
    def __init__(self, use_rag: bool = True):
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()
        self.use_rag = use_rag
        try:
            self.rag_layer = RAGLayer() if use_rag else None
        except Exception as e:
            print(f"Warning: RAG layer initialization failed: {e}")
            self.rag_layer = None
            self.use_rag = False

    def parse_question(self, state: dict) -> dict:
        """Parse user question and identify relevant tables and columns."""
        question = state['question']
        schema = self.db_manager.get_schema(state['uuid'])

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''You are a data analyst that can help summarize SQL tables and parse user questions about a database. 
Given the question and database schema, identify the relevant tables and columns. 
If the question is not relevant to the database or if there is not enough information to answer the question, set is_relevant to false.

Your response should be in the following JSON format:
{{
    "is_relevant": boolean,
    "relevant_tables": [
        {{
            "table_name": string,
            "columns": [string],
            "noun_columns": [string]
        }}
    ]
}}

The "noun_columns" field should contain only the columns that are relevant to the question and contain nouns or names, for example, the column "Artist name" contains nouns relevant to the question "What are the top selling artists?", but the column "Artist ID" is not relevant because it does not contain a noun. Do not include columns that contain numbers.
'''),
            ("human", "===Database schema:\n{schema}\n\n===User question:\n{question}\n\nIdentify relevant tables and columns:")
        ])

        output_parser = JsonOutputParser()

        try:
            response = self.llm_manager.invoke(prompt, schema=schema, question=question)
            parsed_response = output_parser.parse(response)
            return {"parsed_question": parsed_response}
        except Exception as e:
            print(f"Error parsing question: {e}")
            return {"parsed_question": {"is_relevant": False, "relevant_tables": []}, "error": str(e)}

    def get_unique_nouns(self, state: dict) -> dict:
        """Find unique nouns in relevant tables and columns."""
        parsed_question = state['parsed_question']
        
        if not parsed_question['is_relevant']:
            return {"unique_nouns": []}

        unique_nouns = set()
        for table_info in parsed_question['relevant_tables']:
            table_name = table_info['table_name']
            noun_columns = table_info['noun_columns']

            if noun_columns:
                column_names = ', '.join(f'"{col}"' for col in noun_columns)
                # Handle schema.table format by quoting each part separately
                if '.' in table_name:
                    schema, table = table_name.split('.', 1)
                    quoted_table = f'"{schema}"."{table}"'
                else:
                    # Default to robot_vacuum_depot schema if not specified
                    quoted_table = f'"robot_vacuum_depot"."{table_name}"'
                query = f'SELECT DISTINCT {column_names} FROM {quoted_table}'
                try:
                    results = self.db_manager.execute_query(state['uuid'], query)
                    for row in results:
                        unique_nouns.update(str(value) for value in row if value)
                except Exception as e:
                    # Log but continue if one table fails
                    print(f"Warning: Failed to get unique nouns from {table_name}: {e}")

        return {"unique_nouns": list(unique_nouns)}

    def generate_sql(self, state: dict) -> dict:
        """Generate SQL query based on parsed question and unique nouns."""
        question = state['question']
        parsed_question = state['parsed_question']
        unique_nouns = state['unique_nouns']

        if not parsed_question['is_relevant']:
            return {"sql_query": "NOT_RELEVANT", "is_relevant": False}
    
        schema = self.db_manager.get_schema(state['uuid'])

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''
You are an AI assistant that generates SQL queries based on user questions, database schema, and unique nouns found in the relevant tables. Generate a valid SQL query to answer the user's question.

If there is not enough information to write a SQL query, respond with "NOT_ENOUGH_INFO".

Here are some examples:

1. What is the top selling product?
Answer: SELECT product_name, SUM(quantity) as total_quantity FROM sales WHERE product_name IS NOT NULL AND quantity IS NOT NULL AND product_name != "" AND quantity != "" AND product_name != "N/A" AND quantity != "N/A" GROUP BY product_name ORDER BY total_quantity DESC LIMIT 1

2. What is the total revenue for each product?
Answer: SELECT "product name", SUM(quantity * price) as total_revenue FROM sales WHERE "product name" IS NOT NULL AND quantity IS NOT NULL AND price IS NOT NULL AND "product name" != "" AND quantity != "" AND price != "" AND "product name" != "N/A" AND quantity != "N/A" AND price != "N/A" GROUP BY "product name"  ORDER BY total_revenue DESC

3. What is the market share of each product?
Answer: SELECT "product name", SUM(quantity) * 100.0 / (SELECT SUM(quantity) FROM sa  les) as market_share FROM sales WHERE "product name" IS NOT NULL AND quantity IS NOT NULL AND "product name" != "" AND quantity != "" AND "product name" != "N/A" AND quantity != "N/A" GROUP BY "product name"  ORDER BY market_share DESC

4. Plot the distribution of income over time
Answer: SELECT income, COUNT(*) as count FROM users WHERE income IS NOT NULL AND income != "" AND income != "N/A" GROUP BY income

THE RESULTS SHOULD ONLY BE IN THE FOLLOWING FORMAT, SO MAKE SURE TO ONLY GIVE TWO OR THREE COLUMNS:
[[x, y]]
or 
[[label, x, y]]
             
For questions like "plot a distribution of the fares for men and women", count the frequency of each fare and plot it. The x axis should be the fare and the y axis should be the count of people who paid that fare.
SKIP ALL ROWS WHERE ANY COLUMN IS NULL or "N/A" or "".
Just give the query string. Do not format it. Make sure to use the correct spellings of nouns as provided in the unique nouns list.
IMPORTANT: For schema.table names like robot_vacuum_depot.Order, quote them separately as "robot_vacuum_depot"."Order", NOT as "robot_vacuum_depot.Order". All column names should also be enclosed in double quotes.
'''),
            ("human", '''===Database schema:
{schema}

===User question:
{question}

===Relevant tables and columns:
{parsed_question}

===Unique nouns in relevant tables:
{unique_nouns}

Generate SQL query string'''),
        ])

        try:
            response = self.llm_manager.invoke(prompt, schema=schema, question=question, parsed_question=parsed_question, unique_nouns=unique_nouns)

            if response.strip() == "NOT_ENOUGH_INFO":
                return {"sql_query": "NOT_RELEVANT"}
            else:
                return {"sql_query": response}
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return {"sql_query": "NOT_RELEVANT", "error": str(e)}

    def validate_and_fix_sql(self, state: dict) -> dict:
        """Validate and fix the generated SQL query."""
        sql_query = state['sql_query']

        if sql_query == "NOT_RELEVANT":
            return {"sql_query": "NOT_RELEVANT", "sql_valid": False}
        
        schema = self.db_manager.get_schema(state['uuid'])

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''
You are an AI assistant that validates and fixes SQL queries. Your task is to:
1. Check if the SQL query is valid.
2. Ensure all table and column names are correctly spelled and exist in the schema.
3. IMPORTANT: For schema.table names like robot_vacuum_depot.Order, they must be quoted separately as "robot_vacuum_depot"."Order", NOT as "robot_vacuum_depot.Order". All column names should also be enclosed in double quotes.
4. If there are any issues, fix them and provide the corrected SQL query.
5. If no issues are found, return the original query.

Respond in JSON format with the following structure. Only respond with the JSON:
{{
    "valid": boolean,
    "issues": string or null,
    "corrected_query": string
}}
'''),
            ("human", '''===Database schema:
{schema}

===Generated SQL query:
{sql_query}

Respond in JSON format with the following structure. Only respond with the JSON:
{{
    "valid": boolean,
    "issues": string or null,
    "corrected_query": string
}}

For example:
1. {{
    "valid": true,
    "issues": null,
    "corrected_query": "None"
}}
             
2. {{
    "valid": false,
    "issues": "Column USERS does not exist",
    "corrected_query": "SELECT * FROM \"users\" WHERE age > 25"
}}

3. {{
    "valid": false,
    "issues": "Column names and table names should be enclosed in double quotes if they contain spaces or special characters",
    "corrected_query": "SELECT * FROM \"gross income\" WHERE \"age\" > 25"
}}
             
'''),
        ])

        output_parser = JsonOutputParser()

        try:
            response = self.llm_manager.invoke(prompt, schema=schema, sql_query=sql_query)
            result = output_parser.parse(response)

            if result["valid"] and result["issues"] is None:
                return {"sql_query": sql_query, "sql_valid": True}
            else:
                return {
                    "sql_query": result["corrected_query"],
                    "sql_valid": result["valid"],
                    "sql_issues": result["issues"]
                }
        except Exception as e:
            print(f"Error validating SQL: {e}")
            # Return original query if validation fails
            return {"sql_query": sql_query, "sql_valid": False, "sql_issues": str(e)}

    def execute_sql(self, state: dict) -> dict:
        """Execute SQL query and return results."""
        query = state.get('sql_query', '')
        uuid = state['uuid']

        if not query or query == "NOT_RELEVANT":
            return {"results": "NOT_RELEVANT"}

        try:
            results = self.db_manager.execute_query(uuid, query)
            return {"results": results}
        except Exception as e:
            return {"results": [], "error": str(e)}

    def format_results(self, state: dict) -> dict:
        """Format query results into a human-readable response."""
        question = state['question']
        results = state.get('results', [])

        if results == "NOT_RELEVANT":
            return {"answer": "Sorry, I can only give answers relevant to the database."}

        if not results or (isinstance(results, list) and len(results) == 0):
            return {"answer": "The query executed successfully but returned no matching data. This could mean no records match the specified criteria in the database."}

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant that formats database query results into a human-readable response. Give a conclusion to the user's question based on the query results. Do not give the answer in markdown format. Only give the answer in one line."),
            ("human", "User question: {question}\n\nQuery results: {results}\n\nFormatted response:"),
        ])

        try:
            response = self.llm_manager.invoke(prompt, question=question, results=results)
            return {"answer": response}
        except Exception as e:
            print(f"Error formatting results: {e}")
            return {"answer": f"Query returned {len(results) if isinstance(results, list) else 0} results."}

    def choose_visualization(self, state: dict) -> dict:
        """Choose an appropriate visualization for the data."""
        question = state['question']
        results = state['results']
        sql_query = state['sql_query']

        if results == "NOT_RELEVANT":
            return {"visualization": "none", "visualization_reasoning": "No visualization needed for irrelevant questions."}

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''
You are an AI assistant that recommends appropriate data visualizations. Based on the user's question, SQL query, and query results, suggest the most suitable type of graph or chart to visualize the data. If no visualization is appropriate, indicate that.

Available chart types and their use cases:
- Bar Graphs: Best for comparing categorical data or showing changes over time when categories are discrete and the number of categories is more than 2. Use for questions like "What are the sales figures for each product?" or "How does the population of cities compare? or "What percentage of each city is male?"
- Horizontal Bar Graphs: Best for comparing categorical data or showing changes over time when the number of categories is small or the disparity between categories is large. Use for questions like "Show the revenue of A and B?" or "How does the population of 2 cities compare?" or "How many men and women got promoted?" or "What percentage of men and what percentage of women got promoted?" when the disparity between categories is large.
- Scatter Plots: Useful for identifying relationships or correlations between two numerical variables or plotting distributions of data. Best used when both x axis and y axis are continuous. Use for questions like "Plot a distribution of the fares (where the x axis is the fare and the y axis is the count of people who paid that fare)" or "Is there a relationship between advertising spend and sales?" or "How do height and weight correlate in the dataset? Do not use it for questions that do not have a continuous x axis."
- Pie Charts: Ideal for showing proportions or percentages within a whole. Use for questions like "What is the market share distribution among different companies?" or "What percentage of the total revenue comes from each product?"
- Line Graphs: Best for showing trends and distributionsover time. Best used when both x axis and y axis are continuous. Used for questions like "How have website visits changed over the year?" or "What is the trend in temperature over the past decade?". Do not use it for questions that do not have a continuous x axis or a time based x axis.

Consider these types of questions when recommending a visualization:
1. Aggregations and Summarizations (e.g., "What is the average revenue by month?" - Line Graph)
2. Comparisons (e.g., "Compare the sales figures of Product A and Product B over the last year." - Line or Column Graph)
3. Plotting Distributions (e.g., "Plot a distribution of the age of users" - Scatter Plot)
4. Trends Over Time (e.g., "What is the trend in the number of active users over the past year?" - Line Graph)
5. Proportions (e.g., "What is the market share of the products?" - Pie Chart)
6. Correlations (e.g., "Is there a correlation between marketing spend and revenue?" - Scatter Plot)

Provide your response in the following format:
Recommended Visualization: [Chart type or "None"]. ONLY use the following names: bar, horizontal_bar, line, pie, scatter, none
Reason: [Brief explanation for your recommendation]
'''),
            ("human", '''
User question: {question}
SQL query: {sql_query}
Query results: {results}

Recommend a visualization:'''),
        ])

        response = self.llm_manager.invoke(prompt, question=question, sql_query=sql_query, results=results)

        # Parse the response more robustly
        visualization = "none"
        reason = ""

        try:
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            for line in lines:
                if 'Recommended Visualization:' in line or 'Visualization:' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        visualization = parts[1].strip().lower().replace('.', '')
                elif 'Reason:' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        reason = parts[1].strip()
        except Exception:
            pass

        # Normalize visualization type
        if visualization not in ['bar', 'horizontal_bar', 'line', 'pie', 'scatter', 'none']:
            visualization = 'none'

        return {"visualization": visualization, "visualization_reason": reason}

    # ==================== OPTIMIZED METHODS ====================

    def generate_sql_direct(self, state: dict) -> dict:
        """Generate SQL query directly without parsing step - optimized for speed with RAG enhancement."""
        question = state['question']
        schema = self.db_manager.get_schema(state['uuid'])

        # Get RAG context if available
        rag_examples = ""
        rag_context = ""
        if self.use_rag and self.rag_layer:
            try:
                rag_data = self.rag_layer.enhance_sql_generation(state)
                rag_examples = rag_data.get('rag_examples', '')
                rag_context = rag_data.get('rag_business_context', '')
            except Exception as e:
                print(f"RAG enhancement failed: {e}")

        # Build system prompt with optional RAG context
        system_prompt = '''You are an expert SQL developer. Generate a valid PostgreSQL query for the given question and schema.

IMPORTANT RULES:
1. Always use schema-qualified table names: "robot_vacuum_depot"."TableName"
2. Quote all identifiers with double quotes
3. Return only 2-3 columns max for visualization
4. Include appropriate WHERE, GROUP BY, ORDER BY clauses
5. Handle NULLs appropriately
6. CRITICAL: When selecting columns from multiple tables, you MUST include proper JOINs
7. Use table aliases for clarity (e.g., o for Order, p for Product)
8. For aggregations (pie charts, bar charts, rankings), add LIMIT 15
9. If the question is not relevant to the schema, respond with exactly: NOT_RELEVANT'''

        if rag_context:
            system_prompt += f"\n\nBusiness Context:\n{rag_context}"

        if rag_examples:
            system_prompt += f"\n\nSimilar Query Examples:\n{rag_examples}"

        system_prompt += '''

Example:
SELECT p."ProductName", COUNT(*) as order_count
FROM "robot_vacuum_depot"."Order" o
JOIN "robot_vacuum_depot"."Product" p ON o."ProductID" = p."ProductID"
GROUP BY p."ProductName"
ORDER BY order_count DESC
LIMIT 15

Just return the SQL query string, nothing else.'''

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", '''Schema:
{schema}

Question: {question}

Generate SQL query:'''),
        ])

        try:
            response = self.llm_manager.invoke(prompt, schema=schema, question=question)

            if "NOT_RELEVANT" in response.upper():
                return {"sql_query": "NOT_RELEVANT", "parsed_question": {"is_relevant": False}}

            # Clean up the response
            sql = response.strip()
            if sql.startswith('```'):
                sql = sql.split('\n', 1)[1] if '\n' in sql else sql[3:]
            if sql.endswith('```'):
                sql = sql[:-3]

            return {"sql_query": sql.strip(), "parsed_question": {"is_relevant": True}}
        except Exception as e:
            print(f"Error in generate_sql_direct: {e}")
            return {"sql_query": "NOT_RELEVANT", "parsed_question": {"is_relevant": False}, "error": str(e)}

    def format_and_visualize(self, state: dict) -> dict:
        """Combined format results and choose visualization - single LLM call."""
        question = state['question']
        results = state.get('results', [])
        sql_query = state.get('sql_query', '')

        if results == "NOT_RELEVANT":
            return {
                "answer": "Sorry, I can only answer questions relevant to the database.",
                "visualization": "none",
                "visualization_reason": "Not relevant"
            }

        if not results or (isinstance(results, list) and len(results) == 0):
            return {
                "answer": "The query executed successfully but returned no matching data.",
                "visualization": "none",
                "visualization_reason": "No data to visualize"
            }

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''You are a data analyst. Given query results, provide:
1. A brief answer to the user's question (1-2 sentences)
2. The best visualization type for this data

Respond in this exact format:
Answer: [your answer]
Visualization: [bar|horizontal_bar|line|pie|scatter|none]
Reason: [brief reason]

Visualization guidelines:
- bar: categorical comparisons (5+ categories)
- horizontal_bar: few categories or large value differences
- line: trends over time
- pie: proportions/percentages
- scatter: correlations between numbers
- none: single values or text data'''),
            ("human", '''Question: {question}
SQL: {sql_query}
Results (first 10 rows): {results}

Provide answer and visualization:'''),
        ])

        # Limit results for prompt
        display_results = results[:10] if isinstance(results, list) else results

        try:
            response = self.llm_manager.invoke(
                prompt,
                question=question,
                sql_query=sql_query,
                results=str(display_results)
            )

            # Parse response
            answer = ""
            visualization = "none"
            reason = ""

            lines = [line.strip() for line in response.split('\n') if line.strip()]
            for line in lines:
                if line.startswith('Answer:'):
                    answer = line.split(':', 1)[1].strip()
                elif line.startswith('Visualization:'):
                    visualization = line.split(':', 1)[1].strip().lower()
                elif line.startswith('Reason:'):
                    reason = line.split(':', 1)[1].strip()

            # Normalize visualization
            if visualization not in ['bar', 'horizontal_bar', 'line', 'pie', 'scatter', 'none']:
                visualization = 'none'

            return {
                "answer": answer or "Query completed successfully.",
                "visualization": visualization,
                "visualization_reason": reason
            }
        except Exception as e:
            print(f"Error in format_and_visualize: {e}")
            return {
                "answer": f"Query returned {len(results) if isinstance(results, list) else 0} results.",
                "visualization": "bar",  # Default to bar chart
                "visualization_reason": "Default visualization due to processing error"
            }
