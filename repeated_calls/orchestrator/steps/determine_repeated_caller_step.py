"""DetermineRepeatedCaller step for the process framework."""
import json
from typing import Annotated

from entities.structured_output import RepeatedCallResult
from repeated_calls.orchestrator.entities.states import RepeatedCallState
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.agents import ChatCompletionAgent,ChatHistoryAgentThread
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

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
        kernel: Annotated[Kernel | None, "The kernel", {"include_in_function_choices": False}], # this is important to avoid json serializing errors (https://github.com/microsoft/semantic-kernel/issues/12067)
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

        try:            # Create a customer data agent
            logger.debug("Creating customer data agent...")

            agent = CustomerDataAgent().create_agent(kernel, "CustomerDataAgent", incoming_message.customer_id)
            response = await agent.get_response()
            logger.debug("Customer data agent response: %s", response)            
            # Convert response.content to a string before parsing as JSON
            formatted_response = json.loads(str(response.content))

            # Create a RepeatedCallState object
            result = RepeatedCallState()
            result.customer=formatted_response["customer_details"]
            result.call_event=formatted_response["call_event"]
            result.call_history=formatted_response["historic_call_events"]

            logger.debug("Customer data agent response: %s", response)

            # Determine if the call is a repeated call
            repeated_call_result = await self.determine_if_repeated_call(kernel, result)

            # Emit appropriate event
            if repeated_call_result.is_repeated_call:
                logger.info("Call identified as repeat call.")
                await context.emit_event("IsRepeatedCall", data=repeated_call_result)
            else:
                logger.info("Call identified as not repeat call.")
                await context.emit_event("IsNotRepeatedCall")

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", e, exc_info=True)
            await context.emit_event("IsNotRepeatedCall")

        except Exception as e:
            logger.exception("Unexpected error in DetermineRepeatedCallerStep: %s", e)
            raise e

    async def determine_if_repeated_call(
        self, 
        kernel: Kernel,
        call_state: RepeatedCallState
    ) -> RepeatedCallResult:
        """
        Determine if the given call is a repeated call based on state data.
        
        Args:
            kernel: Semantic kernel instance
            call_state: The state containing customer, call event and history information
            
        Returns:
            RepeatedCallResult object with analysis and conclusion
        """
        logger.info("Analyzing call data to determine if it's a repeated call")
        
        system_prompt = """
            Based on the information provided, is the current call a repeated call about the same issue? 
            Please analyze the timing between calls, similarity of issues discussed, and provide your reasoning.
            """

        chat_service = kernel.get_service(type=ChatCompletionClientBase)

        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(system_prompt)
        chat_history.add_user_message(
            f"Customer: {call_state.customer}\n"
            f"CallEvent: {call_state.call_event}\n"
            f"CallHistory: {call_state.call_history}"
        )

        execution_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallResult)

        response = await chat_service.get_chat_message_content(
            chat_history=chat_history, settings=execution_settings
        )

        # Parse the JSON response
        formatted_response = json.loads(str(response.content))

        # Convert to RepeatedCallResult object and return
        return RepeatedCallResult(
            customer_id=call_state.customer.get("id", 0) if call_state.customer else 0,
            analysis=formatted_response.get("analysis", ""),
            conclusion=formatted_response.get("conclusion", ""),
            is_repeated_call=formatted_response.get("is_repeated_call", False),
        )

