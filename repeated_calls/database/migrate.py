"""Module for database migration and data ingestion."""

import argparse
import os

import pandas as pd
from sqlalchemy import insert
from sqlalchemy.orm import Session

from repeated_calls.database import engine, tables
from repeated_calls.utils.loggers import Logger

logger = Logger()


def main(data_path: str):
    """Drop and recreate the database table(s) and insert data from CSV files in `data_path`.

    Note that the CSV files must be named after the tables they will populate. For example, if the
    table is called `users`, the CSV file should be named `users.csv`.

    Args:
        data_path (str): Path to the directory containing the CSV files.
    """
    # Check if the data path exists
    abs_path = os.path.abspath(data_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Data path {abs_path} does not exist.")
    else:
        logger.info(f"Loading data from: {abs_path}")

    # Wipe and recreate the database
    logger.info(f"Connecting to database: {engine.url}")
    metadata = tables.Base.metadata
    metadata.drop_all(engine)
    metadata.create_all(engine)

    # Load data from CSV files into the database
    for t in metadata.sorted_tables:
        path = os.path.join(abs_path, f"{t.name}.csv")
        if not os.path.exists(path):
            logger.warning(f"File {path} does not exist. Skipping table {t.name}.")
            continue

        logger.info(f"Inserting data {path} -> {t.name}")
        df = pd.read_csv(path)
        records = df.to_dict(orient="records")

        with Session(engine) as session:
            try:
                session.execute(insert(t), records)
            except Exception:
                session.rollback()
                raise
            else:
                session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database migration script.")
    parser.add_argument("--data", type=str, help="Path to the data file(s) to ingest.")
    args = parser.parse_args()

    if not args.data:
        path = "data/"
        logger.warning(f"No data path provided, using default {path}.")
    else:
        path = args.data

    main(path)
