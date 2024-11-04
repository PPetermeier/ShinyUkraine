"""
Database connection and query functions.
"""

import duckdb
from config import DB_PATH
from .queries import (
    TOTAL_SUPPORT_COLUMNS,
    AID_TYPES_COLUMNS,
    COUNTRY_AID_COLUMNS,
    TIME_SERIES_TABLE,
    COUNTRY_AID_TABLE
)


def get_db_connection():
    """Create and return a database connection."""
    return duckdb.connect(str(DB_PATH))  # DuckDB needs string path


def load_data_from_table(table_name, columns=None, where_clause=None, order_by=None):
    """
    Generic function to load data from a specified table.

    Args:
        table_name (str): Name of the table to query
        columns (list, optional): List of column names to fetch. If None, fetches all columns.
        where_clause (str, optional): WHERE clause for the query
        order_by (str, optional): ORDER BY clause for the query

    Returns:
        pandas.DataFrame: The requested data
    """
    conn = get_db_connection()

    try:
        # Build column list
        columns_str = ", ".join(columns) if columns else "*"

        # Build query
        query = f"SELECT {columns_str} FROM '{table_name}'"
        
        if where_clause:
            query += f" WHERE {where_clause}"
            
        if order_by:
            query += f" ORDER BY {order_by}"

        df = conn.execute(query).fetchdf()
        return df

    except Exception as e:
        print(f"Error in load_data_from_table: {str(e)}")
        raise
    finally:
        conn.close()


def load_time_series_data(columns=None):
    """
    Load time series data from database.

    Args:
        columns (list, optional): List of column names to fetch. If None, fetches all columns.

    Returns:
        pandas.DataFrame: The requested time series data.
    """
    # If no columns specified, use default set
    if columns is None:
        columns = TOTAL_SUPPORT_COLUMNS + AID_TYPES_COLUMNS
        # Remove duplicate 'month' if present
        columns = list(dict.fromkeys(columns))

    # Ensure 'month' is always included
    if "month" not in columns:
        columns.insert(0, "month")

    return load_data_from_table(
        table_name=TIME_SERIES_TABLE,
        columns=columns,
        order_by="month"
    )


def load_country_data(columns=None):
    """
    Load country-level aid data from database.

    Args:
        columns (list, optional): List of column names to fetch. If None, fetches default columns.

    Returns:
        pandas.DataFrame: Country aid data
    """
    # If no columns specified, use default set
    if columns is None:
        columns = COUNTRY_AID_COLUMNS

    total_aid = " + ".join(col for col in columns if col != "country")
    
    return load_data_from_table(
        table_name=COUNTRY_AID_TABLE,
        columns=columns,
        where_clause="country IS NOT NULL",
        order_by=f"({total_aid}) DESC"
    )


# For backward compatibility and convenience
__all__ = [
    "get_db_connection",
    "load_time_series_data",
    "load_country_data",
    "TOTAL_SUPPORT_COLUMNS",
    "AID_TYPES_COLUMNS",
    "COUNTRY_AID_COLUMNS"
]