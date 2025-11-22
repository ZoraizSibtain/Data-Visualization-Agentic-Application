"""
CSV Ingestion - Dynamically ingest CSV files into database
"""
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime
from sqlalchemy.types import TypeDecorator
import config
from pathlib import Path
from typing import Optional


def infer_column_type(series: pd.Series):
    """
    Infer SQLAlchemy column type from pandas series
    
    Args:
        series: Pandas series to analyze
        
    Returns:
        SQLAlchemy column type
    """
    dtype = series.dtype
    
    if pd.api.types.is_integer_dtype(dtype):
        return Integer
    elif pd.api.types.is_float_dtype(dtype):
        return Float
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return DateTime
    else:
        # Default to String for everything else
        return String


def ingest_csv(csv_path: str, table_name: Optional[str] = None, database_url: Optional[str] = None) -> str:
    """
    Ingest a CSV file into the database with automatic schema inference
    
    Args:
        csv_path: Path to CSV file
        table_name: Name for the table (defaults to CSV filename without extension)
        database_url: Database URL (defaults to config.DATABASE_URL)
        
    Returns:
        Success message with table name
    """
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Determine table name
    if table_name is None:
        table_name = Path(csv_path).stem.lower().replace(' ', '_')
    
    # Clean column names (remove spaces, special characters)
    df.columns = [col.strip().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '') 
                  for col in df.columns]
    
    # Create engine
    db_url = database_url or config.DATABASE_URL
    engine = create_engine(db_url)
    metadata = MetaData()
    
    # Dynamically create table schema
    columns = []
    for col_name in df.columns:
        # Infer type
        # infer_column_type returns a class (e.g. Integer), so we instantiate it
        col_type_class = infer_column_type(df[col_name])
        col_type = col_type_class()
        
        # Check nullability (True if any NaN values present)
        is_nullable = df[col_name].hasnans
        
        columns.append(Column(col_name, col_type, nullable=is_nullable))
    
    # Define table
    table = Table(table_name, metadata, *columns)
    
    # Drop if exists (to match previous if_exists='replace' behavior)
    table.drop(engine, checkfirst=True)
    
    # Create table with constraints
    table.create(engine)
    
    # Insert data
    # We use if_exists='append' because we just created the table
    df.to_sql(table_name, engine, if_exists='append', index=False)
    
    return f"Successfully ingested {len(df)} rows into table '{table_name}'"


def setup_default_database():
    """
    Set up the default database with RobotVacuum data
    
    Returns:
        Success message
    """
    if not config.DEFAULT_CSV_PATH.exists():
        return "Default CSV file not found"
    
    # Ensure data directory exists
    config.DATA_DIR.mkdir(exist_ok=True)
    
    # Ingest the default CSV
    result = ingest_csv(str(config.DEFAULT_CSV_PATH), table_name='robot_vacuum_products')
    
    return result
