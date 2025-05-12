import asyncio
import sys
from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.processes.kernel_process import KernelProcessStepContext

from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.keyvault_helper import KeyVaultHelper
from repeated_calls.plugins.csv.ingress_processor import IngressProcessor
from repeated_calls.plugins.csv.operational_data_enricher import OperationalDataEnricher
from repeated_calls.plugins.csv.customer_data_enricher import CustomerDataEnricher
from repeated_calls.plugins.csv.historical_data_enricher import HistoricalDataEnricher
from repeated_calls.plugins.csv.repeat_call_determiner import RepeatCallDeterminer
from repeated_calls.plugins.csv.recommendation_formulator import RecommendationFormulator

from semantic_kernel.contents.function_call_content import FunctionCallContent

logger = Logger()

key_vault_name = "kv-codewith-dev"
key_vault_helper = KeyVaultHelper(key_vault_name)
api_key = key_vault_helper.get_secret("AZURE-OPENAI-KEY")
api_url = key_vault_helper.get_secret("AZURE-OPENAI-URL")

# Initialize the kernel
kernel = Kernel()

# Configure Azure OpenAI service
chat_completion = AzureChatCompletion(
    deployment_name="gpt-4o",
    api_key=api_key,
    base_url=api_url,
    )
kernel.add_service(chat_completion)

# Configure execution settings
execution_settings = AzureChatPromptExecutionSettings()
execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

csv_files = {
    "call_data": "data/call_event.csv",
    "customer_data": "data/customer.csv",
    "discount_data": "data/discount.csv",
    "historical_data": "data/historic_call_event.csv",
    "product_data": "data/product.csv",
    "operational_data": "data/software_update.csv",
    "subcription_data": "data/subscription.csv",
}


# Define the process state
class RepeatedCallProcessState(BaseModel):
    """State for the Repeated Call Process."""
    chat_history: ChatHistory | None = None


# Step 1: Retrieve Call Event
class RetrieveCallEventStep(KernelProcessStep[RepeatedCallProcessState]):

    state: RepeatedCallProcessState = Field(default_factory=RepeatedCallProcessState)
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def retrieve_call_event(self, customer_id: str, kernel: Kernel) -> None:
        ingress_processor = IngressProcessor(logger=logger, csv_file_path=csv_files["call_data"])
        kernel.add_plugin(ingress_processor, plugin_name="IngressProcessor")

        function_call = FunctionCallContent(
            plugin_name="IngressProcessor",
            function_name="ingress_process",
            arguments={"customer_id": customer_id, "chat_history": self.state.chat_history}
        )

        call_event = await kernel.invoke_function_call(
            function_call=function_call,
            chat_history=self.state.chat_history
        )

        # Need to fix this - Store the call history in the process state
        #self.state.call_event = call_event.function_result.value
        logger.info(f"Call Event Retrieved: {self.state.chat_history}")


# Step 2: Retrieve Call History
class RetrieveCallHistoryStep(KernelProcessStep[RepeatedCallProcessState]):
    state: RepeatedCallProcessState = Field(default_factory=RepeatedCallProcessState)
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def retrieve_call_history(self, customer_id: str, kernel: Kernel) -> None:
        historical_data_enricher = HistoricalDataEnricher(logger, csv_files["historical_data"])
        kernel.add_plugin(historical_data_enricher, plugin_name="HistoricalDataEnricher")

        function_call = FunctionCallContent(
            plugin_name="HistoricalDataEnricher",
            function_name="retrieve_historical_data",
            arguments={"customer_id": customer_id, "chat_history": self.state.chat_history}
        )

        historical_data = await kernel.invoke_function_call(
            function_call=function_call,
            chat_history=self.state.chat_history
        )
        #self.state.call_history_result = historical_data.function_result.value
        print(f"Call History Result: {self.state.chat_history}")


