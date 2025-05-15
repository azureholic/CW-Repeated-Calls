"""
Customer data agent for retrieving customer context information.
"""
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import kernel_function,KernelArguments

from repeated_calls.orchestrator.entities.states import RepeatedCallState
from repeated_calls.orchestrator.entities.structured_output import RepeatedCallResult
from repeated_calls.orchestrator.plugins.csv.customer import CustomerDataPlugin


class CustomerDataAgent:
    """Agent responsible for providing customer context information."""
    
    def create_agent(self, kernel: Kernel, agent_name: str, customer_id: int) -> ChatCompletionAgent:
        """
        Create a chat completion agent for retrieving customer data.
        
        Args:
            kernel: The kernel instance to use for the agent
            agent_name: The name of the agent
            customer_id: The ID of the customer to retrieve data for
            
        Returns:
            A configured chat completion agent
        """
        # Clone kernel instance to allow for agent-specific plugin definition
        agent_kernel = kernel.clone()
        
        # Import plugin from type
        # Note: In Python, we would register the plugin using a different approach
        # than the ImportPluginFromType in C#
        agent_kernel.add_plugin(CustomerDataPlugin(data_path='/../../../data'), "CustomerDataPlugin")

        # Create and configure the agent
        agent = ChatCompletionAgent(
            name=agent_name,
            instructions=f"""
            Your job is to provide the context for a given customer. 
            You will be provided with a customer ID and you must return the 
            - get_customer_details
            - get_customer_call_event
            - get_customer_historic_call_events
            
            ## Customer ID: {customer_id}
            """,
            kernel=agent_kernel,
            arguments=KernelArguments(
                execution_settings=AzureChatPromptExecutionSettings(
                    response_format=RepeatedCallState,
                    function_choice_behavior="required",
                    temperature=0,
                )
            )
        )
        
        return agent