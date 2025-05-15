"""Plugins for the customer domain based on CSV files."""

import json
from typing import Annotated

from semantic_kernel.functions import kernel_function

from repeated_calls.database.schemas import CallEvent, Customer, HistoricCallEvent
from repeated_calls.utils.loggers import Logger

logger = Logger()


class CustomerDataPlugin:
    """Plugin with tools for retrieving customer data."""

    def __init__(self, data_path: str):
        """Initialize the plugin with the path to the CSV files."""
        self.customers = Customer.from_csv(f"{data_path}/customer.csv")
        self.call_events = CallEvent.from_csv(f"{data_path}/call_event.csv")
        self.historic_call_events = HistoricCallEvent.from_csv(f"{data_path}/historic_call_event.csv")

    @kernel_function
    def get_customer_details(self, customer_id: int) -> Annotated[str, "Details of the customer."]:
        """Retrieve a JSON string with customer details."""
        # Find customer using the enhanced class method
        for customer in self.customers:
            if customer.id == customer_id:
                return json.dumps(customer.model_dump(mode="json"))

        logger.warning(f"Warning: No customer found with ID {customer_id}")
        return "No customer found"
