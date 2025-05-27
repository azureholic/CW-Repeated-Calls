"""Step for drafting an offer."""

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents.offer_agent import get_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.prompt_engineering.prompts import RecommendationPrompt
from repeated_calls.utils.loggers import Logger
import frontend.utils as us
from repeated_calls.streaming.settings import StreamingSettings


logger = Logger()

config = StreamingSettings(queue = 'agent_output_messages')
client = us.get_sb_client(config.connection_string)
messages = []

class DetermineRecommendationStep(KernelProcessStep):
    """Step for determining a recommendation for the CS employee using a multi-agent system."""

    @kernel_function
    async def recommend(
        self,
        state: State,
        context: KernelProcessStepContext,
        kernel: Kernel,
    ) -> None:
        """Process function to determine the cause of a product issue."""
        prompts = RecommendationPrompt(state)

        # Hacky way to split the system prompt into two parts
        system_prompts = prompts.get_system_prompt().split("===")

        chat = get_agent(
            kernel=kernel,
            draft_instructions=system_prompts[0],
            reviewer_instructions=system_prompts[1],
        )

        await chat.add_chat_message(
            message=prompts.get_user_prompt(),
        )


        async for content in chat.invoke():
            msg = f">> {content.name.upper()}: {content.content}"
            await us._send_async(msg, client, config.queue)
            # messages.append(msg)
            logger.debug(f">> {content.name.upper()}: {content.content}")

        # # Sending messages to the servicebus
        # total_message = us.create_one_message(messages)

        await context.emit_event("Exit", data=state)

