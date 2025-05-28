"""Pre-built Semantic Kernel agent for determining a product issue cause."""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.agents import AzureAIAgent,AzureAIAgentSettings, AzureAIAgentThread
from repeated_calls.orchestrator.entities.structured_output import CauseResult
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from semantic_kernel.connectors.mcp import MCPSsePlugin
from settings import McpApiSettings
from repeated_calls.orchestrator.plugins.mcp_plugins import McpApiKeyPlugin

async def get_agent_response(instructions: str, userprompt:str, thread_id:str) -> str:
    """Agent for determining if the call is repeated or not."""
    # Define temperature and which functions the agent can use
    ai_agent_settings = AzureAIAgentSettings()
    mcp_settings = McpApiSettings()
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds, 
                                    conn_str=ai_agent_settings.endpoint, 
                                    deployment_name=ai_agent_settings.model_deployment_name) as client,
        MCPSsePlugin(
            name="CustomerDataPlugin",
            description="Customer domain data and product related data",
            url=mcp_settings.customer_url
        ) as customer_plugin,
        MCPSsePlugin(
            name="OperationsDataPlugin",
            description="Operations data",
            url=mcp_settings.operations_url
        ) as operations_plugin
    ):
        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="CauseAgent",
            instructions=instructions,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="cause",
                    description="Extract cause information.",
                    schema=CauseResult.model_json_schema(),
                )
            )
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[McpApiKeyPlugin(), customer_plugin, operations_plugin]
        )

        thread = AzureAIAgentThread(client=client, thread_id=thread_id)
        response = await agent.get_response(
            messages=userprompt,
            thread=thread
        )

        await client.agents.delete_agent(agent.id)

    return response.content