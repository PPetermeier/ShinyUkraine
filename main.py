import os

import duckdb

from Code.DataPipeline.ETL import ETLPipeline

if __name__ == "__main__":
    directory = os.getcwd()

    # File paths
    excel_file_location = os.path.join(
        directory, "Original_Data/UkraineSupportTracker.xlsx"
    )
    config_file_location = os.path.join(
        directory, "Code/DataPipeline/pipeline_config.yaml"
    )
    country_categories_location = os.path.join(
        directory, "Original_Data/country_categories.yaml"
    )

    # Database connection
    db_path = os.path.join(directory, "Code/Shiny/Data/UkraineSupportTracker.db")
    database = duckdb.connect(db_path)

    # Create pipeline with correct argument order
    pipeline = ETLPipeline(
        database=database,
        excel_path=excel_file_location,
        config_path=config_file_location,
        country_categories_path=country_categories_location,
    )
    pipeline.run()
