"""DetermineRepeatedCaller step for the process framework."""
import json

from entities.structured_output import RepeatedCallResult
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext


class DetermineRepeatedCallerStep(KernelProcessStep):
    """Step to determine if a call is a repeated call about the same issue."""

    def __init__(self):
        super().__init__()
        self._system_prompt = (
            "Your job is to provide the context for a customer. "
            "You will be provided with a customer ID and you must return the customer object, "
            "the call event object, and the historic call event object. "
            "Determine if the current events are considered a repeateable event."
        )

    @kernel_function
    async def repeated_call(
        self, context: KernelProcessStepContext, kernel: Kernel, callstate
    ) -> None:
        """Process function to determine if a call is a repeated call.

        Args:
            context: The process step context
            kernel: The semantic kernel instance
            callstate: The current call state with customer information
        """

        # Build the user message with detailed context
        user_message = []

        # Add customer information
        if hasattr(callstate, "customer") and callstate.customer:
            user_message.append("## Customer Information")
            user_message.append(f"ID: {callstate.customer.id}")
            user_message.append(f"Name: {callstate.customer.name}")
            user_message.append(f"Customer Lifetime Value: {callstate.customer.clv}")
            user_message.append(
                f"Customer Since: {callstate.customer.relation_start_date.strftime('%Y-%m-%d')}"
            )
            user_message.append("")

        # Add current call information
        if hasattr(callstate, "call_event") and callstate.call_event:
            user_message.append("## Current Call Details")
            user_message.append(f"Call ID: {callstate.call_event.id}")
            user_message.append(f"Call Description: {callstate.call_event.sdc}")
            user_message.append(
                f"Timestamp: {callstate.call_event.time_stamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            user_message.append("")

        # Add call history in reverse chronological order (most recent first)
        if callstate.call_history and len(callstate.call_history) > 0:
            user_message.append("## Previous Call History")

            # Sort history by start time in descending order
            sorted_history = sorted(
                callstate.call_history, key=lambda h: h.start_time, reverse=True
            )

            for call in sorted_history:
                duration = call.end_time - call.start_time
                duration_minutes = duration.total_seconds() / 60

                user_message.append(f"### Call on {call.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                user_message.append(f"Description: {call.sdc}")
                user_message.append(f"Summary: {call.call_summary}")
                user_message.append(f"Duration: {duration_minutes:.1f} minutes")
                user_message.append(f"Start: {call.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                user_message.append(f"End: {call.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

                # If there's a current call, calculate time between this historic call and the
                # current one
                if callstate.call_event:
                    time_since_call = callstate.call_event.time_stamp - call.end_time
                    hours_since_call = time_since_call.total_seconds() / 3600
                    user_message.append(f"Time since this call: {hours_since_call:.1f} hours")

                user_message.append("")

        # Add specific question for the model
        user_message.append(
            "Based on this information, is the current call a repeated call about the same issue? "
            "Please analyze the timing between calls, similarity of issues discussed, and provide "
            "your reasoning."
        )

        # Create the chat completion
        chat_service, settings = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(self._system_prompt)
        chat_history.add_user_message("\n".join(user_message))

        execution_settings = AzureChatPromptExecutionSettings(response_format=RepeatedCallResult)

        response = await chat_service.get_chat_message_content(
            chat_history=chat_history, settings=execution_settings
        )

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
