import re
from typing import Optional


def extract_sql_from_code(code: str) -> Optional[str]:
    """
    Extract SQL query from Python code.

    Args:
        code: Python code that may contain SQL queries

    Returns:
        Extracted SQL query or None if not found
    """
    if not code:
        return None

    # Pattern 1: Triple-quoted strings (most common for multi-line SQL)
    patterns = [
        r'query\s*=\s*"""(.*?)"""',
        r"query\s*=\s*'''(.*?)'''",
        r'sql\s*=\s*"""(.*?)"""',
        r"sql\s*=\s*'''(.*?)'''",
        r'"""(SELECT.*?)"""',
        r"'''(SELECT.*?)'''",
    ]

    for pattern in patterns:
        match = re.search(pattern, code, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Pattern 2: Single-quoted strings
    single_patterns = [
        r'query\s*=\s*"([^"]+)"',
        r"query\s*=\s*'([^']+)'",
        r'sql\s*=\s*"([^"]+)"',
        r"sql\s*=\s*'([^']+)'",
    ]

    for pattern in single_patterns:
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            if sql.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')):
                return sql

    # Pattern 3: pd.read_sql with direct query
    read_sql_pattern = r'pd\.read_sql\s*\(\s*["\']([^"\']+)["\']'
    match = re.search(read_sql_pattern, code, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 4: f-strings (extract the template)
    fstring_pattern = r'query\s*=\s*f"""(.*?)"""'
    match = re.search(fstring_pattern, code, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def format_sql(sql: str) -> str:
    """
    Basic SQL formatting for display.

    Args:
        sql: SQL query string

    Returns:
        Formatted SQL string
    """
    if not sql:
        return ""

    # Add newlines before major keywords
    keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
                'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
                'LIMIT', 'OFFSET', 'UNION', 'WITH']

    formatted = sql
    for keyword in keywords:
        # Add newline before keyword (case-insensitive)
        pattern = rf'\s+({keyword})\s+'
        formatted = re.sub(pattern, f'\n{keyword} ', formatted, flags=re.IGNORECASE)

    return formatted.strip()
