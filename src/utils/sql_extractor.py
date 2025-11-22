"""
SQL Extraction - Extract SQL queries from generated Python code
"""
import re
from typing import Optional


def extract_sql_from_code(python_code: str) -> Optional[str]:
    """
    Extract SQL query from Python code
    
    Args:
        python_code: Python code containing SQL query
        
    Returns:
        Extracted SQL query or None
    """
    if not python_code:
        return None
    
    # Pattern 1: Triple-quoted strings assigned to 'query' variable
    pattern1 = r'query\s*=\s*"""(.*?)"""'
    matches = re.findall(pattern1, python_code, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Pattern 2: Single-quoted strings
    pattern2 = r"query\s*=\s*'''(.*?)'''"
    matches = re.findall(pattern2, python_code, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Pattern 3: Regular strings with newlines
    pattern3 = r'query\s*=\s*"(.*?)"'
    matches = re.findall(pattern3, python_code, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Pattern 4: Look for SQL keywords (fallback)
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']
    for keyword in sql_keywords:
        if keyword in python_code.upper():
            # Try to extract the SQL statement
            lines = python_code.split('\n')
            sql_lines = []
            in_sql = False
            
            for line in lines:
                if keyword in line.upper():
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                    if ';' in line or 'FROM' in line.upper():
                        break
            
            if sql_lines:
                sql = '\n'.join(sql_lines)
                # Clean up quotes and variable assignments
                sql = re.sub(r'query\s*=\s*["\']', '', sql)
                sql = re.sub(r'["\']', '', sql)
                return sql.strip()
    
    return None


def format_sql(sql: str) -> str:
    """
    Format SQL query for better readability
    
    Args:
        sql: SQL query string
        
    Returns:
        Formatted SQL query
    """
    if not sql:
        return ""
    
    # Add newlines before major SQL keywords
    keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT', 'JOIN', 'HAVING']
    formatted = sql
    
    for keyword in keywords:
        formatted = re.sub(f'\\s+{keyword}\\s+', f'\n{keyword} ', formatted, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    formatted = re.sub(r'\n\s+', '\n', formatted)
    formatted = re.sub(r'\s+', ' ', formatted)
    
    return formatted.strip()
