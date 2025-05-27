"""Step for determining the cause of a product issue."""

import json

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents.cause_agent import get_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import CauseResult
from repeated_calls.prompt_engineering.prompts import CausePrompt
from repeated_calls.utils.loggers import Logger
from repeated_calls.utils.conversation_saver import save_conversation

logger = Logger()


class DetermineCauseStep(KernelProcessStep):
    """Step for determining the cause of a product issue.

    Uses a variety of plugins and agents to determine the cause of a product issue.
    """

    @kernel_function
    async def cause(
        self,
        state: State,
        context: KernelProcessStepContext,
        kernel: Kernel,
    ) -> None:
        """Process function to determine the cause of a product issue."""
        prompts = CausePrompt(state)

        agent = get_agent(kernel=kernel, instructions=prompts.get_prompt("system"))

        response = await agent.get_response(
            messages=prompts.get_prompt("user"),
        )

        # Parse the response and update the state
        res = CauseResult(**json.loads(response.content.content))
        logger.debug(
            f">> CAUSE AGENT - Product ID: {res.product_id}. Analysis: {res.analysis}. Conclusion: {res.conclusion}"
        )
        state.update(res)

        if res.is_relevant:
            # Send event to next step
            await context.emit_event(
                "IsRelevant",
                data=state,
            )
        else:
            # Send event to exit step
            await context.emit_event(
                "IsNotRelevant",
                data=state,
            )