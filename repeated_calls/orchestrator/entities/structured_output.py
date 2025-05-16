"""Structured output classes for AI responses."""
from pydantic import BaseModel, Field


class RepeatedCallResult(BaseModel):
    """Result class for repeated call analysis."""

    customer_id: int
    analysis: str = Field(
        description="A description of your reasoning to determine if the issue of the current call is the same as the issue of a call in the last month."
    )
    conclusion: str = Field(
        description="The conclusion of the analysis, indicating whether the call is a repeated call or not."
    )
    is_repeated_call: bool = Field(description="A boolean indicating whether the call is a repeated call.")


class CauseResult(BaseModel):
    """Result class for cause determination analysis."""

    customer_id: int
    product_id: int
    analysis: str = Field(
        description="A description of your reasoning to determine if one of our systems could be the cause of issue that this repeat call is assumed to be about."
    )
    conclusion: str = Field(
        description="The conclusion of the analysis, indicating whether one of our systems is the cause of the issue."
    )
    is_relevant: bool = Field(description="A boolean indicating whether one of our systems is the cause of the issue.")


class OfferResult(BaseModel):
    """Result class for offer."""

    customer_id: int
    product_id: int
    advice: str = Field(
        description="The recommendation you give to the customer service employee on what offer to make to the customer."
    )
