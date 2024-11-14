import os

import duckdb
import pandas as pd
import yaml


def run(excel_file_location: os.path, config_file_location: os.path, database: duckdb.DuckDBPyConnection) -> None:
    """
    Orchestrates the ETL processing

    parameters:
    excel_file_location: os.path object with the location of the excel file
    config_file_location: os.path object with the location of the yaml file with the pipeline configuration
    database: a DuckDB connection object to the file where the database will be created

    returns:
    None
    """
    config = load_config(config_file_location)

    country_categories = load_config(os.path.join(os.getcwd(), "Data/country_categories.yaml"))

    # Create and load country lookup table first
    country_lookup = create_country_lookup(country_categories)
    database.register("zz_country_lookup", country_lookup)
    database.execute("CREATE TABLE zz_country_lookup AS SELECT * FROM zz_country_lookup")

    for sheet_configuration in config:
        if sheet_configuration["read"]:
            raw_data = extract(excel_file_location, sheet_configuration["extract"])
            transformed_data = transform(raw_data, sheet_configuration["transform"], database)
            load(transformed_data, sheet_configuration["load"], database)


def load_config(config_file_location: os.path) -> dict:
    """
    Loads the YAML configuration file.

    parameter:
    config_file_location: a path object with the location of the configuration .yaml file

    returns:
    a dictionary of the yaml file
    """
    with open(config_file_location, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def create_country_lookup(country_categories: dict) -> pd.DataFrame:
    """
    Creates a lookup table for countries with their categories and ISO codes.
    Special handling for Geographic Europe and EU membership:
    - EU members are automatically part of Geographic Europe
    - Geographic Europe includes both explicit Geographic Europe countries and EU members

    Parameters:
    country_categories: dict from country_categories.yaml

    Returns:
    DataFrame with country info, category columns, and ISO codes
    """
    # Get unique countries from all category lists (excluding the country_codes dictionary)
    category_lists = {k: v for k, v in country_categories.items() if k != "country_codes"}
    all_countries = sorted(set(country for category in category_lists.values() for country in category))

    # Create base DataFrame with country_id and ISO codes
    lookup_df = pd.DataFrame(
        {
            "country_id": range(1, len(all_countries) + 1),
            "country_name": all_countries,
            "iso3_code": [country_categories["country_codes"].get(country) for country in all_countries],
        }
    )

    # Add regular category columns
    for category in category_lists:
        if category not in ["Geographic_Europe", "EU_Member"]:  # Skip these for special handling
            lookup_df[category] = lookup_df["country_name"].isin(category_lists[category])

    # Special handling for EU and Geographic Europe
    lookup_df["EU_member"] = lookup_df["country_name"].isin(category_lists["EU_Member"])
    lookup_df["geographic_europe"] = (
        lookup_df["country_name"].isin(category_lists["Geographic_Europe"])  # Explicit Geographic Europe countries
        | lookup_df["EU_member"]  # EU members are automatically part of Geographic Europe
    )

    return lookup_df


def extract(excel_file_location: os.path, config_extract: dict) -> pd.DataFrame:
    """
    Extracts a sheet from an excel file according to the configuration dictionary
    Note that the summary row is excluded as this is typically done by a simple aggregation SQL statement

    parameter:
    excel_file_location: a os.path object with the location of the excel file
    config_extract: a dictionary containing the configuration for the extraction stage
    """

    num_header_rows = config_extract.get("number_header_rows", 1)

    data = pd.read_excel(
        io=excel_file_location,
        sheet_name=config_extract["name"],
        usecols=config_extract["column_range"],
        nrows=config_extract["number_rows"],
        skiprows=config_extract["skip_rows"],
        header=None,  # Create Header after reading
    )
    # Combine the first `num_header_rows` rows to form new headers after converting NaNs to empty strings
    headers = (
        data.iloc[:num_header_rows]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=0)
        .str.strip()  # Remove leading/trailing spaces
        .str.replace("\s+", " ")  # Replace multiple spaces with single space
    )
    # Drop the header rows and reset the index
    data.columns = headers
    data = data.drop(range(num_header_rows)).reset_index(drop=True)
    return data


