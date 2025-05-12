from semantic_kernel.functions import kernel_function
from semantic_kernel.contents.chat_history import ChatHistory

class RecommendationFormulator:
    """
    A plugin to formulate actionable recommendations for customers based on repeat call status,
    operational data, and customer data.
    """

    def __init__(self, logger, chat_completion, execution_settings):
        self.logger = logger
        self.chat_completion = chat_completion
        self.execution_settings = execution_settings

    @kernel_function(name="formulate_recommendation", description="Formulate a recommendation for the customer.")
    async def formulate_recommendation(self, repeat_call: bool, operational_data: list, customer_data: dict):
        try:
            self.logger.info("Formulating recommendation for the customer...")
            prompt = f"""
            Repeat Call: {'Yes' if repeat_call else 'No'}
            Operational Data: {', '.join(operational_data) if operational_data else 'None'}
            Customer Data: {customer_data}

            Based on the above information, provide a detailed and actionable recommendation for the customer.
            """
            result = await self.chat_completion.get_chat_message_content(
                chat_history=ChatHistory([prompt]),
                settings=self.execution_settings,
            )
            self.logger.info("Successfully formulated recommendation for the customer.")
            return result.strip()
        except Exception as e:
            self.logger.error(f"Error formulating recommendation: {e}")
            return "Unable to generate a recommendation at this time."
