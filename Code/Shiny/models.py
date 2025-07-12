"""Data models and validation schemas for the Ukraine Support Tracker.

This module defines Pydantic models for data validation throughout the application,
ensuring type safety and data integrity for dashboard components.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class AidType(str, Enum):
    """Enumeration of support aid types."""

    MILITARY = "military"
    FINANCIAL = "financial"
    HUMANITARIAN = "humanitarian"
    REFUGEE = "refugee"


class DonorGroup(str, Enum):
    """Enumeration of donor country groups."""

    UNITED_STATES = "united_states"
    EUROPE = "europe"
    EU_INSTITUTIONS = "EU Institutions"
    OTHER_DONORS = "other_donors"


class CountrySummary(BaseModel):
    """Model for country-level aid summary data."""

    country: str = Field(..., description="Country name")
    total_aid_eur: float | None = Field(None, description="Total aid in EUR billions")
    total_aid_usd: float | None = Field(None, description="Total aid in USD billions")
    military_aid: float | None = Field(None, description="Military aid amount")
    financial_aid: float | None = Field(None, description="Financial aid amount")
    humanitarian_aid: float | None = Field(None, description="Humanitarian aid amount")
    gdp_2021_billion: float | None = Field(None, description="GDP 2021 in billions")

    @validator("country")
    def validate_country_name(cls, v):
        """Validate country name is not empty."""
        if not v or not v.strip():
            raise ValueError("Country name cannot be empty")
        return v.strip()


class TimeSeriesData(BaseModel):
    """Model for time series aid allocation data."""

    month: datetime = Field(..., description="Month of allocation")
    military_aid_eur: float | None = Field(
        None, description="Military aid in EUR billions"
    )
    financial_aid_eur: float | None = Field(
        None, description="Financial aid in EUR billions"
    )
    humanitarian_aid_eur: float | None = Field(
        None, description="Humanitarian aid in EUR billions"
    )
    united_states: float | None = Field(None, description="US aid allocation")
    europe: float | None = Field(None, description="European aid allocation")
    other_donors: float | None = Field(None, description="Other donors allocation")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class WeaponStock(BaseModel):
    """Model for weapon stock and delivery data."""

    equipment_type: str = Field(..., description="Type of military equipment")
    ukraine_need: int | None = Field(None, description="Ukraine's stated need")
    delivered: int | None = Field(None, description="Amount delivered")
    to_be_delivered: int | None = Field(
        None, description="Amount pledged but not delivered"
    )
    ukrainian_stock: int | None = Field(None, description="Pre-war Ukrainian stock")


class FinancialAidBreakdown(BaseModel):
    """Model for financial aid type breakdown."""

    country: str = Field(..., description="Donor country")
    loan: float | None = Field(None, description="Loan amount")
    grant: float | None = Field(None, description="Grant amount")
    guarantee: float | None = Field(None, description="Guarantee amount")
    central_bank_swap_line: float | None = Field(
        None, description="Central bank swap line amount"
    )


class PlotConfiguration(BaseModel):
    """Model for plot configuration settings."""

    title: str = Field(..., description="Plot title")
    x_axis_label: str = Field(..., description="X-axis label")
    y_axis_label: str = Field(..., description="Y-axis label")
    color_palette: dict[str, str] = Field(
        ..., description="Color mapping for plot elements"
    )
    show_legend: bool = Field(True, description="Whether to show legend")
    height: int = Field(400, ge=200, le=1000, description="Plot height in pixels")
    width: int | None = Field(None, ge=200, le=2000, description="Plot width in pixels")


class DataValidationResult(BaseModel):
    """Model for data validation results."""

    table_name: str = Field(..., description="Name of validated table")
    row_count: int = Field(..., ge=0, description="Number of rows")
    column_count: int = Field(..., ge=0, description="Number of columns")
    validation_timestamp: datetime = Field(
        ..., description="When validation was performed"
    )
    passed_checks: list[str] = Field(
        default_factory=list, description="List of passed validation checks"
    )
    failed_checks: list[str] = Field(
        default_factory=list, description="List of failed validation checks"
    )
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.failed_checks) == 0


class DatabaseConnection(BaseModel):
    """Model for database connection configuration."""

    db_path: str = Field(..., description="Path to DuckDB database file")
    read_only: bool = Field(True, description="Whether connection is read-only")
    connection_timeout: int = Field(
        30, ge=1, le=300, description="Connection timeout in seconds"
    )

    @validator("db_path")
    def validate_db_path(cls, v):
        """Validate database path."""
        from pathlib import Path

        if not v:
            raise ValueError("Database path cannot be empty")

        db_file = Path(v)
        if not db_file.exists():
            raise ValueError(f"Database file does not exist: {v}")

        return v


class ChartData(BaseModel):
    """Generic model for chart data with validation."""

    data: list[dict[str, str | int | float | datetime]] = Field(
        ..., description="Chart data points"
    )
    metadata: dict[str, str | int | float] = Field(
        default_factory=dict, description="Chart metadata"
    )

    @validator("data")
    def validate_data_not_empty(cls, v):
        """Validate that data is not empty."""
        if not v:
            raise ValueError("Chart data cannot be empty")
        return v

    def get_column_values(self, column: str) -> list[str | int | float | datetime]:
        """Extract values for a specific column.

        Args:
            column: Column name to extract

        Returns:
            List of values for the specified column
        """
        return [row.get(column) for row in self.data if column in row]


class ErrorResponse(BaseModel):
    """Model for API error responses."""

    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: dict[str, str | int] | None = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When error occurred"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
