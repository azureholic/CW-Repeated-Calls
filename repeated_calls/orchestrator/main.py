"""Main application script for the Repeated Calls process."""

import argparse
import asyncio
import csv
import os
from datetime import datetime
from importlib.resources import files

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from repeated_calls.orchestrator.steps.determine_cause import DetermineCauseStep
from repeated_calls.orchestrator.steps.determine_repeated_call import DetermineRepeatedCallStep
from repeated_calls.orchestrator.steps.exit_step import ExitStep

from repeated_calls.database.schemas import CallEvent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.plugins import (
    customer_plugin,
    operations_plugin,
    McpApiKeyPlugin,
)
from repeated_calls.orchestrator.settings import AzureOpenAISettings, AppInsightsSettings
from repeated_calls.orchestrator.steps.determine_recommendation import DetermineRecommendationStep
from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.conversation_saver import (
    get_current_timestamp,
    setup_logging_directories,
    AGENT_NAMES,
)

from opentelemetry import trace

# Initialize telemetry
from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.otel import configure_telemetry

# Get connection string from environment or settings
appinsights_settings = AppInsightsSettings()
configure_telemetry(appinsights_settings.connection_string, "repeated-calls-service")

from repeated_calls.utils.loggers import get_application_logger

# Create a logger with your module name
logger = get_application_logger(__name__)
logger.info("Telemetry configured for Azure Monitor")


def get_event(row_id: int | None = None) -> CallEvent:
    """Create a sample CallEvent object."""
    data_path = os.path.join(os.path.dirname(files("repeated_calls")), "data")
    csv_path = os.path.join(data_path, "call_event.csv")

    with open(csv_path, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        if not rows:
            raise ValueError("CSV file is empty")

        if row_id is None:
            row = rows[0]
        else:
            matching_rows = [r for r in rows if int(r.get("id", -1)) == row_id]
            if not matching_rows:
                raise ValueError(f"No row found with ID {row_id}")
            row = matching_rows[0]

        return CallEvent(
            id=int(row.get("id", -1)),
            customer_id=int(row.get("customer_id", -1)),
            sdc=row.get("sdc", "No description available"),
            timestamp=datetime.fromisoformat(row.get("timestamp", "1970-01-01 00:00:00")),
        )


async def run_sequence(row_id: int = 1) -> None:
    """Run the sequence of steps for the Repeated Calls process."""
    # Get OpenTelemetry tracer
    tracer = trace.get_tracer("repeated_calls.orchestrator")

    # Setup logging directories
    setup_logging_directories()

    # Generate a run timestamp for this execution
    run_timestamp = get_current_timestamp()
    logger.info(f"Starting run with timestamp: {run_timestamp} for row_id: {row_id}")

    # Start a span for this sequence execution
    with tracer.start_as_current_span("repeated_calls.run_sequence") as span:
        call_event = get_event(row_id)
        state = State.from_call_event(call_event)
        state.run_timestamp = run_timestamp
        state.row_id = str(row_id)
        logger.debug(f"### INCOMING CALL ###\n{state.call_event}")
        # Add attributes to the span
        span.set_attribute("call_event.id", str(call_event.id))
        span.set_attribute("call_event.customer_id", str(call_event.customer_id))

        try:
            settings = AzureOpenAISettings()

            kernel = Kernel()
            kernel.add_service(
                AzureChatCompletion(
                    endpoint=settings.endpoint,
                    api_key=settings.api_key.get_secret_value() if settings.api_key else None,
                    deployment_name=settings.deployment,
                )
            )

            # Keep MCP plugins alive for the whole run
            async with customer_plugin() as cust, operations_plugin() as ops:
                kernel.add_plugin(cust, cust.name)  # → "CustomerDataPlugin"
                kernel.add_plugin(ops, ops.name)  # → "OperationsDataPlugin"
                kernel.add_plugin(McpApiKeyPlugin(), "McpApiKeyPlugin")

                process_builder = ProcessBuilder("RepeatedCalls")

                # Add steps
                determine_repeated_call = process_builder.add_step(DetermineRepeatedCallStep)
                determine_cause = process_builder.add_step(DetermineCauseStep)
                determine_recommendation = process_builder.add_step(DetermineRecommendationStep)
                exit_step = process_builder.add_step(ExitStep)

                # Orchestrate steps
                process_builder.on_input_event("Start").send_event_to(
                    determine_repeated_call, function_name="repeated_call", parameter_name="state"
                )

                determine_repeated_call.on_event("IsRepeatedCall").send_event_to(
                    determine_cause, function_name="cause", parameter_name="state"
                )
                determine_repeated_call.on_event("IsNotRepeatedCall").send_event_to(exit_step)

                determine_cause.on_event("IsRelevant").send_event_to(
                    determine_recommendation, function_name="recommend", parameter_name="state"
                )
                determine_cause.on_event("IsNotRelevant").send_event_to(exit_step)

                determine_recommendation.on_event("Exit").send_event_to(exit_step)

                # Compile/build
                process = process_builder.build()

                logger.info("Starting process execution...")
                await start(
                    process=process,
                    kernel=kernel,
                    initial_event=KernelProcessEvent(id="Start", data=state),
                )

                logger.info("Process execution completed successfully.")

        except Exception as exc:
            logger.error(
                "An error occurred during the sequence execution: %s", str(exc), exc_info=True
            )
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
    parser.add_argument(
        "--row_id",
        type=int,
        default=1,
        help="Row ID to use from the call_event.csv file (default: 1)",
    )
    args = parser.parse_args()

    if args.loglevel:
        logger.setLevel(args.loglevel.upper())

    call_event = get_event()

    logger.info("Application started.")
    await run_sequence(row_id=args.row_id)
    logger.info("Application finished.")


if __name__ == "__main__":
    asyncio.run(main())
