"""
Structured output classes for AI responses.
"""
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
    analysis: str
    conclusion: str
    is_operations_cause: bool
