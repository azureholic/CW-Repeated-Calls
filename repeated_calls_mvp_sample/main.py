#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.

import os
import asyncio
import argparse

from src.data_loader import get_data_for_call
from src.processor import process_specific_call


async def main():
    """Main entry point for the repeated call handler."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Process customer calls and generate recommendations for repeated contact handling."
    )
    parser.add_argument(
        "call_id",
        nargs="?",
        default="c3",
        help="ID of a specific call to process (e.g., c1, c2, c3, etc.)",
    )

    args = parser.parse_args()

    # Create necessary output directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "output"), exist_ok=True)

    # Load data for this call from CSV
    call_id = args.call_id
    try:
        data = get_data_for_call(call_id)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Get the prepared data
    calls = data["call_history"]

    # Put the current call last in the list for processing
    current_call_index = next((i for i, c in enumerate(calls) if c["call_id"] == call_id), None)
    if current_call_index is not None:
        current_call = calls.pop(current_call_index)
        calls.append(current_call)

    customer = data["customer"]
    disruptions = data["disruptions"]

    # Process the specified call
    await process_specific_call(call_id, calls, customer, disruptions)


if __name__ == "__main__":
    asyncio.run(main())
