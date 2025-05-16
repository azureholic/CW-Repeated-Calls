"""Step for determining the cause of a product issue."""

import json

from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.database.schemas import CallEvent
from repeated_calls.orchestrator.agents import cause_agent
from repeated_calls.utils.loggers import Logger

logger = Logger()


class CauseDetermination(BaseModel):
    """Determination of whether a customer complaint is relevant."""

    is_relevant: bool = Field(..., description="Whether the company is at fault and a fix is needed.")
    explanation: str = Field(..., description="Explanation of the relevancy determination.")


class DetermineCauseStep(KernelProcessStep):
    """Step for determining the cause of a product issue.
    
    Uses a variety of plugins and agents to determine the cause of a product issue.
    """
    
    @kernel_function
    async def cause(
        self,
        call_event: CallEvent,
        context: KernelProcessStepContext,
        kernel: Kernel,
    ) -> None:
        """Process function to determine the cause of a product issue."""
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

        agent = cause_agent(kernel=kernel)

        response = await agent.get_response(
            messages=(
                f"Customer ID: {call_event.customer_id}\n"
                f"Call ID: {call_event.id}\n"
                f"Call Date: {call_event.timestamp}\n"
                f"Call Reason: {call_event.sdc}\n"
            )
        )

        # Classify whether the call is a repeated call with an LLM
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
        chat_settings = AzureChatPromptExecutionSettings(response_format=CauseDetermination, temperature=0.0)

        # Prepare the chat interaction
        chat_history = ChatHistory()
        chat_history.add_user_message(str(response))

        res = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=chat_settings,
        )
        chat_history.add_assistant_message(res.content)
        logger.debug(f"Cause determination response: {res.content}")

        if json.loads(res.content)["is_relevant"]:
            # Send event to next step
            await context.emit_event(
                "IsRelevant",
                data=call_event,
            )
        else:
            # Send event to exit step
            await context.emit_event(
                "IsNotRelevant",
                data=call_event,
            )
