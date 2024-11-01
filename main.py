import os
import duckdb
from Code.DataPipeline import ETL as Pipeline

if __name__ == "__main__":
    # Set location of the excel and yaml file to use
    directory = os.getcwd()
    excel_file_location = os.path.join(directory, "Data/UkraineSupportTracker.xlsx")
    config_file_location = os.path.join(directory, "Code/DataPipeline/pipeline_config.yaml")
    # Create a destination Duckdb
    database = duckdb.connect("Data/UkraineSupportTracker.db")

    Pipeline.run(excel_file_location, config_file_location, database)
    
