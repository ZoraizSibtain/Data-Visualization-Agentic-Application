#!/usr/bin/env python3
"""
Database setup script for Agentic Data Analysis application.
Run this script to initialize the database with schema and sample data.
"""

import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database_setup import initialize_database, test_database_connection
from config import DEFAULT_CSV_PATH


def main():
    parser = argparse.ArgumentParser(description='Initialize the database for Agentic Data Analysis')
    parser.add_argument('--csv', type=str, help='Path to CSV file to load', default=str(DEFAULT_CSV_PATH))
    parser.add_argument('--reset', action='store_true', help='Drop and recreate all tables')

    args = parser.parse_args()

    print("=" * 50)
    print("Agentic Data Analysis - Database Setup")
    print("=" * 50)
    print()

    # Test connection
    print("Testing database connection...")
    if not test_database_connection():
        print("\nFailed to connect to database.")
        print("Please check your .env file and ensure PostgreSQL is running.")
        sys.exit(1)

    print("Connection successful!\n")

    # Initialize database
    try:
        initialize_database(csv_path=args.csv, reset=args.reset)
        print("\n" + "=" * 50)
        print("Setup complete! You can now run the application:")
        print("  streamlit run Home.py")
        print("=" * 50)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
