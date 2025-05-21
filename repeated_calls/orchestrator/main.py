"""Main application script for the Repeated Calls process."""

import argparse
import asyncio
import csv
import os
from datetime import datetime
from importlib.resources import files

from azure.ai.projects import AIProjectClient, enable_telemetry
from azure.ai.inference.tracing import AIInferenceInstrumentor 
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry import trace

from repeated_calls.orchestrator.observability import setup_observability

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.connectors.ai.azure_ai_inference import AzureAIInferenceChatCompletion
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.tracing import AIInferenceInstrumentor 
from steps.determine_cause import DetermineCauseStep
from steps.determine_repeated_call import DetermineRepeatedCallStep
from steps.exit_step import ExitStep

from repeated_calls.database.schemas import CallEvent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.plugins.csv.customer import CustomerDataPlugin
from repeated_calls.orchestrator.plugins.csv.operations import OperationsDataPlugin
from repeated_calls.orchestrator.settings import AzureOpenAISettings, AzureAIFoundrySettings

from repeated_calls.orchestrator.steps.determine_recommendation import DetermineRecommendationStep
from repeated_calls.utils.loggers import Logger


ai_foundry_settings = AzureAIFoundrySettings()

project_client = AIProjectClient(
    endpoint=ai_foundry_settings.endpoint,
    credential=DefaultAzureCredential()
)

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "repeated_calls"})
application_insights_connection_string = project_client.telemetry.get_connection_string()        

logger = Logger()

setup_observability(
    connection_string=application_insights_connection_string,
    resource=resource
)

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

        # kernel.add_service(AzureAIInferenceChatCompletion(
        #     ai_model_id=settings.deployment,
        #     client=ChatCompletionsClient(
        #         endpoint=f"{str(settings.endpoint).strip('/')}/openai/deployments/{settings.deployment}",
        #         credential=DefaultAzureCredential(),
        #         credential_scopes=["https://cognitiveservices.azure.com/.default"],
        #     ),
        # ))
        kernel.add_plugin(CustomerDataPlugin(data_path="data"), "CustomerDataPlugin")
        kernel.add_plugin(OperationsDataPlugin(data_path="data"), "OperationsDataPlugin")

        logger.debug("Initialising state...")
        call_event = get_event()

        state = State.from_call_event(call_event)
        logger.debug("State initialized: %s", state)

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

        scenario = os.path.basename("repeated_call_flow")
        tracer = trace.get_tracer(__name__)
       
        with tracer.start_as_current_span(scenario):
            logger.info("Starting process execution...")
            await start(
                process=process,
                kernel=kernel,
                initial_event=KernelProcessEvent(id="Start", data=state),
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
