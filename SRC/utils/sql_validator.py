import sqlglot
from sqlglot import exp

class SQLValidator:
    def __init__(self):
        self.forbidden_commands = {
            exp.Drop,
            exp.Delete,
            exp.TruncateTable,
            exp.Insert,
            exp.Update,
            exp.Alter,
            exp.Create,
            exp.Grant,
            exp.Revoke,
            exp.Commit,
            exp.Rollback
        }

    def validate(self, sql: str) -> tuple[bool, str]:
        """
        Validate that the SQL query is safe (read-only).
        Returns (is_valid, error_message).
        """
        try:
            # Parse the SQL
            parsed = sqlglot.parse(sql)
            
            for expression in parsed:
                # Check for forbidden command types
                if type(expression) in self.forbidden_commands:
                    return False, f"Forbidden command type: {expression.key.upper()}. Only SELECT queries are allowed."
                
                # Recursively check for forbidden commands in subqueries/CTEs
                for node in expression.walk():
                    if type(node) in self.forbidden_commands:
                        return False, f"Forbidden command type in subquery: {node.key.upper()}"
            
            return True, "Valid SQL"
            
        except Exception as e:
            return False, f"SQL Validation Error: {str(e)}"

def validate_sql(sql: str) -> tuple[bool, str]:
    """Helper function to validate SQL."""
    validator = SQLValidator()
    return validator.validate(sql)
