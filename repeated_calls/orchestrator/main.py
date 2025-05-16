"""Main application script for the Repeated Calls process."""

import argparse
import asyncio
from datetime import datetime

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from steps.determine_repeated_call import DetermineRepeatedCallStep
from steps.exit_step import ExitStep

from repeated_calls.database.schemas import CallEvent
from repeated_calls.orchestrator.plugins.csv.customer import CustomerDataPlugin
from repeated_calls.orchestrator.settings import AzureOpenAISettings
from repeated_calls.utils.loggers import Logger

logger = Logger()


async def run_sequence() -> None:
    """Run the sequence of steps for the Repeated Calls process."""
    try:
        logger.debug("Initializing Azure OpenAI settings...")
        settings = AzureOpenAISettings()

        logger.debug("Creating Semantic Kernel instance...")
        kernel = Kernel()

        logger.debug("Adding AzureChatCompletion service to kernel...")
        kernel.add_service(
            AzureChatCompletion(
                endpoint=settings.endpoint,
                api_key=settings.api_key.get_secret_value() if settings.api_key else None,
                deployment_name=settings.deployment,
            )
        )
        kernel.add_plugin(CustomerDataPlugin("data"))

        # Add the message manually now for testing purposes
        call_event = CallEvent(
            id=1,
            customer_id=7,
            sdc="My self-driving mower isn't working since this morning",
            timestamp=datetime.fromisoformat("2024-01-10 10:05:22"),
        )

        process_builder = ProcessBuilder("RepeatedCalls")

        # Add steps
        determine_repeated_call = process_builder.add_step(DetermineRepeatedCallStep)
        exit_step = process_builder.add_step(ExitStep)

        # Orchestrate steps
        process_builder.on_input_event("Start").send_event_to(
            determine_repeated_call, function_name="repeated_call", parameter_name="call_event"
        )
        process_builder.on_event("IsRepeatedCall").send_event_to(exit_step)
        process_builder.on_event("IsNotRepeatedCall").send_event_to(exit_step)

        # Compile/build
        process = process_builder.build()

        logger.info("Starting process execution...")
        await start(
            process=process,
            kernel=kernel,
            initial_event=KernelProcessEvent(id="Start", data=call_event),
        )

        logger.info("Process execution completed successfully.")

    except Exception as exc:
        logger.error("An error occurred during the sequence execution: %s", str(exc), exc_info=True)
        raise


async def main() -> None:
    """Entry point for the Repeated Calls application."""
    parser = argparse.ArgumentParser(description="Run the Repeated Calls process.")
    parser.add_argument(
        "--loglevel",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override the default log level (e.g., DEBUG, INFO, WARNING)",
    )
    args = parser.parse_args()

    if args.loglevel:
        logger.setLevel(args.loglevel.upper())

    logger.info("Application started.")
    await run_sequence()
    logger.info("Application finished.")


if __name__ == "__main__":
    asyncio.run(main())
