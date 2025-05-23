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
)
from repeated_calls.orchestrator.settings import (
    AzureOpenAISettings,
    AppInsightsSettings
)
from repeated_calls.orchestrator.steps.determine_recommendation import DetermineRecommendationStep
from repeated_calls.utils.loggers import Logger
from repeated_calls.webapp.service_bus_operations import ServiceBusOperations

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



def get_event() -> CallEvent:
    """Create a sample CallEvent object."""
    data_path = os.path.join(os.path.dirname(files("repeated_calls")), "data")
    csv_path = os.path.join(data_path, "call_event.csv")

    with open(csv_path, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert the data to appropriate types
            return CallEvent(
                id=int(row.get("id", -1)),
                customer_id=int(row.get("customer_id", -1)),
                sdc=row.get("sdc", "No description available"),
                timestamp=datetime.fromisoformat(row.get("timestamp", "1970-01-01 00:00:00")),
            )


async def get_events_from_service_bus() -> list[CallEvent]:
    """Get CallEvent objects from Service Bus."""
    try:
        messages = await ServiceBusOperations.receive_messages()
        call_events = []
        
        for message in messages:
            try:
                # Handle both string and dict message formats
                if isinstance(message, str):
                    import json
                    message_data = json.loads(message)
                else:
                    message_data = message
                
                # Create CallEvent from message data
                call_event = CallEvent(
                    id=message_data.get("id", 1),
                    customer_id=message_data.get("customer_id"),
                    sdc=message_data.get("sdc", "No description available"),
                    timestamp=datetime.fromisoformat(message_data.get("timestamp", datetime.now().isoformat()))
                )
                call_events.append(call_event)
                logger.info(f"Parsed CallEvent from Service Bus: ID={call_event.id}, Customer={call_event.customer_id}")
                
            except Exception as e:
                logger.error(f"Error parsing CallEvent from message: {str(e)}")
                # Fallback to sample event if parsing fails
                call_events.append(get_event())
        
        if not call_events:
            logger.info("No messages in Service Bus, using sample CallEvent")
            call_events.append(get_event())
            
        return call_events
        
    except Exception as e:
        logger.error(f"Error retrieving messages from Service Bus: {str(e)}")
        logger.info("Falling back to sample CallEvent")
        return [get_event()]


async def send_result_to_service_bus(state: State, processing_result: dict) -> None:
    """Send processing result back to Service Bus."""
    try:
        result_data = {
            "call_event_id": state.call_event.id,
            "customer_id": state.call_event.customer_id,
            "original_sdc": state.call_event.sdc,
            "processing_timestamp": datetime.now().isoformat(),
            "is_repeated_call": getattr(state, 'is_repeated_call', None),
            "cause_analysis": getattr(state, 'cause_result', None),
            "recommendation": getattr(state, 'recommendation_result', None),
            "processing_result": processing_result,
            "status": "completed"
        }
        
        success = await ServiceBusOperations.send_result(result_data)
        if success:
            logger.info(f"Successfully sent result to Service Bus for CallEvent {state.call_event.id}")
        else:
            logger.error(f"Failed to send result to Service Bus for CallEvent {state.call_event.id}")
            
    except Exception as e:
        logger.error(f"Error sending result to Service Bus: {str(e)}")


async def run_sequence() -> None:
    """Run the sequence of steps for the Repeated Calls process."""
    # Get OpenTelemetry tracer
    tracer = trace.get_tracer("repeated_calls.orchestrator")

    # Start a span for this sequence execution
    with tracer.start_as_current_span("repeated_calls.run_sequence") as span:
        # Get CallEvents from Service Bus
        call_events = await get_events_from_service_bus()
        
        logger.info(f"Processing {len(call_events)} CallEvent(s)")
        span.set_attribute("call_events.count", len(call_events))
        
        # Process each CallEvent
        for i, call_event in enumerate(call_events):
            with tracer.start_as_current_span(f"repeated_calls.process_call_event_{i}") as call_span:
                call_span.set_attribute("call_event.id", str(call_event.id))
                call_span.set_attribute("call_event.customer_id", str(call_event.customer_id))
                
                logger.info(f"### PROCESSING CALL EVENT {i+1}/{len(call_events)} ###")
                logger.debug(f"CallEvent details: {call_event}")
                
                state = State.from_call_event(call_event)
                processing_result = {"status": "started", "call_event_id": call_event.id}
                
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

                        logger.info(f"Starting process execution for CallEvent {call_event.id}...")
                        await start(
                            process=process,
                            kernel=kernel,
                            initial_event=KernelProcessEvent(id="Start", data=state),
                        )

                        processing_result.update({
                            "status": "completed",
                            "is_repeated_call": getattr(state, 'is_repeated_call', None),
                            "cause_analysis": getattr(state, 'cause_result', None),
                            "recommendation": getattr(state, 'recommendation_result', None)
                        })
                        
                        logger.info(f"Process execution completed successfully for CallEvent {call_event.id}")

                except Exception as exc:
                    logger.error(f"An error occurred during processing CallEvent {call_event.id}: %s", str(exc), exc_info=True)
                    processing_result.update({
                        "status": "failed",
                        "error": str(exc),
                        "error_type": type(exc).__name__
                    })
                    call_span.set_attribute("error", True)
                    call_span.set_attribute("error.message", str(exc))
                
                # Send result back to Service Bus
                await send_result_to_service_bus(state, processing_result)
                
        logger.info("All CallEvents processed successfully.")


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
