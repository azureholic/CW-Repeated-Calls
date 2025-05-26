"""Pre-built Semantic Kernel agent creating an offer recommendation."""

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.agents import AzureAIAgent,AzureAIAgentSettings, AzureAIAgentThread
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)

from repeated_calls.orchestrator.entities.structured_output import OfferResult


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

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.endpoint,
            deployment_name=ai_agent_settings.model_deployment_name,
        ) as client,
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
        )

        # 3. Create the copy writer agent on the Azure AI agent service
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Reviewer",
            instructions=reviewer_instructions,
        )

        # 4. Create a Semantic Kernel agent for the copy writer Azure AI agent
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
        )

        thread = AzureAIAgentThread(client=client, thread_id=thread_id)
        # 5. Place the agents in a group chat with a custom termination strategy
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        try:
            # 6. Add the task as a message to the group chat
            await chat.add_chat_message(message=user_prompt)
            
            # 7. Invoke the chat
            async for content in chat.invoke(thread=thread):
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
        finally:
            # 8. Cleanup: Delete the agents
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)

        # 9. Return the final response content
        chat.get_chat_messages()
        response = chat.get_chat_messages()[-1]
        return response.content


# def get_agent(kernel: Kernel, draft_instructions: str, reviewer_instructions: str) -> AgentGroupChat:
#     """Agent collaboration chat for interactively drafting and reviewing an offer."""
#     drafter = ChatCompletionAgent(
#         name="Drafter",
#         instructions=draft_instructions,
#         kernel=kernel,
#         arguments=KernelArguments(
#             settings=AzureChatPromptExecutionSettings(
#                 function_choice_behavior=FunctionChoiceBehavior.Auto(
#                     auto_invoke=True,
#                     filters={"included_plugins": ["CustomerDataPlugin", "McpApiKeyPlugin"]},
#                 ),
#                 temperature=0.0,
#                 seed=1337,
#             )
#         ),
#     )

#     reviewer = ChatCompletionAgent(
#         name="Reviewer",
#         instructions=reviewer_instructions,
#         kernel=kernel,
#         arguments=KernelArguments(
#             settings=AzureChatPromptExecutionSettings(
#                 function_choice_behavior=FunctionChoiceBehavior.Auto(
#                     auto_invoke=True,
#                     filters={"included_plugins": ["CustomerDataPlugin", "McpApiKeyPlugin"]},
#                 ),
#                 temperature=0.0,
#                 seed=1337,
#             )
#         ),
#     )

#     return AgentGroupChat(
#         agents=[drafter, reviewer],
#         termination_strategy=ApprovalTerminationStrategy(agents=[reviewer], maximum_iterations=4),
#     )
