"""GetCustomerData step for the process framework."""


from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.entities.database import Customer as DeprecatedCustomer
from repeated_calls.orchestrator.entities.database import HistoricCallEvent as DeprecatedHistoricCallEvent
from repeated_calls.orchestrator.entities.state import State


class GetCustomerDataStep(KernelProcessStep):
    """Step to retrieve customer data and context for process execution.

    Uses the enhanced database objects with static data loading.
    """

    @kernel_function
    async def get_call_event(self, state: State, context: KernelProcessStepContext) -> None:
        """Process function to retrieve customer data and call events using the enhanced database objects.

        Args:
            incoming_message: The incoming message with customer ID
            context: The process step context
        """
        # Check if incoming_message is already the correct type
        # this code below is to 'fix' semantic_kernel.exceptions.kernel_exceptions.KernelException:
        # The function get_call_event on step GetCustomerDataStep has more than one parameter, so a
        # parameter name must be provided.
        if not isinstance(state, State):
            raise TypeError("State must be of type State")

        # Find customer's historic call events using the enhanced class method
        customer_historic_call_events = DeprecatedHistoricCallEvent.find_by_customer_id(state.customer_id)

        if not customer_historic_call_events:
            print(f"Warning: No historic call event found for customer ID {state.customer_id}")

        # Find customer using the enhanced class method
        customer = DeprecatedCustomer.find_by_id(state.customer_id)
        if not customer:
            print(f"Warning: No customer found with ID {state.customer_id}")

        # Update state object with customer data and call history
        state.update(customer, customer_historic_call_events)

        # Emit event to continue process flow
        await context.emit_event("FetchingContextDone", data=state)
