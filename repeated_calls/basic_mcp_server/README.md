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
├── customer/
│   ├── customer_mcp_server.py      # Customer MCP server entrypoint
│   └── test_customer_mcp_server.py # Customer MCP test client
├── operations/
│   ├── operations_mcp_server.py    # Operations MCP server entrypoint
│   └── test_operations_mcp_server.py # Operations MCP test client
├── common/                         # Shared components
│   ├── models.py                   # Shared Pydantic data models
│   ├── db.py                       # Database connection helpers
│   └── settings.py                 # Configuration
├── Dockerfile-customer-mcp-server  # Dockerfile for the Customer MCP Server
└── Dockerfile-operations-mcp-server # Dockerfile for the Operations MCP Server
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

3. **Run the servers:** (from project root):
    *   **Customer MCP Server** (e.g., on port 8000):
        ```bash
        python repeated_calls/basic_mcp_server/customer/customer_mcp_server.py --host 0.0.0.0 --port 8000
        ```

    *   **Operations MCP Server** (e.g., on port 8001):
        ```bash
        python repeated_calls/basic_mcp_server/operations/operations_mcp_server.py --host 0.0.0.0 --port 8001
        ```


---

## Dockerization
To build and run the MCP servers with Docker:

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

You can use the provided test clients to run sanity checks against your running MCP servers:

*   **Customer MCP Server** :
    ```bash
    python repeated_calls/basic_mcp_server/customer/test_customer_mcp_server.py --host localhost:8000 --customer 7 --product 101
    ```

*   **Operations MCP Server** :
    ```bash
    python repeated_calls/basic_mcp_server/operations/test_operations_mcp_server.py --host localhost:8001 --product 101
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
export MCPAPIKEY="[REPLACE_WITH_MCP_API_KEY]"
export KEYVAULT_NAME="[REPLACE_WITH_KEYVAULT_NAME]"
```

> **Note:**
> - Replace all `[REPLACE_WITH_...]` placeholders above with your actual values.
> - The value `${USER_ASSIGNED_IDENTITY}` refers to an existing user-assigned managed identity in your Azure environment.
> - This identity **must already exist** and **must have "AcrPull" role assignment** on your Azure Container Registry (`${ACR_NAME}`).
> - Make sure all referenced Azure resources (`${ACR_NAME}`, `${RESOURCE_GROUP}`, `${ENVIRONMENT_ID}`, `${USER_ASSIGNED_IDENTITY}`) already exist.
> - You must be logged in to Azure CLI and have the necessary permissions.

### 2. Login to Azure 
```bash
az login
az acr login --name ${ACR_NAME}
```

### 3. Add secrets to KeyVault
```bash
az keyvault secret set --vault-name ${KEYVAULT_NAME} --name PGPASSWORD --value "<your-password>"
az keyvault secret set --vault-name ${KEYVAULT_NAME} --name MCP-CUSTOMERS-API-KEY --value "<your-api-key>"
az keyvault secret set --vault-name ${KEYVAULT_NAME} --name MCP-OPERATIONS-API-KEY --value "<your-api-key>"
```

### 3. Grant access to the managed identity
```bash
az keyvault set-policy --name ${KEYVAULT_NAME} --object-id <USER_ASSIGNED_IDENTITY_OBJECT_ID> --secret-permissions get
```

### 5. Deploy Customer MCP Server to Azure Container App

```bash
# Set variables specific to the Customer MCP App
export CUSTOMER_CONTAINERAPP_NAME="customer-mcp-app" # Or your desired app name
export CUSTOMER_IMAGE_NAME="customer-mcp-server"    # As defined in Dockerization

# Create the Customer MCP Container App
az containerapp create \
  --name ${CUSTOMER_CONTAINERAPP_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --environment ${ENVIRONMENT_ID} \
  --image ${ACR_LOGIN_SERVER}/${CUSTOMER_IMAGE_NAME}:${IMAGE_TAG} \
  --cpu 1 --memory 2.0Gi \
  --ingress external --target-port 8000 \
  --registry-server ${ACR_LOGIN_SERVER} \
  --secrets pg-admin-password=keyvaultref:<KEYVAULT-PGPASSWORD-SECRET-URL>,identityref:<USERASSIGNED-MANAGED-DENTITY-URL> mcp-api-key=keyvaultref:<KEYVAULT-MCP-CUSTOMERS-API-KEY-SECRET-URL>,identityref:<USERASSIGNED-MANAGED-DENTITY-URL> \
  --env-vars PGHOST="${PGHOST}" PGUSER="${PGUSER}" PGPASSWORD=secretref:pg-admin-password PGDATABASE="${PGDATABASE}" PGPORT="${PGPORT}" MCPAPIKEY=secretref:mcp-api-key \
  --user-assigned ${USER_ASSIGNED_IDENTITY}
```
### 6. Deploy Operations MCP Server to Azure Container App

```bash
# Set variables specific to the Operations MCP App
export OPERATIONS_CONTAINERAPP_NAME="operations-mcp-app" # Or your desired app name
export OPERATIONS_IMAGE_NAME="operations-mcp-server"    # As defined in Dockerization

# Create the Operations MCP Container App
az containerapp create \
  --name ${OPERATIONS_CONTAINERAPP_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --environment ${ENVIRONMENT_ID} \
  --image ${ACR_LOGIN_SERVER}/${OPERATIONS_IMAGE_NAME}:${IMAGE_TAG} \
  --cpu 1 --memory 2.0Gi \
  --ingress external --target-port 8000 \
  --registry-server ${ACR_LOGIN_SERVER} \
  --secrets pg-admin-password=keyvaultref:<KEYVAULT-PGPASSWORD-SECRET-URL>,identityref:<USERASSIGNED-MANAGED-DENTITY-URL> mcp-api-key=keyvaultref:<KEYVAULT-MCP-CUSTOMERS-API-KEY-SECRET-URL>,identityref:<USERASSIGNED-MANAGED-DENTITY-URL> \
  --env-vars PGHOST="${PGHOST}" PGUSER="${PGUSER}" PGPASSWORD=secretref:pg-admin-password PGDATABASE="${PGDATABASE}" PGPORT="${PGPORT}" MCPAPIKEY=secretref:mcp-api-key \
  --user-assigned ${USER_ASSIGNED_IDENTITY}
```

---
