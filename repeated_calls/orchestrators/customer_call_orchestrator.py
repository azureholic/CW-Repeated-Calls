import asyncio
from semantic_kernel import Kernel
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

from semantic_kernel.contents.chat_history import ChatHistory
from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.keyvault_helper import KeyVaultHelper

from repeated_calls.plugins.csv.ingress_processor import IngressProcessor
from repeated_calls.plugins.csv.historical_data_enricher import HistoricalDataEnricher
from repeated_calls.plugins.csv.repeat_call_determiner import RepeatCallDeterminer
from repeated_calls.plugins.csv.operational_data_enricher import OperationalDataEnricher
from repeated_calls.plugins.csv.customer_data_enricher import CustomerDataEnricher
from repeated_calls.plugins.csv.recommendation_formulator import RecommendationFormulator
from repeated_calls.plugins.csv.recommendation_reviewer import RecommendationReviewer
from repeated_calls.plugins.csv.recommendation_publisher import RecommendationPublisher

logger = Logger()

key_vault_name = "kv-codewith-dev"
key_vault_helper = KeyVaultHelper(key_vault_name)
api_key = key_vault_helper.get_secret("AZURE-OPENAI-KEY")
api_url = key_vault_helper.get_secret("AZURE-OPENAI-URL")

kernel = Kernel()

chat_completion = AzureChatCompletion(
    deployment_name="gpt-4o",
    api_key=api_key,
    base_url=api_url,
)
kernel.add_service(chat_completion)

execution_settings = AzureChatPromptExecutionSettings()
execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
history = ChatHistory()

csv_files = {
    "call_data": "data/call_event.csv",
    "customer_data": "data/customer.csv",
    "discount_data": "data/discount.csv",
    "historical_data": "data/historical_call_event.csv",
    "product_data": "data/product.csv",
    "operational_data": "data/software_update.csv",
    "subcription_data": "data/subscription.csv",
}

async def main():
    ingress_processor = IngressProcessor(logger, csv_files["call_data"])
    historical_data_enricher = HistoricalDataEnricher(logger, csv_files["historical_data"], chat_completion)
    repeat_call_determiner = RepeatCallDeterminer(kernel, logger, chat_completion, execution_settings)
    operational_data_enricher = OperationalDataEnricher(logger, csv_files["operational_data"])
    customer_data_enricher = CustomerDataEnricher(logger, csv_files["customer_data"])
    recommendation_formulator = RecommendationFormulator(logger, chat_completion, execution_settings)
    recommendation_reviewer = RecommendationReviewer(logger, csv_files["customer_data"])
    recommendation_publisher = RecommendationPublisher(logger)

    kernel.add_plugin(ingress_processor, plugin_name="IngressProcessor")
    kernel.add_plugin(historical_data_enricher, plugin_name="HistoricalDataEnricher")
    kernel.add_plugin(repeat_call_determiner, plugin_name="RepeatCallDeterminer")
    kernel.add_plugin(operational_data_enricher, plugin_name="OperationalDataEnricher")
    kernel.add_plugin(customer_data_enricher, plugin_name="CustomerDataEnricher")
    kernel.add_plugin(recommendation_formulator, plugin_name="RecommendationFormulator")
    kernel.add_plugin(recommendation_reviewer, plugin_name="RecommendationReviewer")
    kernel.add_plugin(recommendation_publisher, plugin_name="RecommendationPublisher")


    while True:
        customer_id_input = input("User > Please provide the customer ID (or type 'exit' to quit): ")
        if customer_id_input.lower() == "exit":
            break
        try:
            customer_id = int(customer_id_input)
        except ValueError:
            print("Assistant > Invalid customer ID. Please enter a numeric value.")
            continue

        # Step 1: Ingress Process
        ingress_data_func = FunctionCallContent(
            plugin_name="IngressProcessor",
            function_name="ingress_process",
            arguments={"customer_id": customer_id}
        )
        ingress_invocation_context = await kernel.invoke_function_call(
            function_call=ingress_data_func,
            chat_history=history
        )

        logger.info(f"Updated Chat History: {history}")

        if ingress_invocation_context is None:
            logger.error("IngressProcessor function invocation failed or terminated.")
            print("Error: IngressProcessor function invocation failed.")
        else:
            ingress_data = ingress_invocation_context.function_result.value
            logger.info(f"Returned ingress_data: {ingress_data}")
            print(f"Ingress Data: {ingress_data}")

        # Step 2: Retrieve Historical Call Data
        historical_data_func = FunctionCallContent(
            plugin_name="HistoricalDataEnricher",
            function_name="retrieve_historical_data",
            arguments={"ingress_data": ingress_data, "history": history}
        )   
        historical_data = await kernel.invoke_function_call(
            function_call=historical_data_func,
            chat_history=history
        )

        # Step 3: Determine Repeat Call
        repeat_call = await kernel.invoke(
            plugin_name="RepeatCallDeterminer",
            function_name="determine_repeat_call",
            historical_data=historical_data
        )

        # Step 4: Retrieve Operational Data
        operational_data = await kernel.invoke(
            plugin_name="OperationalDataEnricher",
            function_name="retrieve_operational_data",
            product_id=1  # Example product_id
        )

        # Step 5: Retrieve Customer Data
        customer_data = await kernel.invoke(
            plugin_name="CustomerDataEnricher",
            function_name="retrieve_customer_data",
            customer_id=customer_id
        )

        # Step 6: Formulate Recommendation
        recommendation = await kernel.invoke(
            plugin_name="RecommendationFormulator",
            function_name="formulate_recommendation",
            repeat_call=repeat_call,
            operational_data=operational_data,
            customer_data=customer_data
        )

        # Step 7: Review Recommendation
        reviewed_recommendation = await kernel.invoke(
            plugin_name="RecommendationReviewer",
            function_name="review_recommendation",
            recommendation=recommendation
        )

        # Step 8: Publish Recommendation
        result = await kernel.invoke(
            plugin_name="RecommendationPublisher",
            function_name="publish_recommendation",
            recommendation=reviewed_recommendation
        )

        # Add the message from the agent to the chat history
        history.add_message(result)

        # Print the recommendation
        print("Assistant > " + str(result))

if __name__ == "__main__":
    asyncio.run(main())
