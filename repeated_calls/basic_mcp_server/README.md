# Basic MCP Server

This folder contains the **Repeated Calls MCP Data Service**—a a FastMCP-based microservice (FastMCP is built on FastAPI) for handling customer, product, subscription, and call event data for the Repeated Calls project.

---

## Features

- **Async PostgreSQL** connection pooling
- **FastMCP** API for customer, product, subscription, call event, software update, and discount data
- Pydantic models for data validation and serialization
- Run the server directly with Python
- Ready for containerization with Docker

---

## Folder Structure

```
basic_mcp_server/
├── mcp_server.py         # Main server application
├── test_server.py        # Test client for MCP server
├── models.py             # Pydantic data models
├── dao/                  # Data access objects
├── db.py                 # Database connection helpers
├── settings.py           # Configuration
└── ...
```

---

## Running Locally

1. **Install dependencies** (from project root):
    ```bash
    poetry install
    ```

2. **Set up environment variables**  
   Define the environment variables `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, and optionally `PGPORT`, either as environment variables or in a `.env` file in project root.

3. **Run the server:**
    ```bash
    python repeated_calls/basic_mcp_server/mcp_server.py --host 0.0.0.0 --port 8000
    ```

---

## Dockerization

To build and run the MCP server with Docker:

1. Create a `Dockerfile-mcp-server` in project root folder.
2. Build the Docker image from project root folder:
    ```bash
    docker build -f Dockerfile-mcp-server -t mcp-server:latest .
    ```
3. Run the container:
    ```bash
    docker run -p 8000:8000 --env-file .env mcp-server:latest
    ```

---

## Testing

You can use `test_server.py` to run sanity checks against your running MCP server:

```bash
python repeated_calls/basic_mcp_server/test_server.py --host localhost:8000 --customer 7 --product 101
```

---
