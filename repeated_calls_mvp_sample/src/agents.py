#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments

from src.models import (
    RepeatCallAnalysis,
    FaultAnalysis,
    CompensationRecommendation,
    CompensationReview,
    CallAgentSummary,
)


# Create kernels with different service IDs for each agent
def create_kernel_with_service(service_id):
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


# Define termination strategy for the recommendation review
class ApprovalTerminationStrategy(TerminationStrategy):
    """Terminate when the review is complete with either approval or rejection."""

    async def should_agent_terminate(self, agent, history):
        if not history:
            return False
        last_message = history[-1].content.lower()
        return "approved" in last_message or "rejected" in last_message


# Create the repeat call detection agent
def create_repeat_call_detector():
    repeat_settings = AzureChatPromptExecutionSettings()
    repeat_settings.response_format = RepeatCallAnalysis

    repeat_agent = ChatCompletionAgent(
        kernel=create_kernel_with_service("repeat-detector"),
        name="RepeatCallDetector",
        instructions="""
        You are an expert at analyzing customer call history to determine if a call is a repeat call.
        A repeat call is defined as multiple calls from the same customer about the same issue within a 7-day period.
        Analyze the call data and determine if the current call is a repeat call.

        Important: Include detailed reasoning about why you classified this as a repeat call or not.
        Consider factors like:
        - Is this a different product than previous calls?
        - Is this a new issue versus previous calls?
        - How similar are the call_reason and details between calls?
        - Is the time period within 7 days?

        Each call contains:
        - call_id: A unique identifier for the call
        - customer_id: The ID of the customer
        - timestamp: When the call occurred
        - call_reason: The reason for the call as stated by the customer
        - details: Additional details or notes about the call (may be empty for current calls)
        - resolved: Whether the call was resolved

        Provide your analysis in the requested structured format.
        """,
        arguments=KernelArguments(settings=repeat_settings),
    )
    return repeat_agent


# Create the fault determination agent
def create_fault_analyzer():
    fault_settings = AzureChatPromptExecutionSettings()
    fault_settings.response_format = FaultAnalysis

    fault_agent = ChatCompletionAgent(
        kernel=create_kernel_with_service("fault-analyzer"),
        name="FaultAnalyzer",
        instructions="""
        You are an expert at determining whether reported issues are the company's fault.
        Analyze the call data, customer information, and operational disruptions to determine if
        the recurring issue is due to the company's fault.

        Important: Include detailed reasoning about why you classified this as our fault or not.
        Consider factors like:
        - Are there matching operational disruptions?
        - Is the customer using the product as intended?
        - Is there an indication of user error?
        - Did we make promises about resolution that weren't met?
        - Is this a known issue with the product?

        Each call contains:
        - call_id: A unique identifier for the call
        - customer_id: The ID of the customer
        - timestamp: When the call occurred
        - call_reason: The reason for the call as stated by the customer
        - details: Additional details or notes about the call (may be empty for current calls)
        - resolved: Whether the call was resolved

        Provide your analysis in the requested structured format.
        """,
        arguments=KernelArguments(settings=fault_settings),
    )
    return fault_agent


# Create the recommendation agent
def create_compensation_recommender():
    recommend_settings = AzureChatPromptExecutionSettings()
    recommend_settings.response_format = CompensationRecommendation

    recommend_agent = ChatCompletionAgent(
        kernel=create_kernel_with_service("recommender"),
        name="CompensationRecommender",
        instructions="""
        You are an expert at determining appropriate compensation for customers experiencing recurring issues.
        Consider the customer's customer_lifetime_value (Low, Med, High), previous compensations, and the nature of the issue.
        For customers with High CLV, be more generous to ensure they feel valued.
        Provide your recommendation in the requested structured format.
        """,
        arguments=KernelArguments(settings=recommend_settings),
    )
    return recommend_agent


# Create the reviewer agent
def create_compensation_reviewer():
    review_settings = AzureChatPromptExecutionSettings()
    review_settings.response_format = CompensationReview

    reviewer_agent = ChatCompletionAgent(
        kernel=create_kernel_with_service("reviewer"),
        name="CompensationReviewer",
        instructions="""
        You are a supervisor responsible for reviewing compensation recommendations.
        Your job is to ensure that recommendations are fair, consistent with company policy, and appropriate for the situation.
        You will start the conversation by reviewing the recommendation provided.
        Review the recommendation and either approve it or suggest adjustments.
        Consider company costs and the precedent set by the compensation.
        Provide your review in the requested structured format.
        If you approve, clearly state 'Approved' in your comments.
        If you reject, clearly state 'Rejected' in your comments.
        """,
        arguments=KernelArguments(settings=review_settings),
    )
    return reviewer_agent


# Create the recommendation publisher for call agent consumption
def create_recommendation_publisher():
    publisher_settings = AzureChatPromptExecutionSettings()
    publisher_settings.response_format = CallAgentSummary

    publisher_agent = ChatCompletionAgent(
        kernel=create_kernel_with_service("publisher"),
        name="RecommendationPublisher",
        instructions="""
        You are an expert at summarizing complex information for call center agents who need quick, actionable information.
        Your job is to create a clear, concise summary that a call agent can easily read and understand while on a live call with a customer.
        The summary should start with a one-sentence recommendation that captures the essence of what the agent should tell or offer the customer.
        Follow this with supporting details organized in a way that's easy to scan during an active call.
        Provide talking points that the agent can use verbatim when speaking with the customer.
        Ensure your output follows the required structured format.
        """,
        arguments=KernelArguments(settings=publisher_settings),
    )
    return publisher_agent


# Create a standard recommender agent for the group chat
def create_group_chat_recommender():
    recommender_agent = ChatCompletionAgent(
        kernel=create_kernel_with_service("recommender"),
        name="CompensationRecommender",
        instructions="""
        You are an expert at determining appropriate compensation for customers experiencing recurring issues.
        You have already made your initial recommendation. Wait for the reviewer to provide their initial feedback.
        Then address any concerns or suggestions from the reviewer and either defend your recommendation or refine it.
        Do not start the conversation - respond only after the reviewer has provided their assessment.
        Consider the reviewer's feedback carefully and respond thoughtfully.
        Aim to come to a mutually agreeable compensation solution.
        """,
    )
    return recommender_agent
