"""DetermineRepeatedCaller step for the process framework."""
import json

from entities.structured_output import RepeatedCallResult
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.prompt_engineering.repeat_caller_prompt import RepeatCallerPrompt


class DetermineRepeatedCallerStep(KernelProcessStep):
    """Step to determine if a call is a repeated call about the same issue."""

    def __init__(self):
        """Initialize the DetermineRepeatedCallerStep."""
        super().__init__()

    @kernel_function
    async def repeated_call(self, context: KernelProcessStepContext, kernel: Kernel, callstate) -> None:
        """
        Process function to determine if a call is a repeated call.

        Args:
            context: The process step context
            kernel: The semantic kernel instance
            callstate: The current call state with customer information
        """
        prompt = RepeatCallerPrompt().from_callstate(callstate)

        # Create the chat completion
        chat_service, _ = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(prompt.get_system_prompt())
        chat_history.add_user_message(prompt.get_user_prompt())

        execution_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallResult)

        response = await chat_service.get_chat_message_content(chat_history=chat_history, settings=execution_settings)

        try:
            # Parse the JSON response
            formatted_response = json.loads(response.content)

            # Get customer ID safely (default to 0 if not available)
            customer_id = 0
            if callstate.customer and hasattr(callstate.customer, "id"):
                customer_id = callstate.customer.id

            # Convert to RepeatedCallResult object
            result = RepeatedCallResult(
                customer_id=customer_id,
                analysis=formatted_response.get("analysis", ""),
                conclusion=formatted_response.get("conclusion", ""),
                is_repeated_call=formatted_response.get("is_repeated_call", False),
            )

            print(result)

            # Emit appropriate event based on result
            if result.is_repeated_call:
                await context.emit_event("IsRepeatedCall", data=result)
            else:
                await context.emit_event("IsNotRepeatedCall")

        except json.JSONDecodeError:
            print("Error parsing AI response as JSON")
            await context.emit_event("IsNotRepeatedCall")
