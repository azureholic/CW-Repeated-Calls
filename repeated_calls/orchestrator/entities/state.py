"""Entity classes for representing message and state objects."""
from datetime import datetime

from pydantic import BaseModel, Field

from repeated_calls.database.schemas import CallEvent, Customer, HistoricCallEvent
from repeated_calls.utils.loggers import Logger

logger = Logger()


class State(BaseModel):
    """State class for the flow."""

    customer_id: int
    sdc: str
    timestamp: datetime
    customer: Customer | None = Field(default=None)
    call_history: list[HistoricCallEvent] = Field(default_factory=list)

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
                self.customer = arg  # self.convert(arg)
            elif isinstance(arg, list) and all(isinstance(i, HistoricCallEvent) for i in arg):
                self.call_history = arg  # self.convert(arg)
            else:
                logger.error(f"Invalid argument '{arg}' type: {type(arg)}")
                raise ValueError("Invalid argument type. Expected Customer or list of HistoricCallEvent.")
