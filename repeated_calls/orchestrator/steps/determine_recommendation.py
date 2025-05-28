"""Step for drafting an offer."""

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents.offer_agent import get_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import OfferResult
from repeated_calls.prompt_engineering.prompts import RecommendationPrompt
from repeated_calls.utils.loggers import Logger

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

        # Store all responses
        responses = []

        await chat.add_chat_message(
            message=prompts.get_prompt("user"),
        )

        conversation = []
        async for content in chat.invoke():
            c = f">> {content.name.upper()}: {content.content}"
            logger.debug(c)
            conversation.append(c)

        # Update state
        state.update(
            OfferResult(
                customer_id=state.cause_result.customer_id,
                product_id=state.cause_result.product_id,
                conversation=conversation,
            )
        )

        
        await context.emit_event("Exit", data=state)
