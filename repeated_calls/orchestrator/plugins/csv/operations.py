"""Plugins for the customer domain based on CSV files."""

import json
from typing import Annotated

from semantic_kernel.functions import kernel_function

from repeated_calls.database.schemas import SoftwareUpdate
from repeated_calls.utils.loggers import Logger

logger = Logger()


class OperationsDataPlugin:
    """Plugin with tools for retrieving customer data."""

    def __init__(self, data_path: str):
        """Initialize the plugin with the path to the CSV files."""
        self.software_updates = SoftwareUpdate.from_csv(f"{data_path}/software_update.csv")

    @kernel_function
    def get_software_update(self, product_id: str) -> Annotated[str, "Software update of the product."]:
        """Retrieve a JSON string of the software update of the product."""
        # Find customer's software update using the enhanced class method
        for software_update in self.software_updates:
            if software_update.product_id == product_id:
                return json.dumps(software_update.model_dump(mode="json"))

        logger.warning(f"Warning: No software update found for product {product_id}")
        return "No software update found"

    # Extra dummy function, always returns "No outages found"
    @kernel_function
    def check_outages(
        self, product_id: str
    ) -> Annotated[str, "Check if there is a current outage known for the product"]:
        """Retrieve a string whether a current outage is known for the product."""
        return "No outages found"
