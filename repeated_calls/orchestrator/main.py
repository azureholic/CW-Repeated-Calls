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
from repeated_calls.orchestrator.settings import (
    AzureOpenAISettings,
    AppInsightsSettings
)
from repeated_calls.orchestrator.steps.determine_recommendation import DetermineRecommendationStep
from repeated_calls.utils.loggers import Logger

from opentelemetry import trace

  # Initialize telemetry
from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.otel import configure_telemetry

# Get connection string from environment or settings
appinsights_settings = AppInsightsSettings()
configure_telemetry(appinsights_settings.connection_string, "repeated-calls-service")

from repeated_calls.utils.loggers import get_application_logger
from repeated_calls.streaming.settings import StreamingSettings
from frontend import utils as us
from azure.servicebus import ServiceBusMessage          


config_ingressqueue = StreamingSettings(queue='customercalls')
config_egressqueue = StreamingSettings(queue='agent_output_messages')


# Create a logger with your module name
logger = get_application_logger(__name__)
logger.info("Telemetry configured for Azure Monitor")
client = us.get_sb_client(config_ingressqueue.connection_string)

# Receiving the message from the servicebus
received_sb_msg = us.receive_servicebus_msg(client, config_ingressqueue.queue)

# Transforming the message into a dictionary
message = us.transform_servicebus_msg_2_dict(received_sb_msg)

def get_event(msg: dict) -> CallEvent:
    
    return CallEvent(
        id = int(msg['id']),
        customer_id = int(msg['customer_id']),
        sdc = msg['sdc'],
        timestamp = datetime.fromisoformat(msg['timestamp']),
    )

async def run_sequence(call_event: CallEvent) -> None:
    """Run the sequence of steps for the Repeated Calls process."""
    # Get OpenTelemetry tracer
    tracer = trace.get_tracer("repeated_calls.orchestrator")

    

    # Start a span for this sequence execution
    with tracer.start_as_current_span("repeated_calls.run_sequence") as span:
        state = State.from_call_event(call_event)
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
                kernel.add_plugin(cust, cust.name)   # → "CustomerDataPlugin"
                kernel.add_plugin(ops,  ops.name)    # → "OperationsDataPlugin"
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
                msg_2 = "Starting process execution..."
                us.send_servicebus_msg(msg_2, client, config_egressqueue.queue)
                logger.info(msg_2)
                await start(
                    process=process,
                    kernel=kernel,
                    initial_event=KernelProcessEvent(id="Start", data=state),
                )
                msg_3 = "Process execution completed successfully."
                us.send_servicebus_msg(msg_3, client, config_egressqueue.queue)
                logger.info(msg_3)

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

    call_event = get_event(message)
    if call_event is None:
        logger.info("No valid CallEvent found in the queue. Skipping.")
        # Optionally, continue to the next message or exit
        exit()

    msg_1 = "\n Application started."
    us.send_servicebus_msg(msg_1, client, config_egressqueue.queue)
    logger.info(msg_1)

    await run_sequence(call_event)

    msg_4 = "Application finished."
    us.send_servicebus_msg(msg_4, client, config_egressqueue.queue)
    logger.info(msg_4)

if __name__ == "__main__":
    asyncio.run(main())
