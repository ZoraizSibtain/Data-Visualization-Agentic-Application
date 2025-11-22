"""
DatabaseManager - Handles database connections and dynamic schema inspection
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Optional
import config


class DatabaseManager:
    """Manages database connections and provides dynamic schema information"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: SQLAlchemy database URL (defaults to config.DATABASE_URL)
        """
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_schema(self) -> str:
        """
        Dynamically inspect database and return schema as formatted string
        
        Returns:
            Human-readable schema description for LLM context
        """
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        
        if not table_names:
            return "No tables found in database."
        
        schema_parts = ["Database Schema:\n"]
        
        for table_name in table_names:
            schema_parts.append(f"\nTable: {table_name}")
            columns = inspector.get_columns(table_name)
            
            schema_parts.append("Columns:")
            for col in columns:
                col_type = str(col['type'])
                nullable = "Nullable" if col['nullable'] else "Required"
                schema_parts.append(f"  - {col['name']}: {col_type} ({nullable})")
            
            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name)
            if pk_constraint and pk_constraint['constrained_columns']:
                pk_cols = ', '.join(pk_constraint['constrained_columns'])
                schema_parts.append(f"Primary Key: {pk_cols}")
            
            # Get foreign keys
            fk_constraints = inspector.get_foreign_keys(table_name)
            if fk_constraints:
                schema_parts.append("Foreign Keys:")
                for fk in fk_constraints:
                    fk_cols = ', '.join(fk['constrained_columns'])
                    ref_table = fk['referred_table']
                    ref_cols = ', '.join(fk['referred_columns'])
                    schema_parts.append(f"  - {fk_cols} -> {ref_table}({ref_cols})")
        
        return '\n'.join(schema_parts)
    
    def execute_query(self, query: str) -> List[Dict]:
        """
        Execute a SQL query and return results
        
        Args:
            query: SQL query string
            
        Returns:
            List of dictionaries representing rows
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return rows
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names in database"""
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_connection_string(self) -> str:
        """Get the database connection string for use in agents"""
        return str(self.database_url)
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()