def transform(data: pd.DataFrame, config_transform: dict, database: duckdb.DuckDBPyConnection = None) -> pd.DataFrame:
    """
    Transforms data according to configuration.

    Parameters:
    - data: pd.DataFrame - The data to transform
    - config_transform: dict - Configuration for transformations
    - database: duckdb.DuckDBPyConnection - Database connection for SQL-based transformations

    Returns:
    - pd.DataFrame: Transformed data
    """
    config_transform_keys = config_transform.keys()

    if "replace_values" in config_transform_keys:
        for column, replace_dict in config_transform['replace_values'].items():
        # Apply the replacement dictionary to the column
            data[column] = data[column].apply(lambda x: replace_dict.get(x, x)).astype(float)

    if "forward_fill_column" in config_transform_keys:
        data[config_transform['forward_fill_column']] = data[config_transform['forward_fill_column']].ffill()
    
    if "entry_correction" in config_transform_keys:
        row_index = data[data.iloc[:,0 ]== 'German aid to Ukraine'].index
        data.iloc[row_index, 3] = 18.08

    if "datatypes" in config_transform_keys:
        data = data.astype(config_transform["datatypes"])

    if "datetime" in config_transform:
        date_columns = list(config_transform["datetime"].keys())
        date_format = str(list(config_transform["datetime"].values())[0])
        data[date_columns] = data[date_columns].apply(pd.to_datetime, format=date_format)

    if "columnnames" in config_transform_keys:
        data = data.rename(columns=lambda col: config_transform["columnnames"].get(col, col))

    if "clean_column_names" in config_transform_keys:
        data.columns = pd.Series(data.columns).str.lower().str.replace("\s+", "_", regex=True).str.replace("[^a-z0-9_]", "", regex=True).str.strip("_")



    # Apply existing transformations
    if "reshape" in config_transform_keys:
            reshape_config = config_transform["reshape"]
            if reshape_config["type"] == "melt":
                data = pd.melt(
                    data,
                    id_vars=reshape_config["id_vars"],
                    value_vars=reshape_config["value_vars"],
                    var_name=reshape_config["var_name"],
                    value_name=reshape_config["value_name"]
                )


    # Handle SQL-based column additions
    if "add_columns" in config_transform_keys and database is not None:
        data = _add_columns_from_sql(data, config_transform["add_columns"], database)

    return data


def load(data: pd.DataFrame, config_load: dict, database: duckdb.DuckDBPyConnection) -> None:
    """
    Loads a DataFrame into a DuckDB table.

    Parameters:
    - data: pd.DataFrame - The DataFrame to be loaded.
    - config_load: dict - A configuration dictionary containing the table name.
    - database: duckdb.DuckDBPyConnection - The DuckDB database connection.
    """
    # Use DuckDB's built-in functionality to create the table directly from the DataFrame
    table_name = config_load["name"]
    database.register(table_name, data)
    database.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")


def _add_columns_from_sql(data: pd.DataFrame, add_columns_config: dict, database: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Adds columns to DataFrame using SQL queries.

    Parameters:
    - data: pd.DataFrame - Original data
    - add_columns_config: dict - Configuration for columns to add
    - database: duckdb.DuckDBPyConnection - Database connection

    Returns:
    - pd.DataFrame: Data with added columns
    """
    # Register the input DataFrame as a temporary table
    temp_table_name = "temp_transform_table"
    database.register(temp_table_name, data)

    try:
        for column_name, column_config in add_columns_config.items():
            data = database.execute(column_config["join_query"]).fetchdf()

    finally:
        # Clean up temporary table
        database.execute(f"DROP VIEW IF EXISTS {temp_table_name}")
        database.execute(f"DROP TABLE IF EXISTS {temp_table_name}")

    return data
