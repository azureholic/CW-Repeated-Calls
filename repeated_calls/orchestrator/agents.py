"""Library of prebuilt Semantic Kernel agents."""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments


def cause_agent(kernel: Kernel) -> ChatCompletionAgent:
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
        instructions="Your job is to determine the cause of a product issue.",
        kernel=kernel,
        arguments=KernelArguments(settings=settings),
        plugins=None,
    )

    return agent
