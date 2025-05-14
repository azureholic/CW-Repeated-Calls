"""Entity classes for representing message and state objects."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from repeated_calls.orchestrator.entities.database import CallEvent, Customer, HistoricCallEvent


@dataclass
class IncomingMessage:
    """Incoming message entity class."""

    customer_id: int
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RepeatedCallState:
    """State class for repeated call processing."""

    customer: Optional[Customer] = None
    call_event: Optional[CallEvent] = None
    call_history: List[HistoricCallEvent] = field(default_factory=list)
    is_repeated_call: bool = False
