"""Step for drafting an offer."""
import json
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents.offer_agent import get_agent_response
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import OfferResult
from repeated_calls.prompt_engineering.prompts import RecommendationPrompt
from repeated_calls.utils.loggers import Logger
from semantic_kernel.agents import AzureAIAgent,AzureAIAgentSettings,AzureAIAgentThread
logger = Logger()


class DetermineRecommendationStep(KernelProcessStep):
    """Step for determining a recommendation for the CS employee using a multi-agent system."""

    @kernel_function
    async def recommend(
        self,
        state: State,
        context: KernelProcessStepContext       
    ) -> None:
        """Process function to determine the cause of a product issue."""
        prompts = RecommendationPrompt(state)

        # Hacky way to split the system prompt into two parts
        system_prompts = prompts.get_system_prompt().split("===")

        agent_response = await get_agent_response(
            draft_instructions=system_prompts[0],
            reviewer_instructions=system_prompts[1],
            user_prompt=prompts.get_user_prompt(),
            thread_id=state.thread_id
        )

        res = OfferResult(**json.loads(agent_response.content))
        logger.info(
            f">> OFFER AGENT - {res.advice}"
        )
        
        state.update(res)
        await context.emit_event("Exit", data=state)
