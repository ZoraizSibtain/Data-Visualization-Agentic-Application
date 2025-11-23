from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import QueuePool
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL


class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=10,
            pool_pre_ping=True
        )

    def get_schema(self) -> str:
        """Dynamically inspect database schema and return human-readable description."""
        inspector = inspect(self.engine)
        schema_parts = []

        tables = inspector.get_table_names()

        for table_name in tables:
            # Skip internal tables
            if table_name.startswith('_'):
                continue

            schema_parts.append(f"\nTable: {table_name}")
            schema_parts.append("-" * 50)

            # Get columns
            columns = inspector.get_columns(table_name)
            schema_parts.append("Columns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                col_type = str(col['type'])
                default = f" DEFAULT {col['default']}" if col.get('default') else ""
                schema_parts.append(f"  - {col['name']}: {col_type} {nullable}{default}")

            # Get primary keys
            pk = inspector.get_pk_constraint(table_name)
            if pk and pk.get('constrained_columns'):
                schema_parts.append(f"Primary Key: {', '.join(pk['constrained_columns'])}")

            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                schema_parts.append("Foreign Keys:")
                for fk in fks:
                    cols = ', '.join(fk['constrained_columns'])
                    ref_table = fk['referred_table']
                    ref_cols = ', '.join(fk['referred_columns'])
                    schema_parts.append(f"  - {cols} -> {ref_table}({ref_cols})")

            schema_parts.append("")

        return "\n".join(schema_parts)

    def execute_query(self, query: str) -> list:
        """Execute a raw SQL query and return results as list of dictionaries."""
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def get_table_names(self) -> list:
        """Get list of all table names."""
        inspector = inspect(self.engine)
        return [t for t in inspector.get_table_names() if not t.startswith('_')]

    def dispose(self):
        """Dispose of the database engine and connections."""
        self.engine.dispose()
