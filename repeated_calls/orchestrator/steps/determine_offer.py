"""Step for drafting an offer."""

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext

from repeated_calls.orchestrator.agents import offer_agent
from repeated_calls.orchestrator.entities.state import State
from repeated_calls.utils.loggers import Logger

logger = Logger()


class DetermineOfferStep(KernelProcessStep):
    """Step for determining an offer for the customer using a multi-agent system."""

    @kernel_function
    async def offer(
        self,
        state: State,
        context: KernelProcessStepContext,
        kernel: Kernel,
    ) -> None:
        """Process function to determine the cause of a product issue."""

        draft_instructions = """
        Your job is to draft an offer for a customer experiencing a product issue. There are various discounts to offer, but
        it is your job to determine one which is relevant and for which the customer is eligible based on their Customer Lifetime Value (CLV).

        Reason whether the customer should receive the discount and include the following in the advice to a customer service agent:
        - Whether the customer should receive a discount
        - The discount to offer
        - The reasoning behind the discount
        - The issue the customer is experiencing and the request to confirm this with the customer
        - The customer ID and relevant product ID
        """

        review_instructions = """
        Your job is to review the offer drafted by the drafter agent.

        Check the offer based on the following criteria:
        - Is the offer relevant to the customer?
        - Is the offer eligible for the customer based on their Customer Lifetime Value (CLV)?
        - Is the reasoning behind the offer clear and logical?
        - Is the issue the customer is experiencing and the request to confirm this with the customer clear?
        - Is the customer ID and relevant product ID included?

        If the offer is not relevant or eligible, provide feedback to the drafter agent on how to improve the offer.
        If the offer is relevant and eligible, include a sentence with the word 'APPROVED'.
        """

        chat = offer_agent(
            kernel=kernel,
            draft_instructions=draft_instructions,
            reviewer_instructions=review_instructions,
        )

        await chat.add_chat_message(
            message=f"Customer ID: {state.call_event.customer_id}\nReason: {state.cause_result.analysis}"
        )

        async for content in chat.invoke():
            logger.debug(f"{content.name} > {content.content}")

        await context.emit_event("Exit", data=state)
