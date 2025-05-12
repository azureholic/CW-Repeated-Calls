import asyncio
from typing import ClassVar

from pydantic import BaseModel

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
    "historical_data": "data/historical_call_event.csv",
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


# Step 2: Analyze Call History
class AnalyzeCallHistoryStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def analyze_call_history(self, kernel: Kernel) -> None:
        historical_data_enricher = HistoricalDataEnricher(logger, csv_files["historical_data"], chat_completion)
        repeat_call_determiner = RepeatCallDeterminer()
        kernel.add_plugin(historical_data_enricher, plugin_name="HistoricalDataEnricher")
        kernel.add_plugin(repeat_call_determiner, plugin_name="RepeatCallDeterminer")

        # Retrieve historical data
        historical_data = await kernel.invoke_function_call(
            plugin_name="HistoricalDataEnricher",
            function_name="retrieve_historical_data",
            arguments={"call_history": self.state.call_event},
            chat_history=self.state.chat_history
        )

        # Analyze historical data to determine if it's a repeated call
        analysis_result = await kernel.invoke_function_call(
            plugin_name="RepeatCallDeterminer",
            function_name="determine_repeat_call",
            arguments={"historical_data": historical_data.function_result.value},
            chat_history=self.state.chat_history
        )
        self.state.analysis_result = analysis_result.function_result.value
        print(f"Analysis Result: {self.state.analysis_result}")


# Step 3: Retrieve Operational Data
class RetrieveOperationalDataStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def retrieve_operational_data(self, kernel: Kernel) -> None:
        operational_data_enricher = OperationalDataEnricher()
        kernel.add_plugin(operational_data_enricher, plugin_name="OperationalDataEnricher")

        operational_data = await kernel.invoke_function_call(
            plugin_name="OperationalDataEnricher",
            function_name="retrieve_operational_data",
            arguments={"issue_details": self.state.analysis_result},
            chat_history=self.state.chat_history
        )
        self.state.operational_data = operational_data.function_result.value
        print(f"Operational Data Retrieved: {self.state.operational_data}")


# Step 4: Retrieve Customer Data
class RetrieveCustomerDataStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def retrieve_customer_data(self, customer_id: str, kernel: Kernel) -> None:
        customer_data_enricher = CustomerDataEnricher()
        kernel.add_plugin(customer_data_enricher, plugin_name="CustomerDataEnricher")

        customer_data = await kernel.invoke_function_call(
            plugin_name="CustomerDataEnricher",
            function_name="retrieve_customer_data",
            arguments={"customer_id": customer_id},
            chat_history=self.state.chat_history
        )
        self.state.customer_data = customer_data.function_result.value
        print(f"Customer Data Retrieved: {self.state.customer_data}")


# Step 5: Generate and Publish Recommendations
class GenerateAndPublishRecommendationStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state

    @kernel_function
    async def generate_and_publish_recommendation(self, kernel: Kernel) -> None:
        recommendation_formulator = RecommendationFormulator()
        kernel.add_plugin(recommendation_formulator, plugin_name="RecommendationFormulator")

        recommendation = await kernel.invoke_function_call(
            plugin_name="RecommendationFormulator",
            function_name="formulate_recommendation",
            arguments={
                "analysis_result": self.state.analysis_result,
                "operational_data": self.state.operational_data,
                "customer_data": self.state.customer_data
            },
            chat_history=self.state.chat_history
        )
        self.state.recommendation = recommendation.function_result.value
        print(f"Recommendation Generated and Published: {self.state.recommendation}")


# Define the process flow
process_builder = ProcessBuilder(name="RepeatedCallHandling")

# Add the steps
call_event_step = process_builder.add_step(RetrieveCallEventStep)
analysis_step = process_builder.add_step(AnalyzeCallHistoryStep)
operational_data_step = process_builder.add_step(RetrieveOperationalDataStep)
customer_data_step = process_builder.add_step(RetrieveCustomerDataStep)
recommendation_step = process_builder.add_step(GenerateAndPublishRecommendationStep)


# Orchestrate the events
process_builder.on_input_event("Start").send_event_to(
    target=call_event_step, function_name="retrieve_call_history", parameter_name="customer_id"
)

call_event_step.on_function_result(function_name="retrieve_call_history").send_event_to(
    target=analysis_step, function_name="analyze_call_history"
)

analysis_step.on_function_result(function_name="analyze_call_history").send_event_to(
    target=operational_data_step, function_name="retrieve_operational_data"
)

operational_data_step.on_function_result(function_name="retrieve_operational_data").send_event_to(
    target=customer_data_step, function_name="retrieve_customer_data", parameter_name="customer_id"
)

customer_data_step.on_function_result(function_name="retrieve_customer_data").send_event_to(
    target=recommendation_step, function_name="generate_and_publish_recommendation"
)

# Build and run the Process
async def main():

    # Initialize chat history
    chat_history = ChatHistory()

    # Initialize the process state with chat_history
    process_state = RepeatedCallProcessState(chat_history=chat_history)

    # Step 1: Retrieve Call History
    call_event_step = RetrieveCallEventStep()
    await call_event_step.activate(process_state)
    await call_event_step.retrieve_call_event(customer_id="7", kernel=kernel)

    # Step 2: Analyze Call History
    analysis_step = AnalyzeCallHistoryStep()
    await analysis_step.activate(process_state)
    await analysis_step.analyze_call_history(kernel=kernel)

    # Step 3: Retrieve Operational Data
    operational_data_step = RetrieveOperationalDataStep()
    await operational_data_step.activate(process_state)
    await operational_data_step.retrieve_operational_data(kernel=kernel)

    # Step 4: Retrieve Customer Data
    customer_data_step = RetrieveCustomerDataStep()
    await customer_data_step.activate(process_state)
    await customer_data_step.retrieve_customer_data(customer_id="12345", kernel=kernel)

    # Step 5: Generate and Publish Recommendations
    recommendation_step = GenerateAndPublishRecommendationStep()
    await recommendation_step.activate(process_state)
    await recommendation_step.generate_and_publish_recommendation(kernel=kernel)

    # Print the final recommendation
    print(f"Final Recommendation: {process_state.recommendation}")


if __name__ == "__main__":
    asyncio.run(main())