"""Step for drafting an offer."""

from semantic_kernel import Kernel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents.offer_agent import get_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.prompt_engineering.prompts import RecommendationPrompt
from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.conversation_saver import save_conversation

logger = Logger()


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

        chat = get_agent(
            kernel=kernel,
            draft_instructions=prompts.get_prompt("system_recommendation"),
            reviewer_instructions=prompts.get_prompt("system_reviewer"),
        )

        # Create a chat history for logging
        chat_history = ChatHistory()
        chat_history.add_system_message(prompts.get_system_prompt())
        chat_history.add_user_message(prompts.get_user_prompt())

        # Store all responses
        responses = []

        await chat.add_chat_message(
            message=prompts.get_prompt("user"),
        )

        async for content in chat.invoke():
            logger.debug(f">> {content.name.upper()}: {content.content}")
            # Add the response to our chat history
            responses.append(f"{content.name}: {content.content}")

        # Add all responses as a single assistant message
        chat_history.add_assistant_message("\n\n".join(responses))

        # Save conversation to all required locations
        agent_name = "RecommendationProvider"
        save_results = save_conversation(
            chat_history=chat_history,
            agent_name=agent_name,
            row_id=state.row_id,
            run_timestamp=state.run_timestamp,
        )
        logger.info(f"Saved conversation to {save_results['individual_file']}")
        logger.info(f"Appended to conversations file: {save_results['conversations_file']}")
        logger.info(f"Appended to run log: {save_results['run_log_file']}")

        await context.emit_event("Exit", data=state)
