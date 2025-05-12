"""
DetermineCause step for the process framework.
"""
import json
from typing import List
from semantic_kernel import Kernel
from semantic_kernel.processes.kernel_process import KernelProcessStep
from semantic_kernel.processes.kernel_process import KernelProcessStepContext
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion,AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory

from entities.database import SoftwareUpdate, Product, Subscription
from entities.structured_output import RepeatedCallResult, CauseResult


class DetermineCauseStep(KernelProcessStep):
    """
    Step to determine the cause of a product issue.
    Uses the enhanced database objects with static data loading.
    """
    def __init__(self):
        super().__init__()
        self._system_prompt = """
        Your job is to determine the cause of a product issue. 
        You will be provided with a list of software updates and products, 
        and you must identify the associated software updates and products for the given issue.
        """
        
    @kernel_function
    async def determine_cause(self, context: KernelProcessStepContext, kernel: Kernel, result) -> None:
        """
        Process function to determine the cause of an issue.
        
        Args:
            context: The process step context
            kernel: The semantic kernel instance
            result: The repeated call analysis result
        """        # Get data using the enhanced database objects
        software_updates = SoftwareUpdate.get_all()
        products = Product.get_all()
        
        # Get customer subscriptions
        customer_products = Subscription.find_by_customer_id(result.customer_id)
        
        # Get relevant software updates for the customer's products
        customer_relevant_updates = []
        for customer_product in customer_products:
            # Find software updates for the customer's products
            product_software_updates = [
                s for s in software_updates if s.product_id == customer_product.product_id
            ]
            customer_relevant_updates.extend(product_software_updates)
        
        # Build the user message with detailed context
        user_message = []
        
        user_message.append(f"## Customer ID: {result.customer_id}")
        
        # Add conclusion from previous analysis
        if result.conclusion:
            user_message.append("## Conclusion")
            user_message.append(result.conclusion)
            user_message.append("")
        
        # Add software update information
        if customer_relevant_updates and customer_products:
            user_message.append("## Software updates relevant for issue")
            
            for update in customer_relevant_updates:
                user_message.append(f"Product ID: {update.product_id}")
                user_message.append(f"Update ID: {update.id}")
                user_message.append(f"Update Type: {update.type}")
                user_message.append(f"Update Timestamp: {update.rollout_date.strftime('%Y-%m-%d %H:%M:%S')}")
                user_message.append("")
        
        # Add specific question for the model
        user_message.append("Based on this information, is the current call a repeated call about the same issue and is it due because of software updates?")
        
        # Create the chat completion
        chat_service, settings = kernel.select_ai_service(type=ChatCompletionClientBase)
        assert isinstance(chat_service, ChatCompletionClientBase)  # nosec
        
        # Create a chat history object
        chat_history = ChatHistory()
        chat_history.add_system_message(self._system_prompt)
        chat_history.add_user_message("\n".join(user_message))

        execution_settings = AzureChatPromptExecutionSettings(
            response_format=CauseResult
        )

        # Get model response
        response = await chat_service.get_chat_message_content(chat_history = chat_history,settings=execution_settings)
        
        try:
            # Parse the JSON response
            formatted_response = json.loads(response.content)
            
            # Convert to CauseResult object
            result = CauseResult(
                customer_id=result.customer_id,
                product_id=formatted_response.get("product_id", 0),
                analysis=formatted_response.get("analysis", ""),
                conclusion=formatted_response.get("conclusion", ""),
                is_operations_cause=formatted_response.get("is_operations_cause", False)
            )
            
            print(response)
            
            # Emit appropriate event based on result
            if result.is_operations_cause:
                await context.emit_event("CauseDetermined", data=result)
            else:
                await context.emit_event("NotCauseDetermined")
                
        except json.JSONDecodeError:
            print("Error parsing AI response as JSON")
            await context.emit_event("NotCauseDetermined")
