import pandas as pd
from sqlalchemy import create_engine, inspect
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL


def ingest_csv(csv_path: str, table_name: str = None, database_url: str = None) -> str:
    """
    Ingest a CSV file directly into the database as a single table.

    Args:
        csv_path: Path to the CSV file
        table_name: Name for the table (defaults to filename without extension)
        database_url: Database connection URL

    Returns:
        Name of the created table
    """
    database_url = database_url or DATABASE_URL
    engine = create_engine(database_url)

    # Read CSV
    df = pd.read_csv(csv_path)

    # Clean column names
    df.columns = (df.columns
                  .str.strip()
                  .str.lower()
                  .str.replace(' ', '_')
                  .str.replace('[^a-z0-9_]', '', regex=True))

    # Generate table name if not provided
    if table_name is None:
        table_name = os.path.splitext(os.path.basename(csv_path))[0]
        table_name = table_name.lower().replace(' ', '_').replace('-', '_')

    # Load to database
    df.to_sql(table_name, engine, if_exists='replace', index=False)

    return table_name


def get_csv_preview(csv_path: str, rows: int = 5) -> pd.DataFrame:
    """Get a preview of CSV data."""
    return pd.read_csv(csv_path, nrows=rows)


def get_csv_info(csv_path: str) -> dict:
    """Get information about a CSV file."""
    df = pd.read_csv(csv_path)

    return {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': df.columns.tolist(),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum()
    }