# Step 3: Determine if the Call is a Repeat Call
class DetermineRepeatCallStep(KernelProcessStep[RepeatedCallProcessState]):
    state: RepeatedCallProcessState = Field(default_factory=RepeatedCallProcessState)

    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def determine_repeat_call(self, kernel: Kernel) -> None:
        repeat_call_determiner = RepeatCallDeterminer(
            kernel=kernel,
            logger=logger,
            chat_completion=chat_completion,
            execution_settings=execution_settings,
        )
        is_repeat = await repeat_call_determiner.determine_repeat_call(self.state.chat_history)

        if is_repeat:
            logger.info("Call identified as a repeat. Proceeding with further steps.")
        else:
            logger.info("Call is not a repeat. Exiting application.")
            print("Call is not a repeat. Exiting application.")
            sys.exit(0)


# Step 4: Generate Recommendation
class GenerateRecommendationStep(KernelProcessStep[RepeatedCallProcessState]):
    state: RepeatedCallProcessState = Field(default_factory=RepeatedCallProcessState)

    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def generate_recommendation(self, kernel: Kernel) -> None:
        try:
            system_prompt = """
            Based on the provided chat history, generate a recommendation for the customer.
            Confirm if the issue resported in historical call event is related to issue mentioned in call event
            Please respond only with single line if issues are related or not.
            """

            self.state.chat_history.add_message({"role": "system", "content": system_prompt})

            # Filter out invalid messages (e.g., messages with role 'tool')
            valid_chat_history = ChatHistory()
            for message in self.state.chat_history.messages:
                if message.role not in ["tool"]:
                    valid_chat_history.add_message(message)


            response = await chat_completion.get_chat_message_content(
                chat_history=valid_chat_history,
                settings=execution_settings,
                kernel=kernel
            )

            # Log and print the recommendation
            logger.info(f"Generated Recommendation: {response}")
            print(f"Generated Recommendation:\n{response}")

        except Exception as e:
            error_message = f"Error generating recommendation: {e}"
            logger.error(error_message, exc_info=True)
            print(error_message)


# Define the process flow
process_builder = ProcessBuilder(name="RepeatedCallHandling")

# Add the steps
call_event_step = process_builder.add_step(RetrieveCallEventStep)
retrieve_call_history_step = process_builder.add_step(RetrieveCallHistoryStep)
recommendation_step = process_builder.add_step(GenerateRecommendationStep)


# Orchestrate the events

# Step 1: Start the process by retrieving the call event
process_builder.on_input_event("Start").send_event_to(
    target=call_event_step, function_name="retrieve_call_event", parameter_name="customer_id"
)

# Step 2: After retrieving the call event, retrieve the call history
call_event_step.on_function_result(function_name="retrieve_call_event").send_event_to(
    target=retrieve_call_history_step, function_name="retrieve_call_history", parameter_name="customer_id"
)

# Step 3: After retrieving the call history, generate the recommendation
retrieve_call_history_step.on_function_result(function_name="retrieve_call_history").send_event_to(
    target=recommendation_step, function_name="generate_recommendation"
)


# Build and run the Process
async def main():

    # Initialize chat history
    chat_history = ChatHistory()

    # Initialize the process state with chat_history
    process_state = RepeatedCallProcessState(chat_history=chat_history)

    #process = process_builder.build()
    #await process.start(input_event="Start", parameter_name="customer_id", parameter_value="7", state=process_state)


    # Step 1: Retrieve Call History
    call_event_step = RetrieveCallEventStep()
    await call_event_step.activate(process_state)
    await call_event_step.retrieve_call_event(customer_id="7", kernel=kernel)

    # Step 2: Retrieve Call History
    retrieve_call_history_step = RetrieveCallHistoryStep()
    await retrieve_call_history_step.activate(process_state)
    await retrieve_call_history_step.retrieve_call_history(customer_id="7", kernel=kernel)

    # Step 3: Generate Recommendation
    recommendation_step = GenerateRecommendationStep()
    await recommendation_step.activate(process_state)
    await recommendation_step.generate_recommendation(kernel=kernel)


if __name__ == "__main__":
    asyncio.run(main())