"""
ETL pipeline for the Ukraine Support Tracker application.

This module handles the extraction, transformation and loading of data from Excel
files into a DuckDB database. It includes functionality for:
- Loading configuration from YAML files
- Creating country lookup tables
- Processing multiple Excel sheets with configurable transformations
- Loading transformed data into database tables

The pipeline is configured via YAML files that specify extraction parameters,
transformation rules, and loading destinations for each data sheet.
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Union

import duckdb
import pandas as pd
import yaml
from pandas import DataFrame


class TransformationType(Enum):
    """Enumeration of supported data transformation types."""

    MELT = auto()
    CLEAN = auto()
    RENAME = auto()
    REPLACE = auto()
    FORWARD_FILL = auto()
    CORRECT = auto()
    DATATYPE = auto()
    DATETIME = auto()
    ADD_COLUMNS = auto()


@dataclass
class ExtractionConfig:
    """Configuration for data extraction from Excel sheets."""

    name: str
    column_range: str
    number_rows: int
    skip_rows: int
    number_header_rows: int = 1


@dataclass
class TransformationConfig:
    """Configuration for data transformations."""

    clean_column_names: bool = False
    columnnames: Optional[Dict[str, str]] = None
    datetime: Optional[Dict[str, str]] = None
    datatypes: Optional[Dict[str, Any]] = None
    reshape: Optional[Dict[str, Any]] = None
    replace_values: Optional[Dict[str, Dict[Any, Any]]] = None
    forward_fill_column: Optional[str] = None
    entry_correction: bool = False
    add_columns: Optional[Dict[str, Dict[str, str]]] = None


@dataclass
class LoadConfig:
    """Configuration for data loading into database."""

    name: str


class ETLPipeline:
    """Handles ETL operations for Ukraine Support Tracker data."""

    def __init__(
        self,
        database: duckdb.DuckDBPyConnection,
        excel_path: Union[str, Path],
        config_path: Union[str, Path],
        country_categories_path: Union[str, Path],
    ):
        """
        Initialize ETL pipeline.

        Args:
            database: DuckDB connection
            excel_path: Path to Excel data file
            config_path: Path to pipeline configuration YAML
            country_categories_path: Path to country categories YAML
        """
        self.database = database
        self.excel_path = Path(excel_path)
        self.config_path = Path(config_path)
        self.country_categories_path = Path(country_categories_path)

        self.config = self._load_config(self.config_path)
        self.country_categories = self._load_config(self.country_categories_path)

    def run(self) -> None:
        """Execute the complete ETL pipeline."""
        self._initialize_country_lookup()

        for sheet_config in self.config:
            if sheet_config.get("read", False):
                data = self._extract(sheet_config["extract"])
                transformed = self._transform(data, sheet_config["transform"])
                self._load(transformed, sheet_config["load"])

    def _initialize_country_lookup(self) -> None:
        """Create and load country lookup table into database."""
        lookup_df = self._create_country_lookup()
        self.database.register("zz_country_lookup", lookup_df)
        self.database.execute(
            "CREATE TABLE zz_country_lookup AS SELECT * FROM zz_country_lookup"
        )

    def _create_country_lookup(self) -> DataFrame:
        """
        Create country lookup DataFrame with categories and ISO codes.

        Returns:
            DataFrame with country information and category flags
        """
        category_lists = {
            k: v for k, v in self.country_categories.items() if k != "country_codes"
        }
        all_countries = sorted(
            set(country for category in category_lists.values() for country in category)
        )

        lookup_df = pd.DataFrame(
            {
                "country_id": range(1, len(all_countries) + 1),
                "country_name": all_countries,
                "iso3_code": [
                    self.country_categories["country_codes"].get(country)
                    for country in all_countries
                ],
            }
        )

        # Add category columns
        for category in category_lists:
            if category not in ["Geographic_Europe", "EU_Member"]:
                lookup_df[category] = lookup_df["country_name"].isin(
                    category_lists[category]
                )

        # Special handling for EU and Geographic Europe
        lookup_df["EU_member"] = lookup_df["country_name"].isin(
            category_lists["EU_Member"]
        )
        lookup_df["geographic_europe"] = (
            lookup_df["country_name"].isin(category_lists["Geographic_Europe"])
            | lookup_df["EU_member"]
        )

        return lookup_df

    def _extract(self, config: Dict[str, Any]) -> DataFrame:
        """
        Extract data from Excel sheet according to configuration.

        Args:
            config: Extraction configuration dictionary

        Returns:
            DataFrame containing extracted data
        """
        extract_config = ExtractionConfig(**config)

        data = pd.read_excel(
            io=self.excel_path,
            sheet_name=extract_config.name,
            usecols=extract_config.column_range,
            nrows=extract_config.number_rows,
            skiprows=extract_config.skip_rows,
            header=None,
        )

        headers = (
            data.iloc[: extract_config.number_header_rows]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=0)
            .str.strip()
            .str.replace(r"\s+", " ")
        )

        data.columns = headers
        data = data.drop(range(extract_config.number_header_rows)).reset_index(
            drop=True
        )

        return data

    def _transform(self, data: DataFrame, config: Dict[str, Any]) -> DataFrame:
        """
        Apply transformations to DataFrame according to configuration.

        Args:
            data: Input DataFrame
            config: Transformation configuration dictionary

        Returns:
            Transformed DataFrame
        """
        transform_config = TransformationConfig(**config)

        transformers = {
            TransformationType.REPLACE: self._apply_value_replacements,
            TransformationType.FORWARD_FILL: self._apply_forward_fill,
            TransformationType.CORRECT: self._apply_entry_corrections,
            TransformationType.DATATYPE: self._apply_datatypes,
            TransformationType.DATETIME: self._apply_datetime_conversion,
            TransformationType.RENAME: self._apply_column_renames,
            TransformationType.CLEAN: self._clean_column_names,
            TransformationType.MELT: self._reshape_data,
            TransformationType.ADD_COLUMNS: self._add_columns_from_sql,
        }

        # Apply transformations based on config
        for transform_type, transformer in transformers.items():
            data = transformer(data, transform_config)

        return data

    def _load(self, data: DataFrame, config: Dict[str, str]) -> None:
        """
        Load DataFrame into database table.

        Args:
            data: DataFrame to load
            config: Loading configuration dictionary
        """
        load_config = LoadConfig(**config)
        self.database.register(load_config.name, data)
        self.database.execute(
            f"CREATE TABLE {load_config.name} AS SELECT * FROM {load_config.name}"
        )

    @staticmethod
    def _load_config(path: Path) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Args:
            path: Path to YAML file

        Returns:
            Configuration dictionary
        """
        with open(path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _apply_value_replacements(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Apply value replacements to specified columns."""
        if config.replace_values:
            for column, replace_dict in config.replace_values.items():
                data[column] = (
                    data[column].apply(lambda x: replace_dict.get(x, x)).astype(float)
                )
        return data

    def _apply_forward_fill(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Forward fill values in specified column."""
        if config.forward_fill_column:
            data[config.forward_fill_column] = data[config.forward_fill_column].ffill()
        return data

    def _apply_entry_corrections(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Apply specific entry corrections."""
        if config.entry_correction:
            row_index = data[data.iloc[:, 0] == "German aid to Ukraine"].index
            data.iloc[row_index, 3] = 18.08
        return data

    def _apply_datatypes(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Convert columns to specified datatypes."""
        if config.datatypes:
            data = data.astype(config.datatypes)
        return data

    def _apply_datetime_conversion(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Convert specified columns to datetime."""
        if config.datetime:
            for column, format_str in config.datetime.items():
                data[column] = pd.to_datetime(data[column], format=format_str)
        return data

    def _apply_column_renames(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Rename columns according to mapping."""
        if config.columnnames:
            data = data.rename(columns=lambda col: config.columnnames.get(col, col))
        return data

    def _clean_column_names(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Clean and standardize column names."""
        if config.clean_column_names:
            data.columns = (
                pd.Series(data.columns)
                .str.lower()
                .str.replace(r"\s+", "_", regex=True)
                .str.replace(r"[^a-z0-9_]", "", regex=True)
                .str.strip("_")
            )
        return data

    def _reshape_data(self, data: DataFrame, config: TransformationConfig) -> DataFrame:
        """Reshape data according to configuration."""
        if config.reshape and config.reshape["type"] == "melt":
            data = pd.melt(
                data,
                id_vars=config.reshape["id_vars"],
                value_vars=config.reshape["value_vars"],
                var_name=config.reshape["var_name"],
                value_name=config.reshape["value_name"],
            )
        return data

    def _add_columns_from_sql(
        self, data: DataFrame, config: TransformationConfig
    ) -> DataFrame:
        """Add columns using SQL queries."""
        if not config.add_columns:
            return data

        temp_table = "temp_transform_table"
        self.database.register(temp_table, data)

        try:
            for column_config in config.add_columns.values():
                data = self.database.execute(column_config["join_query"]).fetchdf()
        finally:
            self.database.execute(f"DROP VIEW IF EXISTS {temp_table}")
            self.database.execute(f"DROP TABLE IF EXISTS {temp_table}")

        return data
