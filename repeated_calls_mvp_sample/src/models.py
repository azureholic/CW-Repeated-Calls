#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# Define the structured output models
class RepeatCallAnalysis(BaseModel):
    is_repeat_call: bool = Field(
        description="Whether this is a repeat call from the same customer about the same issue"
    )
    related_call_ids: List[str] = Field(
        default_factory=list, description="IDs of related previous calls"
    )
    days_since_first_call: Optional[int] = Field(
        default=None, description="Days since the first related call"
    )
    issue_summary: str = Field(description="Brief summary of the recurring issue")
    reasoning: str = Field(
        description="Explanation of why this is or is not considered a repeat call"
    )


class FaultAnalysis(BaseModel):
    is_our_fault: bool = Field(description="Whether the issue is the company's fault")
    fault_reason: Optional[str] = Field(
        default=None, description="Reason why it's the company's fault, if applicable"
    )
    matching_disruption_ids: List[str] = Field(
        default_factory=list, description="IDs of any matching operational disruptions"
    )
    recommended_action: str = Field(description="Recommended action to resolve the issue")
    reasoning: str = Field(
        description="Detailed explanation of why this issue is or is not our fault"
    )


class CompensationRecommendation(BaseModel):
    recommended_compensation_type: str = Field(
        description="Type of compensation (e.g., Service Credit, Free Month, Discount)"
    )
    amount: float = Field(description="Monetary value or percentage of the compensation")
    duration: Optional[str] = Field(
        default=None, description="Duration of the compensation if applicable"
    )
    justification: str = Field(description="Justification for the compensation amount and type")
    customer_value_consideration: str = Field(
        description="How customer value was considered in this recommendation"
    )


class CompensationReview(BaseModel):
    approved: bool = Field(description="Whether the compensation is approved")
    adjusted_amount: Optional[float] = Field(
        default=None,
        description="Adjusted compensation amount if different from recommended",
    )
    adjusted_type: Optional[str] = Field(
        default=None,
        description="Adjusted compensation type if different from recommended",
    )
    comments: str = Field(description="Comments explaining the review decision")


class CallAgentSummary(BaseModel):
    one_sentence_recommendation: str = Field(
        description="A concise one-sentence recommendation that a call agent can quickly read while on a call"
    )
    compensation_details: str = Field(description="Brief details about the approved compensation")
    technical_resolution: str = Field(
        description="What technical steps should be taken to resolve the issue"
    )
    customer_context: str = Field(
        description="Important context about the customer and their history with this issue"
    )
    talking_points: List[str] = Field(
        description="Key talking points for the call agent to communicate to the customer",
        default_factory=list,
    )
    next_steps: str = Field(description="What the call agent should do after this call")


class ConversationHistory(BaseModel):
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Messages exchanged during the recommendation review",
    )


class FinalRecommendation(BaseModel):
    customer_id: str
    call_id: str
    timestamp: str
    repeat_call_analysis: RepeatCallAnalysis
    fault_analysis: Optional[FaultAnalysis] = None
    compensation_recommendation: Optional[CompensationRecommendation] = None
    compensation_review: Optional[CompensationReview] = None
    call_agent_summary: Optional[CallAgentSummary] = None
    conversation_history: Optional[ConversationHistory] = None
