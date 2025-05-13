"""Main application script for the Repeated Calls process."""
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from entities.states import IncomingMessage
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from steps.determine_cause_step import DetermineCauseStep
from steps.determine_customer_advice import DetermineCustomerAdviceStep
from steps.determine_repeated_caller_step import DetermineRepeatedCallerStep
from steps.exit_step import ExitStep
from steps.get_customer_data_step import GetCustomerDataStep


async def run_sequence() -> None:
    """Main function to run the repeated calls process."""
    # Load environment variables
    load_dotenv()

    # Create Semantic Kernel instance
    kernel = Kernel()

    # Add Azure OpenAI chat completion service
    kernel.add_service(AzureChatCompletion())

    # This is the incoming message that will be processed (simulating a customer call)
    incoming_message = IncomingMessage(
        customer_id=7,
        message="My self-driving mower isn't working since this morning",
        time_stamp=datetime.fromisoformat("2024-01-10 10:05:22"),
    )

    # Create the process builder
    process_builder = ProcessBuilder("RepeatedCalls")

    # Add the steps
    get_customer_context_step = process_builder.add_step(GetCustomerDataStep)
    determine_repeated_caller_step = process_builder.add_step(DetermineRepeatedCallerStep)
    determine_cause_step = process_builder.add_step(DetermineCauseStep)
    determine_customer_advice_step = process_builder.add_step(DetermineCustomerAdviceStep)
    exit_step = process_builder.add_step(ExitStep)

    # Orchestrate the events
    process_builder.on_input_event("Start").send_event_to(
        get_customer_context_step, function_name="get_call_event"
    )

    get_customer_context_step.on_event("FetchingContextDone").send_event_to(
        determine_repeated_caller_step, function_name="repeated_call", parameter_name="callstate"
    )

    determine_repeated_caller_step.on_event("IsRepeatedCall").send_event_to(
        determine_cause_step, function_name="determine_cause", parameter_name="result"
    )
    determine_repeated_caller_step.on_event("IsNotRepeatedCall").send_event_to(exit_step)

    determine_cause_step.on_event("CauseDetermined").send_event_to(
        determine_customer_advice_step, function_name="get_advice", parameter_name="cause_result"
    )
    determine_cause_step.on_event("NotCauseDetermined").send_event_to(exit_step)

    determine_customer_advice_step.on_event("AdviceProvided").send_event_to(exit_step)
    determine_customer_advice_step.on_event("NotAdviceProvided").send_event_to(exit_step)

    # Build and run the process
    process = process_builder.build()

    await start(
        process=process,
        kernel=kernel,
        initial_event=KernelProcessEvent(id="Start", data=incoming_message),
    )


async def main():
    """Main entry point for the application."""
    await run_sequence()


if __name__ == "__main__":
    asyncio.run(main())
