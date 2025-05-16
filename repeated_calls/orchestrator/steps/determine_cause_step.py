"""DetermineCause step for the process framework."""
import json

from entities.database import SoftwareUpdate, Subscription
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import CauseResult
from repeated_calls.prompt_engineering.prompts import CausePrompt
from repeated_calls.utils.loggers import Logger

logger = Logger(__name__)


class DetermineCauseStep(KernelProcessStep):
    """
    Step to determine the cause of a product issue.

    Uses the enhanced database objects with static data loading.
    """

    def __init__(self):
        """Initialise the DetermineCauseStep."""
        super().__init__()

    @kernel_function
    async def determine_cause(self, context: KernelProcessStepContext, kernel: Kernel, state: State) -> None:
        """
        Process function to determine the cause of an issue.

        Args:
            context: The process step context
            kernel: The semantic kernel instance
            result: The repeated call analysis result
        """  # Get data using the enhanced database objects
        software_updates = SoftwareUpdate.get_all()

        # Get customer subscriptions
        customer_products = Subscription.find_by_customer_id(state.customer_id)

        # Get relevant software updates for the customer's products
        customer_relevant_updates = []
        for customer_product in customer_products:
            # Find software updates for the customer's products
            product_software_updates = [s for s in software_updates if s.product_id == customer_product.product_id]
            customer_relevant_updates.extend(product_software_updates)

        # Construct prompt
        prompt = CausePrompt(state.repeated_call_result, customer_products, customer_relevant_updates)

        # Create the chat completion
        chat_service, _ = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(prompt.get_system_prompt())
        chat_history.add_user_message(prompt.get_user_prompt())

        execution_settings = AzureChatPromptExecutionSettings(response_format=CauseResult)

        # Get model response
        response = await chat_service.get_chat_message_content(chat_history=chat_history, settings=execution_settings)

        print("--- DetermineCauseStep --- AI response ---:", response.content, sep="\n")

        try:
            # Parse the JSON response
            formatted_response = json.loads(response.content)

            # Convert to CauseResult object
            result = CauseResult(
                customer_id=state.customer_id,
                product_id=formatted_response.get("product_id", 0),
                analysis=formatted_response.get("analysis", ""),
                conclusion=formatted_response.get("conclusion", ""),
                is_operations_cause=formatted_response.get("is_operations_cause", False),
            )
            logger.info("Parsed CauseResult: %s", result)

            # Update the state with the result
            state.update(result)

            # Emit appropriate event based on result
            if result.is_operations_cause:
                await context.emit_event("CauseDetermined", data=state)
            else:
                await context.emit_event("NotCauseDetermined")

        except json.JSONDecodeError:
            print("Error parsing AI response as JSON")
            await context.emit_event("NotCauseDetermined")
