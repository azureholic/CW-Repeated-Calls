"""DetermineRepeatedCaller step for the process framework."""
import json

from entities.structured_output import RepeatedCallResult
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.entities.state import State
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt
from repeated_calls.utils.loggers import Logger

logger = Logger(__name__)


class DetermineRepeatedCallerStep(KernelProcessStep):
    """Step to determine if a call is a repeated call about the same issue."""

    def __init__(self) -> None:
        """Initialize the DetermineRepeatedCallerStep."""
        super().__init__()

    @kernel_function
    async def repeated_call(
        self,
        context: KernelProcessStepContext,
        kernel: Kernel,
        state: State,
    ) -> None:
        """
        Determine if the given call is a repeated issue based on customer state.

        Args:
            context: Kernel process context.
            kernel: Semantic kernel instance.
            callstate: Call state containing customer data.
        """
        logger.info("Running DetermineRepeatedCallerStep for customer call.")

        try:
            # Construct the prompt from call state
            prompt = RepeatCallerPrompt(state)
            logger.debug("Constructed RepeatCallerPrompt.")

            # Retrieve a compatible AI chat completion service
            chat_service, _ = kernel.select_ai_service(type=ChatCompletionClientBase)
            if not isinstance(chat_service, ChatCompletionClientBase):
                logger.error("Invalid AI service type.")
                await context.emit_event("IsNotRepeatedCall")
                return

            # Log prompt details #TODO: Remove this later
            system_prompt = prompt.get_system_prompt()
            user_prompt = prompt.get_user_prompt()
            print("--- SYSTEM PROMPT ----:\n %s", system_prompt)
            print("--- USER PROMPT ---:\n %s", user_prompt)

            # Prepare the chat interaction
            chat_history = ChatHistory()
            chat_history.add_system_message(prompt.get_system_prompt())
            chat_history.add_user_message(prompt.get_user_prompt())

            # Set execution settings
            execution_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallResult)

            logger.debug("Sending prompt to AI service...")
            response = await chat_service.get_chat_message_content(
                chat_history=chat_history,
                settings=execution_settings,
            )

            logger.debug("Received AI response: %s", response.content)

            # Attempt to parse the response
            formatted_response = json.loads(response.content)

            # Safely extract customer ID
            customer_id = getattr(state.customer, "id", 0)

            result = RepeatedCallResult(
                customer_id=customer_id,
                analysis=formatted_response.get("analysis", ""),
                conclusion=formatted_response.get("conclusion", ""),
                is_repeated_call=formatted_response.get("is_repeated_call", False),
            )

            logger.info("Parsed RepeatedCallResult: %s", result)

            # Emit appropriate event
            if result.is_repeated_call:
                logger.info("Call identified as repeat call.")
                await context.emit_event("IsRepeatedCall", data=result)
            else:
                logger.info("Call identified as not repeat call.")
                await context.emit_event("IsNotRepeatedCall")

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", e, exc_info=True)
            await context.emit_event("IsNotRepeatedCall")

        except Exception as e:
            logger.exception("Unexpected error in DetermineRepeatedCallerStep: %s", e)
            raise e
