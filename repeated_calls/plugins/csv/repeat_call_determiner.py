from semantic_kernel.functions import kernel_function
from semantic_kernel.contents.chat_history import ChatHistory
import sys

class RepeatCallDeterminer:
    """
    A plugin to determine if a customer call is a repeat call based on chat history.
    """

    def __init__(self, kernel, logger, chat_completion, execution_settings):
        self.kernel = kernel
        self.logger = logger
        self.chat_completion = chat_completion
        self.execution_settings = execution_settings

    @kernel_function(name="determine_repeat_call", description="Determine if the current call is a repeat call.")
    async def determine_repeat_call(self, chat_history: ChatHistory):
        """
        Determine if the call is a repeat call. If it is, update the chat history and return True.
        If not, exit the application.
        """
        try:
            self.logger.info("Determining if the call is a repeat based on chat history...")
            prompt = f"""
            Chat History:
            {chat_history.to_string()}

            Determine if this chat history indicates a repeat call. 
            Respond with 'Yes' if it is a repeat call, otherwise respond with 'No'.
            """
            result = await self.chat_completion.get_chat_message_content(
                chat_history=ChatHistory([prompt]),
                settings=self.execution_settings,
                kernel=self.kernel,
            )
            is_repeat = result.strip().lower() == "yes"

            if is_repeat:
                self.logger.info("This is a repeat call. Adding information to chat history...")
                chat_history.add_message("System", "This call is identified as a repeat call.")
                return True
            else:
                self.logger.info("This is not a repeat call. Exiting the application.")
                print("This is not a repeat call. Exiting the application.")
                sys.exit(0)
        except Exception as e:
            self.logger.error(f"Error in RepeatCallDeterminer: {e}")
            return False
