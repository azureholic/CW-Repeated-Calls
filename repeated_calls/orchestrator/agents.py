"""Library of prebuilt Semantic Kernel agents."""

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments


def cause_agent(kernel: Kernel, instructions: str) -> ChatCompletionAgent:
    """Agent for determining the cause of a product issue."""
    # Define temperature and which functions the agent can use
    settings = AzureChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(
            auto_invoke=True,
            filters={"included_plugins": ["CustomerDataPlugin", "OperationsDataPlugin"]},
        ),
        temperature=0.0,
    )

    # Create and configure the agent
    agent = ChatCompletionAgent(
        instructions=instructions,
        kernel=kernel,
        arguments=KernelArguments(settings=settings),
        plugins=None,
    )

    return agent


class ApprovalTerminationStrategy(TerminationStrategy):
    async def should_agent_terminate(self, agent, history):
        return "approved" in history[-1].content.lower()


def offer_agent(kernel: Kernel, draft_instructions: str, reviewer_instructions: str) -> AgentGroupChat:
    """Agent collaboration for interactively drafting and reviewing an offer."""
    drafter = ChatCompletionAgent(
        name="Drafter",
        instructions=draft_instructions,
        kernel=kernel,
        arguments=KernelArguments(
            settings=AzureChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    auto_invoke=True,
                    filters={"included_plugins": ["CustomerDataPlugin"]},
                ),
                temperature=0.0,
            )
        ),
    )

    reviewer = ChatCompletionAgent(
        name="Reviewer",
        instructions=reviewer_instructions,
        kernel=kernel,
        arguments=KernelArguments(
            settings=AzureChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    auto_invoke=True,
                    filters={"included_plugins": ["CustomerDataPlugin"]},
                ),
                temperature=0.0,
            )
        ),
    )

    return AgentGroupChat(
        agents=[drafter, reviewer],
        termination_strategy=ApprovalTerminationStrategy(agents=[reviewer], maximum_iterations=4),
    )
