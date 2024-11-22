"""
Database connection and query functions.
"""

import duckdb
from config import DB_PATH

from .queries import (
    AID_TYPES_COLUMNS,
    COUNTRY_AID_COLUMNS,
    COUNTRY_AID_TABLE,
    TIME_SERIES_TABLE,
    TOTAL_SUPPORT_COLUMNS,
    WEAPON_STOCKS_QUERY,
)


def get_db_connection():
    """Create and return a database connection."""
    return duckdb.connect(str(DB_PATH), read_only=True)


def load_data_from_table(table_name_or_query: str, columns=None, where_clause=None, order_by=None):
    """Load data from table or execute query."""
    conn = get_db_connection()
    try:
        is_query = table_name_or_query.strip().upper().startswith(("SELECT", "WITH"))

        if is_query:
            df = conn.execute(table_name_or_query).fetchdf()
        else:
            columns_str = ", ".join(columns) if columns else "*"
            query = f'SELECT {columns_str} FROM "{table_name_or_query}"'

            if where_clause:
                query += f" WHERE {where_clause}"

            if order_by:
                query += f" ORDER BY {order_by}"

            df = conn.execute(query).fetchdf()

        return df
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

    return load_data_from_table(table_name_or_query=TIME_SERIES_TABLE, columns=columns, order_by="month")


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
        table_name_or_query=COUNTRY_AID_TABLE,
        columns=columns,
        where_clause="country IS NOT NULL",
        order_by=f"({total_aid}) DESC",
    )


def load_weapon_stocks_data():
    """
    Load weapon stocks comparison data from database.

    Returns:
        pandas.DataFrame: Weapon stocks data with countries, equipment types,
                        status and quantities
    """
    return load_data_from_table(table_name_or_query=WEAPON_STOCKS_QUERY)


# For backward compatibility and convenience
__all__ = [
    "get_db_connection",
    "load_time_series_data",
    "load_country_data",
    "TOTAL_SUPPORT_COLUMNS",
    "AID_TYPES_COLUMNS",
    "COUNTRY_AID_COLUMNS",
]
