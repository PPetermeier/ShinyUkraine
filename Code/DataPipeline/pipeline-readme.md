# Ukraine Support Tracker ETL Pipeline

ETL pipeline for processing and analyzing data from the Ukraine Support Tracker maintained by the Kiel Institute for the World Economy.

## Prerequisites

- Python 3.8+
- Required packages: `duckdb`, `pandas`, `pyyaml`
- Excel source file from [IFW Kiel Ukraine Support Tracker](https://www.ifw-kiel.de/publications/ukraine-support-tracker-data-20758/)

## Directory Structure

```
.
├── Data/
│   ├── UkraineSupportTracker.xlsx
│   └── country_categories.yaml
├── Code/
│   ├── DataPipeline/
│   │   ├── ETL.py
│   │   └── pipeline_config.yaml
│   └── Shiny/
│       └── Data/
└── main.py
```

## Usage

1. Download the Excel file and place it in `Data/UkraineSupportTracker.xlsx`
2. Create directory for database: `Code/Shiny/Data/`
3. Run pipeline:

```bash
python main.py
```

## Configuration

- `pipeline_config.yaml`: Controls which sheets to process and how
- `country_categories.yaml`: Defines country groupings and ISO codes

## Output

Creates `UkraineSupportTracker.db` with processed tables ready for analysis.
