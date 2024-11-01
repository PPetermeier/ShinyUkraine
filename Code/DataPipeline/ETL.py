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
            transformed_data = transform(raw_data, sheet_configuration["transform"])
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
    Creates a lookup table for countries with their categories.
    Special handling for Geographic Europe and EU membership:
    - EU members are automatically part of Geographic Europe
    - Geographic Europe includes both explicit Geographic Europe countries and EU members

    Parameters:
    country_categories: dict from country_categories.yaml

    Returns:
    DataFrame with country info and category columns
    """
    # Get unique countries from all category lists
    all_countries = sorted(set(country for category in country_categories.values() for country in category))

    # Create base DataFrame with country_id
    lookup_df = pd.DataFrame({"country_id": range(1, len(all_countries) + 1), "country_name": all_countries})

    # Add regular category columns
    for category in country_categories:
        if category not in ["Geographic_Europe", "EU_Member"]:  # Skip these for special handling
            lookup_df[category] = lookup_df["country_name"].isin(country_categories[category])

    # Special handling for EU and Geographic Europe
    lookup_df["EU_member"] = lookup_df["country_name"].isin(country_categories["EU_Member"])
    lookup_df["geographic_europe"] = (
        lookup_df["country_name"].isin(country_categories["Geographic_Europe"])  # Explicit Geographic Europe countries
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


def transform(data: pd.DataFrame, config_transform: dict) -> pd.DataFrame:
    config_transform_keys = config_transform.keys()
    if "datatypes" in config_transform_keys:
        data = data.astype(config_transform["datatypes"])

    if "datetime" in config_transform:
        date_columns = list(config_transform["datetime"].keys())
        date_format = str(list(config_transform["datetime"].values())[0])
        data[date_columns] = data[date_columns].apply(pd.to_datetime, format=date_format)


    if "columnnames" in config_transform_keys:
        data = data.rename(columns=lambda col: config_transform["columnnames"].get(col, col))

    if "clean_column_names" in config_transform_keys:
        """ Standardizes column names by:
        - Converting to lowercase
        - Replacing spaces with underscores
        - Removing special characters
        - Trimming whitespace
        Uses vectorized operations for efficiency.
        """
        data.columns = pd.Series(data.columns).str.lower().str.replace("\s+", "_", regex=True).str.replace("[^a-z0-9_]", "", regex=True).str.strip("_")

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
