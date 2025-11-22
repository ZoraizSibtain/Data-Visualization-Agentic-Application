"""
Database Setup - Initialize default database schema
"""
from database.csv_ingestion import setup_default_database
import config


def initialize_database():
    """
    Initialize the database with default data
    
    Returns:
        Success message
    """
    # Ensure data directory exists
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if database already exists and has tables
    from database.DatabaseManager import DatabaseManager
    db = DatabaseManager()
    
    existing_tables = db.get_table_names()
    
    if existing_tables:
        return f"Database already initialized with tables: {', '.join(existing_tables)}"
    
    # Set up default database
    result = setup_default_database()
    
    return result


if __name__ == "__main__":
    # Allow running this script directly to initialize database
    print(initialize_database())
