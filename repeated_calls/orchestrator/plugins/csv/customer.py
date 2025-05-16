"""Plugins for the customer domain based on CSV files."""

import json
from typing import Annotated

from semantic_kernel.functions import kernel_function

from repeated_calls.database.schemas import CallEvent, Customer, HistoricCallEvent, Product, Subscription
from repeated_calls.utils.loggers import Logger

logger = Logger()


class CustomerDataPlugin:
    """Plugin with tools for retrieving customer data."""

    def __init__(self, data_path: str):
        """Initialize the plugin with the path to the CSV files."""
        self.customers = Customer.from_csv(f"{data_path}/customer.csv")
        self.call_events = CallEvent.from_csv(f"{data_path}/call_event.csv")
        self.historic_call_events = HistoricCallEvent.from_csv(f"{data_path}/historic_call_event.csv")
        self.subscriptions = Subscription.from_csv(f"{data_path}/subscription.csv")
        self.products = Product.from_csv(f"{data_path}/product.csv")

    @kernel_function
    def get_customer_details(self, customer_id: int) -> Annotated[str, "Details of the customer."]:
        """Retrieve a JSON string with customer details."""
        # Find customer using the enhanced class method
        for customer in self.customers:
            if customer.id == customer_id:
                return json.dumps(customer.model_dump(mode="json"))

        logger.warning(f"Warning: No customer found with ID {customer_id}")
        return "No customer found"

    @kernel_function
    def get_customer_call_event(self, customer_id: int) -> Annotated[str, "Call event of the customer."]:
        """Retrieve a JSON string of the call event of the customer."""
        # Find customer's call event using the enhanced class method
        for call_event in self.call_events:
            if call_event.customer_id == customer_id:
                return json.dumps(call_event.model_dump(mode="json"))

        logger.warning(f"Warning: No call event found for customer ID {customer_id}")
        return "No call event found"

    @kernel_function
    def get_customer_historic_call_events(self, customer_id: int) -> Annotated[str, "Call events of the customer."]:
        """Retrieve a JSON string of the historic call events of the customer."""
        # Find customer's historic call events using the enhanced class method
        historic_call_events = [
            event.model_dump(mode="json") for event in self.historic_call_events if event.customer_id == customer_id
        ]

        if not historic_call_events:
            logger.warning(f"Warning: No historic call events found for customer ID {customer_id}")
            return "No historic call events found"
        else:
            return json.dumps(historic_call_events)

    @kernel_function
    def get_customer_subscriptions(self, customer_id: int) -> Annotated[str, "Subscriptions of the customer."]:
        """Retrieve a JSON string of the subscriptions of the customer."""
        # Find subscriptions for the given customer ID
        customer_subscriptions = [
            subscription.model_dump(mode="json")
            for subscription in self.subscriptions
            if subscription.customer_id == customer_id
        ]

        if not customer_subscriptions:
            logger.warning(f"Warning: No subscriptions found for customer ID {customer_id}")
            return "No subscriptions found"
        else:
            return json.dumps(customer_subscriptions)

    @kernel_function
    def get_product_details(self, product_id: int) -> Annotated[str, "Details of the product."]:
        """Retrieve a JSON string with product details."""
        # Find product using the enhanced class method
        for product in self.products:
            if product.id == product_id:
                return json.dumps(product.model_dump(mode="json"))
        logger.warning(f"Warning: No product found with ID {product_id}")
        return "No product found"
