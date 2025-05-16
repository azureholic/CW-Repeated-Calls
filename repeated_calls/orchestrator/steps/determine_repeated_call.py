"""GetCustomerData step for the process framework."""

import json

from entities.states import State
from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.database.schemas import CallEvent, Customer, HistoricCallEvent
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt
from repeated_calls.utils.loggers import Logger

logger = Logger()


class RepeatedCallClassification(BaseModel):
    """Classification of a call event."""

    is_repeated_call: bool = Field(..., description="Indicates if the call is a repeated call.")
    explanation: str = Field(..., description="Explanation of the classification.")


class DetermineRepeatedCallStep(KernelProcessStep):
    """Step to retrieve customer data and context for process execution.

    Uses the enhanced database objects with static data loading.
    """

    @kernel_function
    async def repeated_call(
        self,
        call_event: CallEvent,
        context: KernelProcessStepContext,
        kernel: Kernel,
    ) -> None:
        """Process function to retrieve customer data and call events using the enhanced database objects."""
        # Check if incoming_message is already the correct type
        # this code below is to 'fix' semantic_kernel.exceptions.kernel_exceptions.KernelException:
        # The function get_call_event on step GetCustomerDataStep has more than one parameter, so a
        # parameter name must be provided.

        if not isinstance(call_event, CallEvent):
            # If it's a dict or similar with attributes we need, try to convert it
            try:
                call_event = CallEvent(**incoming_message)
            except Exception as e:
                raise TypeError(f"Cannot convert input to IncomingMessage: {str(e)}")

        # Get customer data and historic calls manually
        func = kernel.get_function("CustomerDataPlugin", "get_customer_historic_call_events")
        events = await func.invoke(kernel, KernelArguments(customer_id=call_event.customer_id))
        events = json.loads(events.value)
        events = [HistoricCallEvent(**event) for event in events]

        func = kernel.get_function("CustomerDataPlugin", "get_customer_details")
        customer = await func.invoke(kernel, KernelArguments(customer_id=call_event.customer_id))
        customer = json.loads(customer.value)
        customer = Customer(**customer)

        # Classify whether the call is a repeated call with an LLM
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
        chat_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallClassification, temperature=0.0)

        # Prepare the chat interaction
        chat_history = ChatHistory()
        prompts = RepeatCallerPrompt(customer=customer, call_event=call_event, historic_calls=events)
        chat_history.add_system_message(prompts.get_system_prompt())
        chat_history.add_user_message(prompts.get_user_prompt())

        res = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=chat_settings,
        )
        chat_history.add_assistant_message(res.content)
        logger.debug(f"Repeated call response: {res.content}")

        state = State(**json.loads(res.content))

        # Emit event to continue process flow
        if state.is_repeated_call:
            await context.emit_event("IsRepeatedCall", data=state)
        else:
            await context.emit_event("IsNotRepeatedCall", data=state)
