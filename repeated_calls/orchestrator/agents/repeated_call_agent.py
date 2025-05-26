"""Pre-built Semantic Kernel agent for determining a product issue cause."""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.agents import AzureAIAgent,AzureAIAgentSettings, AzureAIAgentThread
from repeated_calls.orchestrator.entities.structured_output import RepeatedCallResult
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)

# def get_agent(kernel: Kernel, instructions: str) -> ChatCompletionAgent:
#     """Agent for determining if the call is repeated or not."""
#     # Define temperature and which functions the agent can use
#     settings = AzureChatPromptExecutionSettings(
#         function_choice_behavior=FunctionChoiceBehavior.Auto(
#             auto_invoke=True,
#             filters={"included_plugins": ["CustomerDataPlugin"]},
#         ),
#         temperature=0.0,
#         seed=1337,
#         max_tokens=3000,
#         response_format=RepeatedCallResult,
#     )

#     # Create and configure the agent
#     agent = ChatCompletionAgent(
#         name="RepeatedCallAgent",
#         instructions=instructions,
#         kernel=kernel,
#         arguments=KernelArguments(settings=settings),
#         plugins=None,
#     )

#     return agent
async def get_agent_response(instructions: str, userprompt:str, thread: AzureAIAgentThread) -> str:
    """Agent for determining if the call is repeated or not."""
    # Define temperature and which functions the agent can use
    ai_agent_settings = AzureAIAgentSettings()
    
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds, 
                                    conn_str=ai_agent_settings.endpoint, 
                                    deployment_name=ai_agent_settings.model_deployment_name) as client,
    ):
        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="RepeatedCallAgent",
            instructions=instructions,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="repeated_call",
                    description="Extract repeated call information.",
                    schema=RepeatedCallResult.model_json_schema(),
                )
            )
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        response = await agent.get_response(
            messages=userprompt,
            thread=thread
        )

    return response.content
