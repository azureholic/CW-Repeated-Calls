"""Pre-built Semantic Kernel agent creating an offer recommendation."""

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments

# TODO: Change this agent to only create an offer and move the review/draft groupchat logic to a different agent
# in draft_review_agent.py


class ApprovalTerminationStrategy(TerminationStrategy):
    """Termination strategy for the agent group chat."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate based on the last message in the chat history."""
        return "approved" in history[-1].content.lower()


def get_agent(kernel: Kernel, draft_instructions: str, reviewer_instructions: str) -> AgentGroupChat:
    """Agent collaboration chat for interactively drafting and reviewing an offer."""
    drafter = ChatCompletionAgent(
        name="Drafter",
        instructions=draft_instructions,
        kernel=kernel,
        arguments=KernelArguments(
            settings=AzureChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    auto_invoke=True,
                    filters={"included_plugins": ["CustomerDataPlugin"]},
                ),
                temperature=0.0,
                seed=1337,
            )
        ),
    )

    reviewer = ChatCompletionAgent(
        name="Reviewer",
        instructions=reviewer_instructions,
        kernel=kernel,
        arguments=KernelArguments(
            settings=AzureChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    auto_invoke=True,
                    filters={"included_plugins": ["CustomerDataPlugin"]},
                ),
                temperature=0.0,
                seed=1337,
            )
        ),
    )

    return AgentGroupChat(
        agents=[drafter, reviewer],
        termination_strategy=ApprovalTerminationStrategy(agents=[reviewer], maximum_iterations=4),
    )
