"""Step for drafting an offer."""

from semantic_kernel import Kernel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents.offer_agent import get_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.prompt_engineering.prompts import RecommendationPrompt
from repeated_calls.utils.loggers import Logger
<<<<<<< HEAD
from repeated_calls.utils.conversation_saver import save_conversation
=======
# from repeated_calls.utils.conversation_saver import save_conversation
from repeated_calls.orchestrator.entities.structured_output import CauseResult, OfferResult, RepeatedCallResult


>>>>>>> d1e2eef (added the drafter reviewer conversation to the state)

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
        drafter_reviewer_conv = []
        
        await chat.add_chat_message(
            message=prompts.get_prompt("user"),
        )

        async for content in chat.invoke():
            logger.debug(f">> {content.name.upper()}: {content.content}")
            # Add the response to our chat history
            responses.append(f"{content.name}: {content.content}")
            drafter_reviewer_conv.append(f">> {content.name.upper()}: {content.content}")


        res_conversation = OfferResult(customer_id = state.call_event.customer_id, 
                             product_id = state.cause_result.product_id, 
                             conversation = drafter_reviewer_conv)
        
        state.update(res_conversation)
            
        await context.emit_event("Exit", data=state)


        State()