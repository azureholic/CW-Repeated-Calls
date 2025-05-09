# Repeated Calls
This repository contains the code for the CodeWith project "Repeated Calls".

## Installation
It is highly recommended to configure Python using [Poetry](https://python-poetry.org/docs/):

```bash
poetry install
```

Otherwise, install all packages using [requirements.txt](/requirements.txt). Note that this file may lack behind.

> **Note for developers**: when making changes to the dependencies, update the requirements file by running `poetry export --without-hashes --format=requirements.txt > requirements.txt`.

## Database management
There is a `database` module which can be used for managing the database in a Pythonic way using `sqlalchemy`. This includes operations like defining table schemas, creating tables and read/write operations. In order to set up the connection, define the environment variables `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE` and `POSTGRES_PORT` (optional), either as environment variables or in a `.env` file.

All tables are defined in [here](/repeated_calls/database/tables.py). To populate the database using CSV files, run the migrations script using

```bash
poetry run python repeated_calls/database/migrate.py --data /path/to/data
```

Note that the CSV files must be named after the tables they will populate. For example, if the table is called `users`, the CSV file should be named `users.csv`.
