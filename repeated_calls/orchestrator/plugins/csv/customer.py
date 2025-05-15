"""Plugins for the customer domain based on CSV files."""

import json
from typing import Annotated

from semantic_kernel.functions import kernel_function

from repeated_calls.database.schemas import Customer
from repeated_calls.utils.loggers import Logger

logger = Logger()


class CustomerDataPlugin:
    """Plugin with tools for retrieving customer data."""

    def __init__(self, data_path: str):
        self.customers = Customer.from_csv(f"{data_path}/customers.csv")

    @kernel_function(name="get_customer_details", description="Retrieves a JSON string with customer details.")
    def get_customer_details(self, customer_id: int) -> Annotated[str, "Details of the customer."]:
        # Find customer using the enhanced class method
        data = [
            json.dumps(customer.model_dump(mode="json")) for customer in self.customers if customer.id == customer_id
        ]
        if not data:
            logger.warning(f"Warning: No customer found with ID {customer_id}")

        return data
