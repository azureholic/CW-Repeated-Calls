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

        # logger.debug(f"System prompt:\n{prompts.get_system_prompt()}")
        # logger.debug(f"User prompt:\n{prompts.get_user_prompt()}")

        agent = get_agent(kernel=kernel, instructions=prompts.get_system_prompt())

        response = await agent.get_response(
            messages=prompts.get_user_prompt(),
        )

        # Parse the response and update the state
        res = CauseResult(**json.loads(response.content.content))
        logger.debug(
            f">> CAUSE AGENT - Product ID: {res.product_id}. Analysis: {res.analysis}. Conclusion: {res.conclusion}"
        )
        state.update(res)
        logger.debug(f"Cause determination response: {response}")

        # Classify whether the call is a repeated call with an LLM
        chat_service = kernel.get_service(type=ChatCompletionClientBase)
        chat_settings = AzureChatPromptExecutionSettings(
            response_format=CauseResult, temperature=0.0
        )

        # Prepare the chat interaction
        chat_history = ChatHistory()
        chat_history.add_system_message(prompts.get_system_prompt())
        chat_history.add_user_message(prompts.get_user_prompt())
        chat_history.add_user_message(str(response))

        chat_response = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=chat_settings,
        )
        chat_history.add_assistant_message(chat_response.content)
        logger.debug(f"Cause determination response: {chat_response.content}")

        # Save conversation to all required locations
        agent_name = "CauseDeterminer"
        save_results = save_conversation(
            chat_history=chat_history,
            agent_name=agent_name,
            row_id=state.row_id,
            run_timestamp=state.run_timestamp,
        )
        logger.info(f"Saved conversation to {save_results['individual_file']}")
        logger.info(f"Appended to conversations file: {save_results['conversations_file']}")
        logger.info(f"Appended to run log: {save_results['run_log_file']}")

        state.update(CauseResult(**json.loads(chat_response.content)))

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
