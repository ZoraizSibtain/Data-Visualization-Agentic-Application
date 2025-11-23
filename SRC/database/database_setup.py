from sqlalchemy import create_engine, text
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL, DEFAULT_CSV_PATH
from .schema_3nf import Base
from .etl_3nf import ETLPipeline
from .query_storage import QueryStorage


def initialize_database(csv_path: str = None, reset: bool = True):
    """
    Initialize the database with schema and load data from CSV.

    Args:
        csv_path: Path to CSV file (uses default if not provided)
        reset: If True, drop and recreate all tables (default True)
    """
    csv_path = csv_path or str(DEFAULT_CSV_PATH)

    print(f"Using CSV file: {csv_path}")

    # Create ETL pipeline
    etl = ETLPipeline(DATABASE_URL)

    try:
        if reset:
            print("Dropping existing tables...")
            etl.drop_tables()

        print("Creating tables...")
        etl.create_tables()

        # Check if CSV exists
        if os.path.exists(csv_path):
            print(f"Loading data from {csv_path}...")
            etl.transform_and_load(csv_path)
            print("Data loaded successfully!")
        else:
            print(f"Warning: CSV file not found at {csv_path}")
            print("Database tables created but no data loaded.")

        # Initialize query storage tables
        print("Initializing query storage...")
        query_storage = QueryStorage(DATABASE_URL)
        query_storage.close()
        print("Query storage initialized!")

        print("\nDatabase initialization complete!")

    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        etl.close()


def test_database_connection() -> bool:
    """Test if database connection works."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    initialize_database(reset=True)
