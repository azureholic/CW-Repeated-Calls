"""Structured output classes for AI responses."""
from dataclasses import dataclass


@dataclass
class RepeatedCallResult:
    """Result class for repeated call analysis."""

    customer_id: int
    analysis: str
    conclusion: str
    is_repeated_call: bool


@dataclass
class CauseResult:
    """Result class for cause determination analysis."""

    customer_id: int
    product_id: int
    analysis: str
    conclusion: str
    is_operations_cause: bool


@dataclass
class OfferResult:
    """Result class for offer."""

    customer_id: int
    product_id: int
    advice: str
