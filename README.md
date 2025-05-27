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

## MCP Data Service

For details on the MCP Data Service (API, Dockerization, deployment, etc.), see the [MCP Server README](repeated_calls/mcp_server/README.md) .


## Prerequisits for MCP Servers

1.  Update the env file in the project root with the PostgeSQL information and the MCP Endpoints:

    ```
    # PostgreSQL
    PGHOST=<postgres-host>
    PGUSER=<postgres-user>
    PGPASSWORD=<postgres-password>
    PGDATABASE=<postgres-db>
    PGPORT= 5432 

    # MCP server endpoints 
    CUSTOMER_MCP_URL= "https://customer-mcp.<region>azurecontainerapps.io/sse"
    OPERATIONS_MCP_URL= "https://operations-mcp.<region>.azurecontainerapps.io/sse" 
    ```

Note: If you dont have the MCP Servers deployed you can run them localy and modify the urls accordingly. If you are using ACA you will need to deploy the mcp servers before setting up the urls. For instructions on how to do that see the ##MCP Data Service Section above.

## Azure Monitor / Traces
Add an Application Insights instance to your AI Foundry project.

Add this to your .env file

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING="<your connection string>"
```

## Running the orchestrator

```bash
poetry install
```
To run the orchestrator in listener mode (will process every incoming message)

```bash
poetry run python -m repeated_calls.orchestrator.main --loglevel INFO --mode listener
```

You can send a test message with this tool
```bash
poetry run python -m repeated_calls.tools.send_test_message
```

To run the orchestrator once (default if --mode is omitted)

```bash
poetry run python -m repeated_calls.orchestrator.main --loglevel INFO --mode once
```