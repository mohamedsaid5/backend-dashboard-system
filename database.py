"""
Database connection utilities
Handles SQLite database connections
"""

import sqlite3
import os

DB_NAME = "demo_dashboard.db"


def get_connection():
    """Get SQLite database connection"""
    try:
        return sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def close_connection(connection, cursor):
    """Close database connection and cursor"""
    if cursor:
        cursor.close()
    if connection:
        connection.close()


def db_exists():
    """Check if database file exists"""
    return os.path.exists(DB_NAME)
