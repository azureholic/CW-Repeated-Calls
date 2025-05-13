"""Module for the RepeatCallerPrompt class."""

from datetime import datetime

from repeated_calls.orchestrator.entities.database import CallEvent, Customer, HistoricCallEvent
from repeated_calls.orchestrator.entities.states import RepeatedCallState
from repeated_calls.prompt_engineering.prompt_template import PromptTemplatePair


class RepeatCallerPrompt(PromptTemplatePair):
    """Prompt class for determining repeated calls, managing both system and user prompts."""

    def __init__(self) -> None:
        """Initialize the RepeatCallerPrompt with specific templates."""
        super().__init__(user_template_name="repeat_caller_user.j2", system_template_name="repeat_caller_system.j2")

    def from_callstate(self, callstate: RepeatedCallState) -> "RepeatCallerPrompt":
        """Create a RepeatCallerPrompt instance from a RepeatedCallState object."""
        # TODO: Figure out what is up with callstate

        # Customer info
        self.set_user_variable(
            "customer",
            {
                "id": callstate.customer.id,
                "name": callstate.customer.name,
                "clv": callstate.customer.clv,
                "relation_start_date": callstate.customer.relation_start_date.strftime("%Y-%m-%d"),
            },
        )

        # Current call info
        self.set_user_variable(
            "call_event",
            {
                "id": callstate.call_event.id,
                "sdc": callstate.call_event.sdc,
                "time_stamp": callstate.call_event.time_stamp.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        # Call history
        history_entries: list[dict[str, str]] = []
        for call in sorted(callstate.call_history, key=lambda h: h.start_time, reverse=True):
            duration = (call.end_time - call.start_time).total_seconds() / 60
            total_hours_since = (callstate.call_event.time_stamp - call.end_time).total_seconds() / 3600
            days_since = int(total_hours_since // 24)
            hours_since = total_hours_since % 24

            history_entries.append(
                {
                    "start_time": call.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": call.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "sdc": call.sdc,
                    "call_summary": call.call_summary,
                    "duration_minutes": f"{duration:.1f}",
                    "days_since": f"{days_since:.1f}",
                    "remaining_hours_since": f"{hours_since:.1f}",
                }
            )
        self.set_user_variable("call_history", history_entries)

        return self


if __name__ == "__main__":

    test_callstate = RepeatedCallState(
        customer=Customer(
            id=12345, name="Jane Doe", clv=9800, relation_start_date=datetime.strptime("2019-03-15", "%Y-%m-%d")
        ),
        call_event=CallEvent(
            id=1,
            customer_id=12345,
            sdc="Call Description",
            time_stamp=datetime.strptime("2023-10-01 12:00:00", "%Y-%m-%d %H:%M:%S"),
        ),
        call_history=[
            HistoricCallEvent(
                id=1,
                customer_id=12345,
                sdc="Previous Call",
                start_time=datetime.strptime("2023-09-01 10:00:00", "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime("2023-09-01 11:00:00", "%Y-%m-%d %H:%M:%S"),
                call_summary="Summary of previous call",
            ),
            HistoricCallEvent(
                id=2,
                customer_id=12345,
                sdc="Another Call",
                start_time=datetime.strptime("2023-08-01 10:00:00", "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime("2023-08-01 11:00:00", "%Y-%m-%d %H:%M:%S"),
                call_summary="Summary of another call",
            ),
        ],
    )

    rc_prompt = RepeatCallerPrompt().from_callstate(test_callstate)

    system_text = rc_prompt.get_system_prompt()
    user_text = rc_prompt.get_user_prompt()

    print("SYSTEM PROMPT:\n", system_text, "\n", sep="")
    print("USER PROMPT:\n", user_text, sep="")
