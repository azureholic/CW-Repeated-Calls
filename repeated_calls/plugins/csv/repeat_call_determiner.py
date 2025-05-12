from semantic_kernel.functions import kernel_function
from semantic_kernel.contents.chat_history import ChatHistory

class RepeatCallDeterminer:
    """
    A plugin to determine if a customer call is a repeat call based on historical call summaries
    and the current call reason.
    """

    def __init__(self, kernel, logger, chat_completion, execution_settings):
        self.kernel = kernel
        self.logger = logger
        self.chat_completion = chat_completion
        self.execution_settings = execution_settings

    @kernel_function(name="determine_repeat_call", description="Determine if the current call is a repeat call.")
    async def determine_repeat_call(self, historical_summaries: list, call_reason: str):
        try:
            self.logger.info("Determining if the call is a repeat...")
            prompt = f"""
            Historical Call Summaries:
            {', '.join(historical_summaries)}

            Current Call Reason:
            {call_reason}

            Determine if the current call reason is related to any of the historical call summaries. 
            Respond with 'Yes' if it is related, otherwise respond with 'No'.
            """
            result = await self.chat_completion.get_chat_message_content(
                chat_history=ChatHistory([prompt]),
                settings=self.execution_settings,
                kernel=self.kernel,
            )
            return result.strip().lower() == "yes"
        except Exception as e:
            self.logger.error(f"Error in RepeatCallDeterminer: {e}")
            return False
