"""
Database connection and query functions.
"""

import duckdb
from config import DB_PATH


def get_db_connection():
    """Create and return a database connection."""
    return duckdb.connect(str(DB_PATH))  # DuckDB needs string path


def load_time_series_data(columns=None):
    """
    Load time series data from database.

    Args:
        columns (list, optional): List of column names to fetch. If None, fetches all columns.

    Returns:
        pandas.DataFrame: The requested time series data.
    """
    conn = get_db_connection()

    try:
        # If no columns specified, fetch all columns
        if columns is None:
            columns = [
                "month",
                "united_states_allocated__billion",
                "europe_allocated__billion",
                "military_aid_allocated__billion",
                "military_aid_allocated__billion_without_us",
                "financial_aid_allocated__billion",
                "financial_aid_allocated__billion_without_us",
                "humanitarian_aid_allocated__billion",
            ]

        # Ensure 'month' is always included
        if "month" not in columns:
            columns.insert(0, "month")

        # Build the query
        columns_str = ", ".join(columns)
        query = f"""
            SELECT {columns_str}
            FROM 'c_allocated_over_time'
            ORDER BY month
        """

        df = conn.execute(query).fetchdf()

        return df

    except Exception as e:
        print(f"Error in load_time_series_data: {str(e)}")
        raise
    finally:
        conn.close()


# Define common column sets for different cards
TOTAL_SUPPORT_COLUMNS = ["month", "united_states_allocated__billion", "europe_allocated__billion"]

AID_TYPES_COLUMNS = [
    "month",
    "military_aid_allocated__billion",
    "military_aid_allocated__billion_without_us",
    "financial_aid_allocated__billion",
    "financial_aid_allocated__billion_without_us",
    "humanitarian_aid_allocated__billion",
]
