"""Pre-built Semantic Kernel agent for determining a product issue cause."""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments

from repeated_calls.orchestrator.entities.structured_output import CauseResult


def get_agent(kernel: Kernel, instructions: str) -> ChatCompletionAgent:
    """Agent for determining the cause of a product issue."""
    # Define temperature and which functions the agent can use
    settings = AzureChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(
            auto_invoke=True,
            filters={"included_plugins": ["CustomerDataPlugin", "OperationsDataPlugin"]},
        ),
        temperature=0.0,
        seed=1337,
        response_format=CauseResult,
    )

    # Create and configure the agent
    agent = ChatCompletionAgent(
        instructions=instructions,
        kernel=kernel,
        arguments=KernelArguments(settings=settings),
        plugins=None,
    )

    return agent
