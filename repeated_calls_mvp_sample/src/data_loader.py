#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.

import os
import json
import csv

# Directory paths
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def load_csv_file(filename):
    """Load data from a CSV file into a list of dictionaries."""
    filepath = os.path.join(DATABASE_DIR, filename)
    result = []

    with open(filepath, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            result.append(row)

    return result


def prepare_call_data():
    """Prepare current and historical call data."""
    # Load current call events
    current_calls = load_csv_file("call_event.csv")

    # Load historical call events
    historical_calls = load_csv_file("historic_call_event.csv")

    # Combine and format call data for our workflow
    all_calls = []

    # Process historical calls first (older calls)
    for call in historical_calls:
        formatted_call = {
            "call_id": f"h{call['id']}",
            "customer_id": call["customer_id"],
            "timestamp": call["start_time"],
            "call_reason": call["sdc"],
            "details": call["call_summary"],  # Store details without duplicating
            "resolved": True,  # Assume historical calls were marked as resolved
        }
        all_calls.append(formatted_call)

    # Process current calls (newer calls)
    for call in current_calls:
        formatted_call = {
            "call_id": f"c{call['id']}",
            "customer_id": call["customer_id"],
            "timestamp": call["time_stamp"],
            "call_reason": call["sdc"],
            "details": "",  # No additional details for current calls yet
            "resolved": False,  # Current calls are not yet resolved
        }
        all_calls.append(formatted_call)

    # Sort calls by customer_id and timestamp
    all_calls.sort(key=lambda x: (x["customer_id"], x["timestamp"]))

    return all_calls


def prepare_customer_data():
    """Prepare customer data with subscription information."""
    # Load customers
    customers = load_csv_file("customer.csv")

    # Load subscriptions
    subscriptions = load_csv_file("subscription.csv")

    # Load products
    products = load_csv_file("product.csv")

    # Format customer data for our workflow
    formatted_customers = []

    for customer in customers:
        # Get all subscriptions for this customer
        customer_subscriptions = [s for s in subscriptions if s["customer_id"] == customer["id"]]

        # Get product details for each subscription
        customer_products = []
        for sub in customer_subscriptions:
            product = next((p for p in products if p["id"] == sub["product_id"]), None)
            if product:
                customer_products.append(product["name"])

        # Format the customer data
        formatted_customer = {
            "customer_id": customer["id"],
            "name": customer["name"],
            "email": f"{customer['name'].lower().replace(' ', '.')}@example.com",  # Generated email
            "phone": f"+1-555-{customer['id']}-0000",  # Generated phone
            "customer_lifetime_value": customer["clv"],  # Keep original CLV value (Low, Med, High)
            "account_start_date": customer["relation_start_date"],
            "products": customer_products,
            "previous_compensations": [],  # Would be populated from compensation history
        }

        formatted_customers.append(formatted_customer)

    return formatted_customers


def prepare_disruption_data():
    """Prepare operational disruption data from software updates."""
    # Load software updates
    software_updates = load_csv_file("software_update.csv")

    # Load products
    products = load_csv_file("product.csv")

    # Format disruption data for our workflow
    disruptions = []

    for update in software_updates:
        product = next((p for p in products if p["id"] == update["product_id"]), None)
        if product:
            disruption = {
                "disruption_id": f"d{update['id']}",
                "type": f"Software Update ({update['type']})",
                "start_time": f"{update['rollout_date']}T00:00:00Z",
                "end_time": f"{update['rollout_date']}T23:59:59Z",
                "affected_areas": ["All regions"],
                "affected_services": [product["name"]],
                "cause": f"{update['type'].capitalize()} software update deployment",
                "resolved": True,
            }
            disruptions.append(disruption)

    return disruptions


def get_data_for_call(call_id):
    """Get all data needed to process a specific call."""
    # Load and prepare all the data
    all_calls = prepare_call_data()
    all_customers = prepare_customer_data()
    all_disruptions = prepare_disruption_data()

    # Find the specific call by ID
    current_call = next((c for c in all_calls if c["call_id"] == call_id), None)
    if not current_call:
        raise ValueError(f"Call with ID {call_id} not found")

    # Get the customer ID for this call
    customer_id = current_call["customer_id"]

    # Filter calls for this customer only, to create the call history
    customer_calls = [c for c in all_calls if c["customer_id"] == customer_id]

    # Find customer information
    customer = next((c for c in all_customers if c["customer_id"] == customer_id), None)
    if not customer:
        raise ValueError(f"Customer with ID {customer_id} not found")

    # Return all the data
    return {
        "current_call": current_call,
        "call_history": customer_calls,
        "customer": customer,
        "disruptions": all_disruptions,
    }


def save_for_workflow(call_id=None, context_dir=None):
    """
    Save the prepared data as JSON files for the workflow.

    Args:
        call_id: The ID of the call to process
        context_dir: The directory to save context files to

    Returns:
        dict: The data prepared for the workflow
    """
    # Use default output dir if no context_dir is provided
    if context_dir is None:
        context_dir = os.path.join(OUTPUT_DIR, "temp_context")

    os.makedirs(context_dir, exist_ok=True)

    # If a call ID is specified, prepare data for that call
    if call_id:
        data = get_data_for_call(call_id)

        # Save the current call as the last item in the calls array
        calls = data["call_history"]
        current_call_index = next((i for i, c in enumerate(calls) if c["call_id"] == call_id), None)
        if current_call_index is not None:
            current_call = calls.pop(current_call_index)
            calls.append(current_call)

        # Save call data
        with open(os.path.join(context_dir, "calls.json"), "w") as file:
            json.dump(calls, file, indent=2)

        # Save customer data
        with open(os.path.join(context_dir, "customers.json"), "w") as file:
            json.dump([data["customer"]], file, indent=2)

        # Save disruption data
        with open(os.path.join(context_dir, "disruptions.json"), "w") as file:
            json.dump(data["disruptions"], file, indent=2)

        return data

    # Otherwise, prepare all data
    else:
        all_calls = prepare_call_data()
        all_customers = prepare_customer_data()
        all_disruptions = prepare_disruption_data()

        # Save all data
        with open(os.path.join(context_dir, "calls.json"), "w") as file:
            json.dump(all_calls, file, indent=2)

        with open(os.path.join(context_dir, "customers.json"), "w") as file:
            json.dump(all_customers, file, indent=2)

        with open(os.path.join(context_dir, "disruptions.json"), "w") as file:
            json.dump(all_disruptions, file, indent=2)

        return {
            "calls": all_calls,
            "customers": all_customers,
            "disruptions": all_disruptions,
        }
