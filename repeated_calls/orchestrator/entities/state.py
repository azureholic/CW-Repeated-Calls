"""Entity classes for representing message and state objects."""
from datetime import datetime

from pydantic import BaseModel, Field

from repeated_calls.database.schemas import CallEvent, Customer, HistoricCallEvent
from repeated_calls.orchestrator.entities.structured_output import CauseResult, OfferResult, RepeatedCallResult
from repeated_calls.utils.loggers import Logger

logger = Logger()


class State(BaseModel):
    """State class for the flow."""

    customer_id: int
    sdc: str
    timestamp: datetime
    customer: Customer | None = Field(default=None)
    call_history: list[HistoricCallEvent] = Field(default_factory=list)
    repeated_call_result: RepeatedCallResult | None = Field(default=None)
    cause_result: CauseResult | None = Field(default=None)
    offer_result: OfferResult | None = Field(default=None)

    @classmethod
    def from_call_event(cls, call_event: CallEvent) -> "State":
        """Create a State instance from a CallEvent object."""
        return cls(
            customer_id=call_event.customer_id,
            sdc=call_event.sdc,
            timestamp=call_event.timestamp,
        )

    def update(self, *args) -> None:
        """Update the state with customer data or call history."""
        for arg in args:
            if isinstance(arg, Customer):
                self.customer = arg
            elif isinstance(arg, list) and all(isinstance(i, HistoricCallEvent) for i in arg):
                self.call_history = arg
            elif isinstance(arg, RepeatedCallResult):
                self.repeated_call_result = arg
            elif isinstance(arg, CauseResult):
                self.cause_result = arg
            elif isinstance(arg, OfferResult):
                self.offer_result = arg
            else:
                logger.error(f"Invalid argument '{arg}' type: {type(arg)}")
                raise ValueError("Invalid argument type. Expected Customer or list of HistoricCallEvent.")
