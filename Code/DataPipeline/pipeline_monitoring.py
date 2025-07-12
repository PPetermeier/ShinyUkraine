"""Pipeline monitoring and execution tracking module.

This module provides comprehensive monitoring capabilities for the ETL pipeline,
including execution tracking, performance metrics, and failure recovery.
"""

import json
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


class PipelineMonitor:
    """Monitors pipeline execution and tracks performance metrics."""

    def __init__(self, log_dir: str = "logs"):
        """Initialize pipeline monitor.

        Args:
            log_dir: Directory for storing execution logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_log: dict[str, Any] = {
            "execution_id": self.execution_id,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "performance_metrics": {},
            "status": "running",
        }

    @contextmanager
    def track_step(
        self, step_name: str, **metadata: Any
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager for tracking individual pipeline steps.

        Args:
            step_name: Name of the pipeline step
            **metadata: Additional metadata for the step

        Yields:
            Step tracking dictionary for adding custom metrics
        """
        step_start = time.time()
        step_data = {
            "step_name": step_name,
            "start_time": datetime.now().isoformat(),
            "metadata": metadata,
            "status": "running",
        }

        try:
            yield step_data
            step_data["status"] = "completed"
        except Exception as e:
            step_data["status"] = "failed"
            step_data["error"] = str(e)
            raise
        finally:
            step_data["duration_seconds"] = time.time() - step_start
            step_data["end_time"] = datetime.now().isoformat()
            self.execution_log["steps"].append(step_data)

    def record_performance_metric(self, metric_name: str, value: Any) -> None:
        """Record a performance metric.

        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        self.execution_log["performance_metrics"][metric_name] = value

    def record_data_lineage(
        self, source: str, target: str, transformation: str, row_count: int
    ) -> None:
        """Record data lineage information.

        Args:
            source: Source data identifier
            target: Target data identifier
            transformation: Description of transformation applied
            row_count: Number of rows processed
        """
        lineage_entry = {
            "source": source,
            "target": target,
            "transformation": transformation,
            "row_count": row_count,
            "timestamp": datetime.now().isoformat(),
        }

        if "data_lineage" not in self.execution_log:
            self.execution_log["data_lineage"] = []
        self.execution_log["data_lineage"].append(lineage_entry)

    def finalize_execution(self, status: str = "completed") -> str:
        """Finalize execution logging and save to file.

        Args:
            status: Final execution status

        Returns:
            Path to saved log file
        """
        self.execution_log["status"] = status
        self.execution_log["end_time"] = datetime.now().isoformat()

        # Calculate total execution time
        start_time = datetime.fromisoformat(self.execution_log["start_time"])
        end_time = datetime.fromisoformat(self.execution_log["end_time"])
        self.execution_log["total_duration_seconds"] = (
            end_time - start_time
        ).total_seconds()

        # Save log file
        log_filename = f"pipeline_execution_{self.execution_id}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, "w") as f:
            json.dump(self.execution_log, f, indent=2, default=str)

        return str(log_path)

    def get_execution_summary(self) -> dict[str, Any]:
        """Get execution summary with key metrics.

        Returns:
            Dictionary containing execution summary
        """
        total_steps = len(self.execution_log["steps"])
        failed_steps = sum(
            1 for step in self.execution_log["steps"] if step["status"] == "failed"
        )
        successful_steps = total_steps - failed_steps

        return {
            "execution_id": self.execution_id,
            "status": self.execution_log["status"],
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "performance_metrics": self.execution_log.get("performance_metrics", {}),
        }


class DataQualityMonitor:
    """Monitors data quality throughout the pipeline."""

    def __init__(self):
        """Initialize data quality monitor."""
        self.quality_checks: dict[str, dict[str, Any]] = {}

    def check_data_completeness(
        self, df: pd.DataFrame, table_name: str, required_columns: list | None = None
    ) -> dict[str, Any]:
        """Check data completeness and missing values.

        Args:
            df: DataFrame to check
            table_name: Name of the table being checked
            required_columns: List of columns that must not be null

        Returns:
            Data completeness report
        """
        completeness_report = {
            "table_name": table_name,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "null_percentage_by_column": {},
            "completely_null_columns": [],
            "required_column_violations": [],
        }

        # Check null percentages
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_percentage = (null_count / len(df)) * 100
            completeness_report["null_percentage_by_column"][col] = round(
                null_percentage, 2
            )

            if null_percentage == 100:
                completeness_report["completely_null_columns"].append(col)

        # Check required columns
        if required_columns:
            for col in required_columns:
                if col in df.columns:
                    if df[col].isnull().any():
                        completeness_report["required_column_violations"].append(col)

        self.quality_checks[f"{table_name}_completeness"] = completeness_report
        return completeness_report

    def check_data_consistency(
        self, df: pd.DataFrame, table_name: str, consistency_rules: dict | None = None
    ) -> dict[str, Any]:
        """Check data consistency based on rules.

        Args:
            df: DataFrame to check
            table_name: Name of the table being checked
            consistency_rules: Dictionary of consistency rules to apply

        Returns:
            Data consistency report
        """
        consistency_report = {
            "table_name": table_name,
            "duplicate_rows": int(df.duplicated().sum()),
            "rule_violations": {},
        }

        if consistency_rules:
            for rule_name, rule_config in consistency_rules.items():
                # Example rule: check if values are within expected range
                if rule_config.get("type") == "range":
                    column = rule_config["column"]
                    min_val = rule_config.get("min")
                    max_val = rule_config.get("max")

                    if column in df.columns:
                        violations = []
                        if min_val is not None:
                            violations.extend(df[df[column] < min_val].index.tolist())
                        if max_val is not None:
                            violations.extend(df[df[column] > max_val].index.tolist())

                        consistency_report["rule_violations"][rule_name] = {
                            "violation_count": len(violations),
                            "violation_rows": violations[:10],  # First 10 violations
                        }

        self.quality_checks[f"{table_name}_consistency"] = consistency_report
        return consistency_report

    def generate_quality_report(self) -> dict[str, Any]:
        """Generate comprehensive data quality report.

        Returns:
            Complete data quality report
        """
        return {
            "quality_checks_performed": len(self.quality_checks),
            "checks": self.quality_checks,
            "generated_at": datetime.now().isoformat(),
        }
