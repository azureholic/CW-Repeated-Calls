"""GetCustomerData step for the process framework."""
import json

from entities.database import Customer, Discount
from entities.structured_output import OfferResult
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.prompt_engineering.prompts import RecommendationPrompt


class DetermineCustomerAdviceStep(KernelProcessStep):
    """Step to determine customer value and advice based on the call event."""

    @kernel_function
    async def get_advice(self, cause_result, kernel: Kernel, context: KernelProcessStepContext) -> None:
        """
        Process function to retrieve customer data and call events using the enhanced database objects.

        Args:
            cause_result: The result of the cause event
            context: The process step context
        """
        customer_id = cause_result.customer_id

        # Get CLV value of the customer
        customer_clv = Customer.find_by_id(customer_id).clv
        if not customer_clv:
            print(f"Warning: No customer found with ID {customer_id}")

        # if customer clv value is high then continue
        # otherwise exit
        if customer_clv == "Low":
            print(f"Warning: Customer CLV value is low for customer ID {customer_id}")
            # Emit event to exit process
            await context.emit_event("NotAdviceProvided", data=None)
            return
        # if customer clv is medium or higher then get the query the discount table
        # get the productId from the cause result
        # Get product discounts
        allDiscountsForProduct = Discount.find_by_product_id(cause_result.product_id)

        if not allDiscountsForProduct:
            print(f"Warning: No discount found for product ID {cause_result.product_id}")
            return

        # Filter discounts to find one matching the customer's CLV value
        matching_discount = None
        for discount in allDiscountsForProduct:
            # Check if the discount applies to this customer's CLV level
            if discount.minimum_clv == customer_clv:
                # TODO: CLV is a string with values "Low", "Medium", "High", should be an enum and should handle "<=" operation
                matching_discount = discount
                break

        if not matching_discount:
            print(
                f"Warning: No matching discount found for customer CLV value {customer_clv} and product ID {cause_result.product_id}"
            )
            return

        # Now we have a single discount object that matches the customer's CLV value
        print(
            f"Found matching discount: {matching_discount.percentage}% for customer ID {customer_id} with CLV {customer_clv} and duration {matching_discount.duration_months} months"
        )

        # Construct prompt
        prompt = RecommendationPrompt(cause_result, customer_clv, matching_discount)

        # Create the chat completion
        chat_service, execution_settings = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(prompt.get_system_prompt())
        chat_history.add_user_message(prompt.get_user_prompt())

        execution_settings = AzureChatPromptExecutionSettings(response_format=OfferResult)

        response = await chat_service.get_chat_message_content(chat_history=chat_history, settings=execution_settings)

        try:
            # Parse the JSON response
            formatted_response = json.loads(response.content)

            # Convert to OfferResult object
            result = OfferResult(
                customer_id=customer_id,
                product_id=formatted_response.get("product_id", 0),
                advice=formatted_response.get("advice", ""),
            )

            print(result)
            # Emit appropriate event based on result
            if result.product_id:
                await context.emit_event("AdviceProvided", data=result)

        except json.JSONDecodeError:
            print("Error parsing AI response as JSON")
            await context.emit_event("IsNotRepeatedCall")
