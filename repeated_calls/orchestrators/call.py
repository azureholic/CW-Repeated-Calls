import asyncio
from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
#from semantic_kernel.processes.local_runtime import KernelProcessEvent, start
from repeated_calls.utils.keyvault_helper import KeyVaultHelper
from repeated_calls.utils.loggers import Logger

logger = Logger()

class RepeatedCallProcessState(BaseModel):
    """State for the Repeated Call Process."""
    chat_history: ChatHistory | None = None


class RetrieveCallHistoryStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state.state
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message="Retrieve call history for the customer.")

    @kernel_function
    async def retrieve_call_history(
        self, context: KernelProcessStepContext, customer_id: str, kernel: Kernel
    ) -> None:
        print(f"{RetrieveCallHistoryStep.__name__}\n\t Retrieving call history for customer_id: {customer_id}")

        # Simulate call history retrieval
        call_history = f"Call history for customer {customer_id}: [Call1, Call2, Call3]"
        self.state.chat_history.add_user_message(f"Call History:\n{call_history}")

        # Emit the retrieved call history as an event
        await context.emit_event(process_event="call_history_retrieved", data=call_history)


class AnalyzeRepeatedCallsStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state.state

    @kernel_function
    async def analyze_repeated_calls(
        self, context: KernelProcessStepContext, kernel: Kernel
    ) -> None:
        print(f"{AnalyzeRepeatedCallsStep.__name__}\n\t Analyzing repeated calls...")

        # Add analysis request to chat history
        self.state.chat_history.add_user_message("Analyze the repeated calls from the provided call history.")

        # Select the AI service
        chat_service, settings = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Perform analysis using the AI service
        response = await chat_service.get_chat_message_content(chat_history=self.state.chat_history, settings=settings)

        # Emit the analysis result as an event
        await context.emit_event(process_event="repeated_calls_analyzed", data=str(response))


class GenerateRecommendationStep(KernelProcessStep[RepeatedCallProcessState]):
    async def activate(self, state: KernelProcessStepState[RepeatedCallProcessState]):
        self.state = state.state

    @kernel_function
    async def generate_recommendation(
        self, context: KernelProcessStepContext, kernel: Kernel
    ) -> None:
        print(f"{GenerateRecommendationStep.__name__}\n\t Generating recommendations...")

        # Add recommendation request to chat history
        self.state.chat_history.add_user_message("Generate recommendations based on the repeated call analysis.")

        # Select the AI service
        chat_service, settings = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Generate recommendations using the AI service
        response = await chat_service.get_chat_message_content(chat_history=self.state.chat_history, settings=settings)

        # Emit the generated recommendation as an event
        await context.emit_event(process_event="recommendation_generated", data=str(response))


async def main():
    # Initialize the kernel
    kernel = Kernel()


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


    # Initialize the process state
    process_state = RepeatedCallProcessState()

    # Initialize the process steps
    retrieve_step = RetrieveCallHistoryStep()
    analyze_step = AnalyzeRepeatedCallsStep()
    recommend_step = GenerateRecommendationStep()

    # Activate the steps
    await retrieve_step.activate(KernelProcessStepState(name="RetrieveCallHistory", state=process_state))
    await analyze_step.activate(KernelProcessStepState(name="AnalyzeRepeatedCalls", state=process_state))
    await recommend_step.activate(KernelProcessStepState(name="GenerateRecommendation", state=process_state))

    # Step 1: Retrieve Call History
    customer_id = "12345"
    await retrieve_step.retrieve_call_history(context=None, customer_id=customer_id, kernel=kernel)

    # Step 2: Analyze Repeated Calls
    await analyze_step.analyze_repeated_calls(context=None, kernel=kernel)

    # Step 3: Generate Recommendations
    await recommend_step.generate_recommendation(context=None, kernel=kernel)


if __name__ == "__main__":
    asyncio.run(main())
