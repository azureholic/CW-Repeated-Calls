"""DetermineRepeatedCaller step for the process framework."""
import json
from typing import Annotated

from entities.structured_output import RepeatedCallResult
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.agents import ChatCompletionAgent,ChatHistoryAgentThread
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt

from repeated_calls.utils.loggers import Logger
from repeated_calls.orchestrator.agents.customer_data_agent import CustomerDataAgent

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
        kernel: Annotated[Kernel | None, "The kernel", {"include_in_function_choices": False}],
        incoming_message,
    ) -> None:
        """
        Determine if the given call is a repeated issue based on customer state.

        Args:
            context: Kernel process context.
            kernel: Semantic kernel instance.
            incoming_message: Incoming message containing customer data.
        """
        logger.info("Running DetermineRepeatedCallerStep for customer call.")

        try:
            # Create a customer data agent
            logger.debug("Creating customer data agent...")

            agent = CustomerDataAgent().create_agent(kernel, "CustomerDataAgent", incoming_message.customer_id)
            response = await agent.get_response(messages="CustomerId is: " + str(incoming_message.customer_id))

            logger.debug("Customer data agent response: %s", response)

            system_prompt = """
                Based on the information provided, is the current call a repeated call about the same issue? 
                Please analyze the timing between calls, similarity of issues discussed, and provide your reasoning.
                """

            chat_service = kernel.select_ai_service(type=ChatCompletionClientBase)
            assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

            # Create a chat history object
            chat_history = ChatHistory()
            chat_history.add_system_message(system_prompt)
            chat_history.add_user_message(response)

            execution_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallResult)

            result = await chat_service.get_chat_message_content(
                chat_history=chat_history, settings=execution_settings
            )

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

