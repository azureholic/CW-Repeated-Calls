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

3. **Run the server:** (from project root):
    ```bash
    python repeated_calls/basic_mcp_server/mcp_server.py --host 0.0.0.0 --port 8000
    ```

---

## Dockerization
To build and run the MCP server with Docker:

1. Set the following variables in your terminal (update values as needed):
    ```bash
    export ACR_NAME="[REPLACE_WITH_ACR_NAME]"
    export ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    export IMAGE_NAME="[REPLACE_WITH_IMAGE_NAME]"
    export IMAGE_TAG="latest"
    ```

    > **Note:** The value of `ACR_NAME` refers to an existing Azure Container Registry (ACR) in Azure environment.
    > Make sure you have access to this ACR before pushing images.

2. Build the Docker image from project root folder:
    ```bash
    docker build -f Dockerfile-mcp-server -t ${IMAGE_NAME}:${IMAGE_TAG} .
    ```
3. Run the container:
    ```bash
    docker run -p 8000:8000 --env-file .env ${IMAGE_NAME}:${IMAGE_TAG}
    ```
4. Tag your image for ACR:
    ```bash
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}
    ```
5. Login to Azure environment
    ```bash
    az login
    ```
6. Login to Azure ACR environment
    ```bash
    az acr login --name ${ACR_NAME}
    ```
7. Push the image to ACR:
    ```bash
    docker push ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}
    ```

---

## Testing

You can use `test_server.py` to run sanity checks against your running MCP server:

```bash
python repeated_calls/basic_mcp_server/test_server.py --host localhost:8000 --customer 7 --product 101
```

---

## Deploying to Azure Container Apps

After pushing your Docker image to Azure Container Registry (ACR), you can deploy it to Azure Container Apps using the Azure CLI.

### 1. Set Deployment Variables

Set the following variables in your terminal (update values as needed):

```bash
export CONTAINERAPP_NAME="[REPLACE_WITH_CONTAINER_APP_NAME]"
export RESOURCE_GROUP="[REPLACE_WITH_RESOURCE_GROUP_NAME]"
export ENVIRONMENT_ID="[REPLACE_WITH_CONTAINER_APP_ENV_RESOURCE_ID]"
export ACR_NAME="[REPLACE_WITH_ACR_NAME]"
export ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
export IMAGE_NAME="[REPLACE_WITH_IMAGE_NAME]"
export IMAGE_TAG="latest"
export PGHOST="[REPLACE_WITH_POSTGRESQL_HOST_NAME]"
export PGUSER="[REPLACE_WITH_POSTGRESQL_ADMIN_NAME]"
export PGPASSWORD="[REPLACE_WITH_POSTGRESQL_ADMIN_PASSWORD]"
export PGDATABASE="default"
export PGPORT="5432"
export USER_ASSIGNED_IDENTITY="[REPLACE_WITH_USER_ASSIGNED_MANAGED_IDENTITY]"
```

> **Note:**
> - Replace all `[REPLACE_WITH_...]` placeholders above with your actual values.
> - The value `${USER_ASSIGNED_IDENTITY}` refers to an existing user-assigned managed identity in your Azure environment.
> - This identity **must already exist** and **must have "AcrPull" role assignment** on your Azure Container Registry (`${ACR_NAME}`).
> - Make sure all referenced Azure resources (`${ACR_NAME}`, `${RESOURCE_GROUP}`, `${ENVIRONMENT_ID}`, `${USER_ASSIGNED_IDENTITY}`) already exist.
> - You must be logged in to Azure CLI and have the necessary permissions.

### 2. Create the Azure Container App

Run the following command to create your container app:

```bash
az login
az acr login --name ${ACR_NAME}
az containerapp create \
  --name ${CONTAINERAPP_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --environment ${ENVIRONMENT_ID} \
  --image ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG} \
  --cpu 1 --memory 2.0Gi \
  --ingress external --target-port 8000 \
  --registry-server ${ACR_LOGIN_SERVER} \
  --env-vars PGHOST="${PGHOST}" PGUSER="${PGUSER}" PGPASSWORD="${PGPASSWORD}" PGDATABASE="${PGDATABASE}" PGPORT="${PGPORT}" \
  --user-assigned ${USER_ASSIGNED_IDENTITY}
```

---
