# Semantic Kernel Process Framework Example

This is a Python implementation of the dotnet-samples example using the Semantic Kernel process framework. The project demonstrates how to:

1. Create process steps
2. Create a process builder to define the workflow
3. Create and use entity objects
4. Create and use kernel functions
5. Load data from CSV files

## Setup

### Prerequisites
- Python 3.9 or later
- Azure OpenAI resource (or another OpenAI compatible API)

### Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the `.env.example` file with your Azure OpenAI configuration:
   ```
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_COMPLETION_MODEL=gpt-35-turbo
   ```

## Running the Example

```bash
python main.py
```

## Troubleshooting

If you encounter import errors, make sure:
1. You've installed all required packages from `requirements.txt`
2. You're using compatible versions of the Semantic Kernel package
3. The virtual environment is activated

## Project Structure

- `entities/` - Contains domain models and data classes
- `steps/` - Contains process steps for the workflow
- `utils/` - Contains utility functions for data retrieval
- `main.py` - Main entry point that sets up the process 

## How it Works

The example demonstrates a process for handling customer calls, determining if they are repeated calls about the same issue, and identifying the cause of the issue if applicable.

The process flow is:
1. Start with customer message
2. Get customer context and history
3. Determine if this is a repeated call
4. If it's a repeated call, determine the cause
5. Exit the process
