"""Exit step for the process framework."""
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep
from repeated_calls.utils.loggers import Logger
from repeated_calls.streaming.settings import StreamingSettings
from frontend import utils as us


config = StreamingSettings(queue = 'agent_output_messages')


logger = Logger()


class ExitStep(KernelProcessStep):
    """Step to exit the process."""

    @kernel_function
    def exit(self) -> None:
        """Process function to exit the process."""
        msg_1 = ">> EXIT: Ending the process."
        logger.debug(msg_1)

        messages = [msg_1]
        total_message = us.create_one_message(messages)
        client = us.get_sb_client(config.connection_string)
        us.send_servicebus_msg(total_message, client, config.queue)
