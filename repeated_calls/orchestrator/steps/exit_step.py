"""Exit step for the process framework."""
from typing import Any
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep

from repeated_calls.utils.loggers import Logger
from repeated_calls.orchestrator.entities.state import State

logger = Logger()


class ExitStep(KernelProcessStep):
    """Step to exit the process and log final state."""

    @kernel_function
    def exit(self, state: State = None) -> None:
        """Process function to exit the process with final state logging."""
        logger.debug(">> EXIT: Ending the process.")
        
        if state:
            logger.info(f"Final processing state for CallEvent {state.call_event.id}:")
            logger.info(f"  - Customer ID: {state.call_event.customer_id}")
            logger.info(f"  - Is Repeated Call: {getattr(state, 'is_repeated_call', 'Not determined')}")
            logger.info(f"  - Cause Analysis: {getattr(state, 'cause_result', 'Not performed')}")
            logger.info(f"  - Recommendation: {getattr(state, 'recommendation_result', 'Not generated')}")
        else:
            logger.info("Process completed without state information.")
        
        logger.info("Process execution finished successfully.")
