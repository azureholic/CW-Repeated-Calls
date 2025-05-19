"""Pre-built Semantic Kernel agent for drafting and reviewing an offer."""

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat

# TODO: Move the group chat agent in offer_agent.py here once we've split that up


def get_agent(kernel: Kernel, draft_instructions: str, reviewer_instructions: str) -> AgentGroupChat:
    """Agent collaboration chat for interactively drafting and reviewing an offer."""
    raise NotImplementedError("This function is not implemented yet. Use cause agent for now.")
