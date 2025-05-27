# Load environment variables from .env file
$envPath = Join-Path $PSScriptRoot "..\\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Remove surrounding quotes if present
            if ($value -match '^"(.*)"$') {
                $value = $matches[1]
            }
            # Set as environment variable
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
    Write-Host "Loaded environment variables from .env file"
} else {
    Write-Warning ".env file not found at $envPath"
}

# Create a proper JSON string for servers configuration in PowerShell
$serverJson = @{
    "Servers" = @{
        "1" = @{
            "Name" = "Minimally Defined Server"
            "Group" = "Server Group 1"
            "Host" = "$env:POSTGRES_HOST"
            "Port" = $env:POSTGRES_PORT
            "Username" = "$env:POSTGRES_USER"
            "MaintenanceDB" = "postgres"
            "ConnectionParameters" = @{
                "sslmode" = "prefer"
                "connect_timeout" = 10
            }
        }
    }
} | ConvertTo-Json -Depth 3 -Compress

# Check the env vars are properly loaded
Write-Host "Connecting to PostgreSQL at $($env:POSTGRES_HOST):$($env:POSTGRES_PORT) with user $($env:POSTGRES_USER)"

# Run pgAdmin container with PostgreSQL connection details from .env
docker run -d `
    --name pgadmin4-cw-repeated-calls `
    -p 5050:80 `
    -e "PGADMIN_DEFAULT_EMAIL=user@domain.com" `
    -e "PGADMIN_DEFAULT_PASSWORD=SuperSecret" `
    -e "PGADMIN_SERVER_JSON=$serverJson" `
    dpage/pgadmin4:latest

Write-Host "pgAdmin4 is now running on http://localhost:5050"
Write-Host "Login with user@domain.com and SuperSecret"
Write-Host "PostgreSQL server is configured automatically with your .env settings"