"""
Customer data agent for retrieving customer context information.
"""
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function,KernelArguments
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from repeated_calls.orchestrator.entities.structured_output import RepeatedCallResult
from repeated_calls.orchestrator.plugins.csv.customer import CustomerDataPlugin


"""Agent responsible for providing customer context information."""
def get_agent(kernel: Kernel, instructions: str) -> ChatCompletionAgent:
    """
    Create a chat completion agent for retrieving customer data.
    
    Args:
        kernel: The kernel instance to use for the agent
        instructions: The instructions for the agent
        customer_id: The ID of the customer to retrieve data for
        
    Returns:
        A configured chat completion agent
    """
    # Clone kernel instance to allow for agent-specific plugin definition
    agent_kernel = kernel.clone()

    # Create and configure the agent
    agent = ChatCompletionAgent(
        instructions=instructions,
        kernel=agent_kernel,
        arguments=KernelArguments(
        settings=AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(
                auto_invoke=True,
                filters={"included_plugins": ["CustomerDataPlugin"]}
            ),
            response_format=RepeatedCallResult,
            temperature=0.0,
            seed=1337,
        )
    )
    )
    
    return agent