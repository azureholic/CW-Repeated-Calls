"""GetCustomerData step for the process framework."""
import json

from entities.database import Customer, Discount
from entities.states import RepeatedCallState
from entities.structured_output import OfferResult
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext


class DetermineCustomerAdviceStep(KernelProcessStep):
    """Step to determine customer value and advice based on the call event."""

    def __init__(self):
        """Initialise the DetermineCustomerAdviceStep."""
        super().__init__()
        self._state = RepeatedCallState()
        self._system_prompt = """
        Your job is to determine if the customer is eligible for a discount based on their
        customer lifetime value (CLV). To do this, you will be provided with a customer ID and a
        product ID, and you must identify the associated discounts. Write a message to the user
        with the customer ID, product ID, CLV value, discount percentage, and duration in months.
        If the customer is not eligible for a discount, write a message to the user indicating
        that. Assure the customer that they are valued and that the company is working to improve
        their experience.
        """

    @kernel_function
    async def get_advice(self, cause_result, kernel: Kernel, context: KernelProcessStepContext) -> None:
        """
        Process function to retrieve customer data and call events using the enhanced database objects.

        Args:
            cause_result: The result of the cause event
            context: The process step context
        """
        customer_id = cause_result.customer_id

        # Get HLV value of the customer
        customer_clv_value = Customer.find_by_id(customer_id).clv
        if not customer_clv_value:
            print(f"Warning: No customer found with ID {customer_id}")

        # if customer clv value is high then continue
        # otherwise exit
        if customer_clv_value == "Low":
            print(f"Warning: Customer CLV value is low for customer ID {customer_id}")
            # Emit event to exit process
            await context.emit_event("NotAdviceProvided", data=None)
            return
        # if customer clv value is medium or higher then get the query the discount table
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
            if discount.minimum_clv == customer_clv_value:
                matching_discount = discount
                break

        if not matching_discount:
            print(
                f"Warning: No matching discount found for customer CLV value {customer_clv_value} and product ID {cause_result.product_id}"
            )
            return

        # Now we have a single discount object that matches the customer's CLV value
        print(
            f"Found matching discount: {matching_discount.percentage}% for customer ID {customer_id} with CLV {customer_clv_value} and duration {matching_discount.duration_months} months"
        )

        # Build the user message with detailed context
        user_message = []
        user_message.append(f"## Customer ID: {cause_result.customer_id}")
        user_message.append(f"## Product ID: {cause_result.product_id}")
        user_message.append(f"## CLV Value: {customer_clv_value}")
        user_message.append(f"## Discount: {matching_discount.percentage}%")
        user_message.append(f"## Duration: {matching_discount.duration_months} months")

        # Create the chat completion
        chat_service, execution_settings = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec

        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(self._system_prompt)
        chat_history.add_user_message("\n".join(user_message))

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
