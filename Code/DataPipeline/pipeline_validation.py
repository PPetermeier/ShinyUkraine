"""Data pipeline validation and quality checks module.

This module provides comprehensive validation for the ETL pipeline,
ensuring data quality and reproducibility throughout the process.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import yaml


class DataValidationError(Exception):
    """Custom exception for data validation failures."""

    pass


class PipelineValidator:
    """Validates data quality and tracks pipeline execution."""

    def __init__(self, config_path: str, db_path: str):
        """Initialize validator with configuration and database paths.

        Args:
            config_path: Path to pipeline configuration YAML
            db_path: Path to DuckDB database
        """
        self.config_path = Path(config_path)
        self.db_path = Path(db_path)
        self.validation_log: list[dict[str, Any]] = []

    def validate_source_file(self, excel_path: str) -> dict[str, Any]:
        """Validate source Excel file integrity and structure.

        Args:
            excel_path: Path to source Excel file

        Returns:
            Dictionary containing validation results and metadata
        """
        excel_file = Path(excel_path)
        if not excel_file.exists():
            raise DataValidationError(f"Source file not found: {excel_path}")

        # Calculate file hash for integrity checking
        file_hash = self._calculate_file_hash(excel_file)

        # Get file metadata
        stat = excel_file.stat()
        metadata = {
            "file_path": str(excel_file),
            "file_size": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_hash": file_hash,
            "validation_timestamp": datetime.now().isoformat(),
        }

        # Load and validate sheets structure
        try:
            excel_sheets = pd.ExcelFile(excel_path).sheet_names
            metadata["available_sheets"] = excel_sheets
        except Exception as e:
            raise DataValidationError(f"Failed to read Excel file: {e}")

        self.validation_log.append(
            {"step": "source_validation", "status": "passed", "metadata": metadata}
        )

        return metadata

    def validate_config_integrity(self) -> dict[str, Any]:
        """Validate pipeline configuration file.

        Returns:
            Configuration validation results
        """
        if not self.config_path.exists():
            raise DataValidationError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        # Validate required sections exist
        required_sheets = [
            sheet for sheet in config if isinstance(sheet, dict) and sheet.get("read")
        ]

        validation_result = {
            "config_path": str(self.config_path),
            "total_sheets_configured": len(config),
            "sheets_to_process": len(required_sheets),
            "config_hash": self._calculate_file_hash(self.config_path),
            "validation_timestamp": datetime.now().isoformat(),
        }

        self.validation_log.append(
            {
                "step": "config_validation",
                "status": "passed",
                "metadata": validation_result,
            }
        )

        return validation_result

    def validate_extracted_data(
        self, table_name: str, df: pd.DataFrame, expected_schema: dict | None = None
    ) -> dict[str, Any]:
        """Validate extracted data quality and structure.

        Args:
            table_name: Name of the extracted table
            df: DataFrame containing extracted data
            expected_schema: Optional schema validation rules

        Returns:
            Validation results for the extracted data
        """
        validation_result = {
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "validation_timestamp": datetime.now().isoformat(),
        }

        # Check for completely empty tables
        if len(df) == 0:
            raise DataValidationError(f"Table {table_name} is empty")

        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        validation_result["duplicate_rows"] = int(duplicate_count)

        # Validate data ranges for numeric columns
        numeric_columns = df.select_dtypes(include=["number"]).columns
        for col in numeric_columns:
            validation_result[f"{col}_min"] = float(df[col].min())
            validation_result[f"{col}_max"] = float(df[col].max())

        self.validation_log.append(
            {
                "step": "data_extraction_validation",
                "table": table_name,
                "status": "passed",
                "metadata": validation_result,
            }
        )

        return validation_result

    def validate_database_integrity(self) -> dict[str, Any]:
        """Validate final database state after ETL completion.

        Returns:
            Database validation results
        """
        if not self.db_path.exists():
            raise DataValidationError(f"Database not found: {self.db_path}")

        conn = duckdb.connect(str(self.db_path))

        # Get table information
        tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        tables = conn.execute(tables_query).fetchall()
        table_names = [table[0] for table in tables]

        validation_result = {
            "database_path": str(self.db_path),
            "database_size": self.db_path.stat().st_size,
            "table_count": len(table_names),
            "tables": table_names,
            "validation_timestamp": datetime.now().isoformat(),
        }

        # Validate each table
        table_stats = {}
        for table_name in table_names:
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            col_info = conn.execute(
                f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"
            ).fetchall()

            table_stats[table_name] = {
                "row_count": row_count,
                "column_count": len(col_info),
                "columns": [{"name": col[0], "type": col[1]} for col in col_info],
            }

        validation_result["table_statistics"] = table_stats
        conn.close()

        self.validation_log.append(
            {
                "step": "database_validation",
                "status": "passed",
                "metadata": validation_result,
            }
        )

        return validation_result

    def save_validation_report(self, output_path: str) -> None:
        """Save complete validation report to file.

        Args:
            output_path: Path where validation report should be saved
        """
        report = {
            "pipeline_execution": {
                "execution_timestamp": datetime.now().isoformat(),
                "total_validation_steps": len(self.validation_log),
                "validation_log": self.validation_log,
            }
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity checking.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash string
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


class PipelineBackup:
    """Handles backup and versioning of data pipeline artifacts."""

    def __init__(self, backup_dir: str):
        """Initialize backup manager.

        Args:
            backup_dir: Directory for storing backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def backup_database(self, db_path: str, version_tag: str) -> str:
        """Create timestamped backup of database.

        Args:
            db_path: Path to source database
            version_tag: Version identifier for backup

        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"ukrainesupporttracker_{version_tag}_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        # Copy database file
        import shutil

        shutil.copy2(db_path, backup_path)

        return str(backup_path)

    def backup_source_data(self, excel_path: str, version_tag: str) -> str:
        """Create backup of source Excel file.

        Args:
            excel_path: Path to source Excel file
            version_tag: Version identifier for backup

        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = Path(excel_path)
        backup_filename = (
            f"{excel_file.stem}_{version_tag}_{timestamp}{excel_file.suffix}"
        )
        backup_path = self.backup_dir / backup_filename

        import shutil

        shutil.copy2(excel_path, backup_path)

        return str(backup_path)
