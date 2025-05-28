"""Test script to send a selected call event from data folder to the Service Bus queue."""

import asyncio
import csv
import json
import os
import sys

from azure.servicebus.aio import ServiceBusClient

from repeated_calls.streaming.settings import StreamingSettings

# Add the project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def load_call_events() -> dict[int, dict]:
    """Load call events from the CSV file."""
    data_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), "data")
    csv_path = os.path.join(data_path, "call_event.csv")

    call_events = {}
    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            call_events[int(row["id"])] = {
                "id": int(row["id"]),
                "customer_id": int(row["customer_id"]),
                "sdc": row["sdc"],
                "timestamp": row["timestamp"],
            }

    return call_events


def display_call_events(call_events: dict[int, dict]) -> None:
    """Display available call events."""
    print("\nAvailable call events:")
    print("-" * 80)
    for id, event in call_events.items():
        print(f"{id}. Customer ID: {event['customer_id']}")
        print(f"   Description: {event['sdc']}")
        print(f"   Timestamp: {event['timestamp']}")
        print()
    print("-" * 80)


def get_user_choice(items: int, prompt: str) -> int:
    """Get user choice from console."""
    while True:
        try:
            choice = int(input(prompt))
            if 1 <= choice <= items:
                return choice
            print(f"Please enter a number between 1 and {items}.")
        except ValueError:
            print("Please enter a valid number.")


async def send_test_message(call_event: dict) -> None:
    """Send a test message to the Service Bus queue."""
    settings = StreamingSettings()
    print(f"Sending test message to queue: {settings.calls_queue}")

    # Ensure timestamp is ISO format
    if isinstance(call_event["timestamp"], str):
        # Keep original timestamp if it's a string (from CSV)
        timestamp_iso = call_event["timestamp"]
    else:
        # Convert to ISO format if it's a datetime object
        timestamp_iso = call_event["timestamp"].isoformat()

    # Convert to JSON-serializable dict
    message_dict = {
        "id": call_event["id"],
        "customer_id": call_event["customer_id"],
        "sdc": call_event["sdc"],
        "timestamp": timestamp_iso,
    }

    # Serialize to JSON
    message_json = json.dumps(message_dict)
    try:
        # Send to Service Bus
        async with ServiceBusClient.from_connection_string(
            conn_str=settings.connection_string, logging_enable=True
        ) as client:
            # Create a sender for the calls queue
            async with client.get_queue_sender(queue_name=settings.calls_queue) as sender:
                print(f"Sending message: {message_json}")
                # Use send_messages instead of send_message (for older SDK versions)
                from azure.servicebus import ServiceBusMessage

                message = ServiceBusMessage(message_json)
                await sender.send_messages(message)

        print("Test message sent successfully!")

    except Exception as e:
        print(f"Error sending message: {str(e)}")


async def main() -> None:
    """Run main function."""
    print("Call Event Sender - Send to Service Bus Queue")
    print("=" * 80)

    # Load call events
    call_events = load_call_events()
    # We're only offering option to send a simple call event
    # Send a simple call event
    display_call_events(call_events)
    call_event_id = get_user_choice(len(call_events), f"Choose a call event (1-{len(call_events)}): ")

    call_event = call_events[call_event_id]
    print(f"\nSelected call event ID {call_event_id}: {call_event['sdc']}")
    await send_test_message(call_event)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error executing script: {str(e)}")
        import traceback

        traceback.print_exc()
        input("Press Enter to exit...")
