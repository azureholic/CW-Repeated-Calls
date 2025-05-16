"""GetCustomerData step for the process framework."""
import json

from entities.database import CallEvent, Customer, HistoricCallEvent
from entities.states import IncomingMessage, RepeatedCallState
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.database.schemas import CallEvent, Customer, HistoricCallEvent


class GetCustomerDataStep(KernelProcessStep):
    """Step to retrieve customer data and context for process execution.

    Uses the enhanced database objects with static data loading.
    """

    def __init__(self):
        """Initialise the GetCustomerDataStep."""
        super().__init__()
        self._state = RepeatedCallState()

    @kernel_function
    async def get_call_event(self, incoming_message, context: KernelProcessStepContext, kernel: Kernel) -> None:
        """Process function to retrieve customer data and call events using the enhanced database objects.

        Args:
            incoming_message: The incoming message with customer ID
            context: The process step context
        """
        # Check if incoming_message is already the correct type
        # this code below is to 'fix' semantic_kernel.exceptions.kernel_exceptions.KernelException:
        # The function get_call_event on step GetCustomerDataStep has more than one parameter, so a
        # parameter name must be provided.

        if not isinstance(incoming_message, IncomingMessage):
            # If it's a dict or similar with attributes we need, try to convert it
            try:
                incoming_message = IncomingMessage(**incoming_message)
            except Exception as e:
                raise TypeError(f"Cannot convert input to IncomingMessage: {str(e)}")

        # Get customer data and historic calls manually
        func = kernel.get_function("CustomerDataPlugin", "get_customer_historic_call_events")
        events = await func.invoke(kernel, KernelArguments(customer_id=incoming_message.customer_id))
        events = json.loads(events.value)
        events = [HistoricCallEvent(**event) for event in events]

        func = kernel.get_function("CustomerDataPlugin", "get_customer_details")
        customer = await func.invoke(kernel, KernelArguments(customer_id=incoming_message.customer_id))
        customer = json.loads(customer.value)
        customer = Customer(**customer)

        current_call = CallEvent(
            id=incoming_message.id,
            customer_id=incoming_message.customer_id,
            sdc=incoming_message.message,
            timestamp=incoming_message.timestamp,
        )

        # Create state object
        repeated_call_state = RepeatedCallState(
            customer=customer,
            call_event=current_call,
            call_history=events,
        )

        # Emit event to continue process flow
        await context.emit_event("FetchingContextDone", data=repeated_call_state)
