"""
GetCustomerData step for the process framework.
"""
import os
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.functions import kernel_function
from typing import List
from datetime import datetime

from entities.states import RepeatedCallState, IncomingMessage
from entities.database import Customer, CallEvent, HistoricCallEvent


class GetCustomerDataStep(KernelProcessStep):
    """
    Step to retrieve customer data and context for process execution.
    Uses the enhanced database objects with static data loading.
    """
    def __init__(self):
        super().__init__()
        self._state = RepeatedCallState()
    @kernel_function
    async def get_call_event(self, incoming_message, context: KernelProcessStepContext) -> None:
        """
        Process function to retrieve customer data and call events using the enhanced database objects.
        
        Args:
            incoming_message: The incoming message with customer ID
            context: The process step context
        """
        # Check if incoming_message is already the correct type
        # this code below is to 'fix' semantic_kernel.exceptions.kernel_exceptions.KernelException: The function get_call_event on step GetCustomerDataStep has more than one parameter, so a parameter name must be provided.
        if not isinstance(incoming_message, IncomingMessage):
            # If it's a dict or similar with attributes we need, try to convert it
            try:
                incoming_message = IncomingMessage(
                    customer_id=incoming_message.customer_id,
                    message=incoming_message.message,
                    time_stamp=incoming_message.time_stamp if hasattr(incoming_message, 'time_stamp') else datetime.utcnow()
                )
            except Exception as e:
                raise TypeError(f"Cannot convert input to IncomingMessage: {str(e)}")
        
        customer_id = incoming_message.customer_id
        
        # Find customer's call event using the enhanced class method
        customer_call_events = CallEvent.find_by_customer_id(customer_id)
        customer_call_event = next(iter(customer_call_events), None)
        if not customer_call_event:
            print(f"Warning: No call event found for customer ID {customer_id}")
        
        # Find customer's historic call events using the enhanced class method
        customer_historic_call_events = HistoricCallEvent.find_by_customer_id(customer_id)
        if not customer_historic_call_events:
            print(f"Warning: No historic call event found for customer ID {customer_id}")
        
        # Find customer using the enhanced class method
        customer = Customer.find_by_id(customer_id)
        if not customer:
            print(f"Warning: No customer found with ID {customer_id}")
        
        # Create state object
        repeated_call_state = RepeatedCallState(
            customer=customer,
            call_event=customer_call_event,
            call_history=customer_historic_call_events
        )
        
        # Emit event to continue process flow
        await context.emit_event("FetchingContextDone", data=repeated_call_state)
