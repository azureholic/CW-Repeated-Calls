"""GetCustomerData step for the process framework."""

import json
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from repeated_calls.orchestrator.agents.repeated_call_agent import get_agent
from repeated_calls.database.schemas import Customer, HistoricCallEvent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import RepeatedCallResult
from repeated_calls.prompt_engineering.prompts import RepeatCallerPrompt
from repeated_calls.utils.loggers import Logger

logger = Logger()


class DetermineRepeatedCallStep(KernelProcessStep):
    """Step to retrieve customer data and context for process execution.

    Uses the enhanced database objects with static data loading.
    """

    @kernel_function
    async def repeated_call(
        self,
        state: State,
        context: KernelProcessStepContext,
        kernel: Annotated[Kernel | None, "The kernel", {"include_in_function_choices": False}], # this is important to avoid json serializing errors (https://github.com/microsoft/semantic-kernel/issues/12067)
        
    ) -> None:
        """Process function to retrieve customer data and call events using the enhanced database objects."""

        prompts = RepeatCallerPrompt(state)
        agent = get_agent(kernel=kernel, instructions=prompts.get_system_prompt())
        response = await agent.get_response()
        
        logger.debug(f"RepeatedCall response: {response}")

        state.update(RepeatedCallResult(**json.loads(str(response.content))))

        # Emit event to continue process flow
        if state.repeated_call_result.is_repeated_call:
            await context.emit_event("IsRepeatedCall", data=state)
        else:
            await context.emit_event("IsNotRepeatedCall", data=state)
