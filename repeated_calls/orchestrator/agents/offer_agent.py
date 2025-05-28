"""Pre-built Semantic Kernel agent creating an offer recommendation."""

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents import AzureAIAgent,AzureAIAgentSettings, AzureAIAgentThread
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from repeated_calls.orchestrator.plugins.mcp_plugins import McpApiKeyPlugin
from semantic_kernel.connectors.mcp import MCPSsePlugin
from repeated_calls.orchestrator.entities.structured_output import OfferResult
from settings import McpApiSettings
from repeated_calls.utils.loggers import Logger

logger = Logger()


# TODO: Change this agent to only create an offer and move the review/draft groupchat logic to a different agent
# in draft_review_agent.py


class ApprovalTerminationStrategy(TerminationStrategy):
    """Termination strategy for the agent group chat."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate based on the last message in the chat history."""
        return "approved" in history[-1].content.lower()

async def get_agent_response(draft_instructions: str, reviewer_instructions: str, user_prompt:str, thread_id:str) -> str:
    """Agent for creating an offer recommendation."""
    # Define temperature and which functions the agent can use
    ai_agent_settings = AzureAIAgentSettings()
    mcp_settings = McpApiSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.endpoint,
            deployment_name=ai_agent_settings.model_deployment_name,
        ) as client,
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
        reviewer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Drafter",
            instructions=draft_instructions,
            
        )

        # 2. Create a Semantic Kernel agent for the reviewer Azure AI agent
        agent_reviewer = AzureAIAgent(
            client=client,
            definition=reviewer_agent_definition,
             plugins=[
                customer_plugin,
                operations_plugin,
                McpApiKeyPlugin()                
            ]
        )

        # 3. Create the copy writer agent on the Azure AI agent service
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Reviewer",
            instructions=reviewer_instructions,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="offer",
                    description="offer information.",
                    schema=OfferResult.model_json_schema()
                )
            )
        )

        # 4. Create a Semantic Kernel agent for the copy writer Azure AI agent
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
            plugins=[
                customer_plugin,
                operations_plugin,
                McpApiKeyPlugin()           
            ]
        )

        # 5. Place the agents in a group chat with a custom termination strategy
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=5),
        )
        
        chat_messages = []
        try:
            # 6. Add the task as a message to the group chat
            await chat.add_chat_message(message=user_prompt)
            
            # 7. Invoke the chat and capture messages
            async for content in chat.invoke():
                logger.info(f"# {content.role} - {content.name or '*'}: '{content.content}'")
                chat_messages.append(content)
        finally:
            # 8. Cleanup: Delete the agents
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)
            
            # Get the last message as the response
            if chat_messages:
                for message in chat_messages:
                    await AgentThreadActions.create_message(client, thread_id, message)
                formatter_messages = [msg for msg in chat_messages if msg.name == "Reviewer"]
                if formatter_messages:
                    response = formatter_messages[-1]
            await chat.reset()

        # 9. Return the final response content
        if chat_messages:
            return response
        else:
            return "No response generated"
