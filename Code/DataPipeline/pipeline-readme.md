# Ukraine Support Tracker ETL Pipeline

ETL pipeline for processing and analyzing data from the Ukraine Support Tracker maintained by the Kiel Institute for the World Economy. This pipeline transforms Excel-based data into a structured DuckDB database optimized for dashboard visualizations.

## Prerequisites

- Python 3.8+
- Required packages:
  - `duckdb`
  - `pandas`
  - `pyyaml`
  - `openpyxl`
- Excel source file from [IFW Kiel Ukraine Support Tracker](https://www.ifw-kiel.de/publications/ukraine-support-tracker-data-20758/)

## Directory Structure

```
.
├── Data/
│   ├── UkraineSupportTracker.xlsx    # Source Excel file
│   └── country_categories.yaml        # Country grouping definitions
├── Code/
│   ├── DataPipeline/
│   │   ├── ETL.py                    # Main ETL logic
│   │   └── pipeline_config.yaml      # Pipeline configuration
│   └── Shiny/
│       └── Data/                     # Output directory for database
└── main.py                           # Pipeline entry point
```

## Setup and Usage

1. Download the Excel file and place it in `Data/UkraineSupportTracker.xlsx`
2. Create output directory for database:

```bash
mkdir -p Code/Shiny/Data/
```

3. Install dependencies:

```bash
pip install duckdb pandas pyyaml openpyxl
```

4. Run pipeline:

```bash
python main.py
```

## Pipeline Configuration

The ETL pipeline can be configured without coding using the `pipeline_config.yaml` file. Each entry in the configuration represents a sheet from the Excel file and how it should be processed.

### Basic Sheet Configuration

Basic structure for configuring a sheet:

```yaml
- read: true                          # Whether to process this sheet
  extract:
    name: "Sheet Name"                # Exact name of Excel sheet
    column_range: "B:F"               # Excel column range to read
    number_rows: 43                   # Number of data rows to read
    skip_rows: 7                      # Rows to skip before header
    number_header_rows: 2             # Number of header rows
  transform:
    clean_column_names: true          # Apply column name cleaning
  load:
    name: "target_table_name"         # Name of resulting database table
```

### Configuration Options

#### 1. Extract Settings

```yaml
extract:
  name: "Sheet Name"               # Required: Excel sheet name
  column_range: "B:AI"            # Required: Column range (Excel notation)
  number_rows: 43                 # Required: Number of data rows
  skip_rows: 7                    # Required: Rows to skip before data
  number_header_rows: 2           # Optional: Number of header rows (default: 1)
```

#### 2. Transform Settings

```yaml
transform:
  clean_column_names: true        # Convert to snake_case, remove special chars
  columnnames:                    # Rename specific columns
    "Old Name": "New Name"
  datetime:                       # Convert columns to datetime
    "Date Column": "%b-%Y"       # With format string
  datatypes:                      # Set column data types
    "column_name": "float"
  reshape:                        # Reshape data (melt operation)
    type: "melt"
    id_vars: ["column1"]
    value_vars: ["column2"]
    var_name: "category"
    value_name: "amount"
  replace_values:                 # Replace specific values
    "column_name":
      "old_value": "new_value"
  forward_fill_column: "column"   # Fill NA values forward
  entry_correction: true          # Apply specific corrections
  add_columns:                    # Add columns through SQL
    new_column:
      source_table: "other_table"
      join_query: "SELECT ... FROM ..."
```

#### 3. Load Settings

```yaml
load:
  name: "table_name"             # Required: Target table name in database
```

### Example Configurations

#### 1. Simple Time Series Data

```yaml
- read: true
  extract:
    name: "Fig 1. Allocated over time"
    column_range: "B:L"
    number_rows: 33
    skip_rows: 6
    number_header_rows: 1
  transform:
    clean_column_names: true
    datetime:
      Month: "%b-%Y"
  load:
    name: "c_allocated_over_time"
```

#### 2. Complex Data with Reshaping

```yaml
- read: true
  extract:
    name: "Fig 12. Weapon Stocks UKR RU"
    column_range: "B:F"
    number_rows: 6
    skip_rows: 10
    number_header_rows: 1
  transform:
    clean_column_names: true
    reshape:
      type: "melt"
      id_vars: ["item"]
      value_vars: ["howitzer155mm", "mlrs", "tanks", "ifvs"]
      var_name: "equipment_type"
      value_name: "quantity"
  load:
    name: "j_weapon_stocks_base"
```

#### 3. Data with Value Replacements

```yaml
- read: true
  extract:
    name: "Fig 21. Priorities Germany"
    column_range: "B:F"
    number_rows: 6
    skip_rows: 10
    number_header_rows: 1
  transform:
    clean_column_names: true
    replace_values:
      Total bilateral aid:
        .: 0
      EU aid shares:
        .: 0
    datatypes:
      Total bilateral aid: float
      EU aid shares: float
  load:
    name: "x_comparison_germany_abs"
```

## Country Categories Configuration

The `country_categories.yaml` file defines country groupings and ISO codes, which are neede for the map widget in the landing page:

```yaml
EU_Member:
  - "Austria"
  - "Belgium"
  # ... more countries

Geographic_Europe:
  - "Norway"
  - "Switzerland"
  # ... more countries

country_codes:
  "Austria": "AUT"
  "Belgium": "BEL"
  # ... more codes
```

## Output

The pipeline creates `ukrainesupporttracker.db` in the `Code/Shiny/Data/` directory containing:

- Processed data tables
- Country lookup tables with groupings
- Standardized column names and data types

## Troubleshooting

Common issues and solutions:

1. Excel file not found:
   - Verify file path in `Data` directory
   - Check file name case sensitivity

2. Column range errors:
   - Verify column ranges exist in Excel sheet
   - Check for hidden columns/rows

3. Data type conversion errors:
   - Check for unexpected values in columns
   - Verify date formats match configuration

## Output Database Schema

The resulting DuckDB database includes tables following this naming convention:

- `a_summary_€`: Summary data in euros
- `b_summary_$`: Summary data in dollars
- `c_allocated_over_time`: Time series allocations
- Additional tables as configured in pipeline_config.yaml

## Acknowledgments

Based on data from the [Ukraine Support Tracker](https://www.ifw-kiel.de/topics/war-against-ukraine/ukraine-support-tracker/) by the Kiel Institute for the World Economy.
