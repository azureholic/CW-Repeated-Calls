"""Step for determining the cause of a product issue."""

import json

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents import cause_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.orchestrator.entities.structured_output import CauseResult
from repeated_calls.prompt_engineering.prompts import CausePrompt
from repeated_calls.utils.loggers import Logger

logger = Logger()


# class CauseDetermination(BaseModel):
#     """Determination of whether a customer complaint is relevant."""

#     is_relevant: bool = Field(..., description="Whether the company is at fault and a fix is needed.")
#     explanation: str = Field(..., description="Explanation of the relevancy determination.")


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
        # Check if incoming_message is already the correct type
        # this code below is to 'fix' semantic_kernel.exceptions.kernel_exceptions.KernelException:
        # The function get_call_event on step GetCustomerDataStep has more than one parameter, so a
        # parameter name must be provided.

        prompts = CausePrompt(state)
        # logger.debug(f"System prompt:\n{prompts.get_system_prompt()}")
        # logger.debug(f"User prompt:\n{prompts.get_user_prompt()}")

        agent = cause_agent(kernel=kernel)

        response = await agent.get_response(
            messages=prompts.get_user_prompt(),
        )
        logger.debug(f"Cause determination response: {response}")

        # Classify whether the call is a repeated call with an LLM
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
        chat_settings = AzureChatPromptExecutionSettings(response_format=CauseResult, temperature=0.0)

        # Prepare the chat interaction
        chat_history = ChatHistory()
        chat_history.add_system_message(prompts.get_system_prompt())
        chat_history.add_user_message(prompts.get_user_prompt())
        chat_history.add_user_message(str(response))

        res = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=chat_settings,
        )
        chat_history.add_assistant_message(res.content)
        logger.debug(f"Cause determination response: {res.content}")

        state.update(CauseResult(**json.loads(res.content)))

        if json.loads(res.content)["is_relevant"]:
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
